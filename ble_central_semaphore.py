import bluetooth
import random
import struct
import time
import micropython
from ble_advertising import decode_services, decode_name
from micropython import const
from machine import Pin
import ubinascii

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
_IRQ_GATTS_READ_REQUEST = const(4)
_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)
_IRQ_PERIPHERAL_CONNECT = const(7)
_IRQ_PERIPHERAL_DISCONNECT = const(8)
_IRQ_GATTC_SERVICE_RESULT = const(9)
_IRQ_GATTC_SERVICE_DONE = const(10)
_IRQ_GATTC_CHARACTERISTIC_RESULT = const(11)
_IRQ_GATTC_CHARACTERISTIC_DONE = const(12)
_IRQ_GATTC_DESCRIPTOR_RESULT = const(13)
_IRQ_GATTC_DESCRIPTOR_DONE = const(14)
_IRQ_GATTC_READ_RESULT = const(15)
_IRQ_GATTC_READ_DONE = const(16)
_IRQ_GATTC_WRITE_DONE = const(17)
_IRQ_GATTC_NOTIFY = const(18)
_IRQ_GATTC_INDICATE = const(19)

_ADV_IND = const(0x00)
_ADV_DIRECT_IND = const(0x01)
_ADV_SCAN_IND = const(0x02)
_ADV_NONCONN_IND = const(0x03)

_DEVICE = const(0x28cdc10b595b)

_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_TX_UUID = bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_RX_UUID = bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")

_UART_TX_CHAR = (
    _UART_TX_UUID,
    bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY,
)
_UART_RX_CHAR = (
    _UART_RX_UUID,
    bluetooth.FLAG_WRITE | bluetooth.FLAG_WRITE_NO_RESPONSE,
)
_UART_SERVICE = (
    _UART_UUID,
    (_UART_TX_CHAR, _UART_RX_CHAR),
)

class BLESemaphoreCentral:
    def __init__(self, ble):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._handle_tx, self._handle_rx),) = self._ble.gatts_register_services((_UART_SERVICE,))
        self._reset()

    def _reset(self):
        # Cached name and address from a successful scan.
        self._name = None
        self._addr_type = None
        self._addr = None

        # Cached value (if we have one)
        self._value = None

        # Callbacks for completion of various operations.
        # These reset back to None after being invoked.
        self._scan_callback = None
        self._conn_callback = None
        self._read_callback = None
        self._write_callback = None
        self._write_done = False

        # Persistent callback for when new data is notified from the device.
        self._notify_callback = None

        # Connected device.
        self._conn_handle = None
        self._start_handle = None
        self._end_handle = None
        self._value_handle = None

    def _irq(self, event, data):
        if event == _IRQ_SCAN_RESULT:
            addr_type, addr, adv_type, rssi, adv_data = data
            if ubinascii.hexlify(addr).decode() == str(hex(_DEVICE))[2:]:
                type_list = decode_services(adv_data)
                if _UART_UUID in type_list:
                    # Found a potential device, remember it and stop scanning.
                    self._addr_type = addr_type
                    self._addr = bytes(addr)  # Note: addr buffer is owned by caller so need to copy it.
                    self._name = decode_name(adv_data) or "?"
                    self._ble.gap_scan(None)

        elif event == _IRQ_SCAN_DONE:
            if self._scan_callback:
                if self._addr:
                    # Found a device during the scan (and the scan was explicitly stopped).
                    self._scan_callback(self._addr_type, self._addr, self._name)
                    self._scan_callback = None
                else:
                    # Scan timed out.
                    self._scan_callback(None, None, None)

        elif event == _IRQ_PERIPHERAL_CONNECT:
            conn_handle, addr_type, addr = data
            print(f'conn_handle: {conn_handle}, addr_type = {addr_type}, addr: {bytes(addr)}')
            if conn_handle == 0:
                print('Connect unsuccessful!')
                return False
            else:
                print('Connect successful!')
            if addr_type == self._addr_type and addr == self._addr:
                self._conn_handle = conn_handle
                self._ble.gattc_discover_services(self._conn_handle)

        elif event == _IRQ_PERIPHERAL_DISCONNECT:
            # Disconnect (either initiated by us or the remote end).
            print('Disconnected!')
            conn_handle, _, _ = data
            if conn_handle == self._conn_handle:
                # If it was initiated by us, it'll already be reset.
                self._reset()

        elif event == _IRQ_GATTC_SERVICE_RESULT:
            # Connected device returned a service.
            conn_handle, start_handle, end_handle, uuid = data
            
            if conn_handle == self._conn_handle and uuid == _UART_UUID:
                self._start_handle, self._end_handle = start_handle, end_handle

        elif event == _IRQ_GATTC_SERVICE_DONE:
            # Service query complete.
            if self._start_handle and self._end_handle:
                self._ble.gattc_discover_characteristics(
                    self._conn_handle, self._start_handle, self._end_handle
                )
            else:
                print("Failed to find environmental sensing service.")

        elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
            # Connected device returned a characteristic.
            conn_handle, def_handle, value_handle, properties, uuid = data
            if conn_handle == self._conn_handle and uuid == _UART_RX_UUID:
                self._value_handle = value_handle

        elif event == _IRQ_GATTC_CHARACTERISTIC_DONE:
            # Characteristic query complete.
            if self._value_handle:
                # We've finished connecting and discovering device, fire the connect callback.
                if self._conn_callback:
                    self._conn_callback()
            else:
                print("Failed to find UART characteristic.")

        elif event == _IRQ_GATTC_READ_RESULT:
            # A read completed successfully.
            conn_handle, value_handle, char_data = data
            print(f'conn_handle, value_handle, char_data: {conn_handle}, {value_handle}, {bytes(char_data)}')
            if conn_handle == self._conn_handle and value_handle == self._value_handle:
                self._update_value(char_data)
                if self._read_callback:
                    self._read_callback(self._value)
                    self._read_callback = None

        elif event == _IRQ_GATTC_READ_DONE:
            # Read completed (no-op).
            conn_handle, value_handle, status = data

        elif event == _IRQ_GATTC_NOTIFY:
            # The ble_temperature.py demo periodically notifies its value.
            conn_handle, value_handle, notify_data = data
            if conn_handle == self._conn_handle and value_handle == self._value_handle:
                self._update_value(notify_data)
                if self._notify_callback:
                    self._notify_callback(self._value)

        elif event == _IRQ_GATTC_WRITE_DONE:
            # A gattc_write() has completed.
            # Note: Status will be zero on success, implementation-specific value otherwise.
            conn_handle, value_handle, status = data
            if status == 0:
                self._write_done = True
                print(f'Write done, status: {status}')

    # Returns true if we've successfully connected and discovered characteristics.
    def is_connected(self):
        return self._conn_handle is not None and self._value_handle is not None

    # Find a device advertising the environmental sensor service.
    def scan(self, callback=None):
        self._addr_type = None
        self._addr = None
        self._scan_callback = callback
        self._ble.gap_scan(2000, 30000, 30000)

    # Connect to the specified device (otherwise use cached address from a scan).
    def connect(self, addr, callback=None):
        self._addr_type = 0
        self._addr = addr
        self._conn_callback = callback
        if self._addr_type is None or self._addr is None:
            return False
        print(f'_addr_type: {self._addr_type}, _addr: {self._addr}')
        self._ble.gap_connect(self._addr_type, self._addr)

    # Disconnect from current device.
    def disconnect(self):
        if not self._conn_handle:
            return
        self._ble.gap_disconnect(self._conn_handle)
        self._reset()

    # Issues an (asynchronous) read, will invoke callback with data.
    def read(self, callback):
        if not self.is_connected():
            return
        self._read_callback = callback
        try:
            self._ble.gattc_read(self._conn_handle, self._value_handle)
        except OSError as error:
            print(error)

    def send(self, data):
        self._write_done = False
        self._ble.gattc_write(self._conn_handle, self._handle_rx, data, 1)

    # Sets a callback to be invoked when the device notifies us.
    def on_notify(self, callback):
        self._notify_callback = callback

    def _update_value(self, data):
        # Data is sint16 in degrees Celsius with a resolution of 0.01 degrees Celsius.
        try:
            self._value = struct.unpack("<h", data)[0] / 100
        except OSError as error:
            print(error)

    def value(self):
        return self._value
    

# Byte to readable addr
    # a = str.upper(ubinascii.hexlify(addr).decode())
    # print(f'MAC: {a[0:2]}:{a[2:4]}:{a[4:6]}:{a[6:8]}:{a[8:10]}:{a[10:12]}')


    def sent_to_address(self, addr, value):
        byte_address = ubinascii.unhexlify(addr.replace(':', '').lower())
        try:
            central.connect(byte_address)
            i = 0
            j = 0
            while not central.is_connected():
                print(f'Pass: {j}')

                if i > 20:
                    raise Exception("Can't connect")
                i += 1
                j += 1
                time.sleep_ms(100)

            central.send(value)
            i = 0
            while not central._write_done:
                if i > 20:
                    raise Exception("Can't write")
                i += 1
                time.sleep_ms(100)

            central.disconnect()
            while central.is_connected():
                if i > 20:
                    raise Exception("Can't disconnect")
                i += 1
                time.sleep_ms(100)
            time.sleep_ms(1000)
        except:
            return False
        else:
            return True

if __name__ == "__main__":
    ble = bluetooth.BLE()
    central = BLESemaphoreCentral(ble)
    while True:
        central.sent_to_address('28:CD:C1:0B:59:5B', "set10")
        time.sleep_ms(2500)
        central.sent_to_address('28:CD:C1:0B:59:5B', "reset")
        time.sleep_ms(2500)
        central.sent_to_address('28:CD:C1:0B:59:21', "set10")
        time.sleep_ms(2500)
        central.sent_to_address('28:CD:C1:0B:59:21', "reset")
        time.sleep_ms(2500)
    
    # while(True):
    # # demo(ble, central)
    #     central.update_counter(b'(\xcd\xc1\x0bY[', "set10")
    #     # central.update_counter(b'(\xcd\xc1\x0bY!', "set10")