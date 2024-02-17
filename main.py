import json
import time
from matrix_8x8 import matrix_8x8
from graphics import *
from machine import Pin
import bluetooth
from ble_simple_peripheral import BLESimplePeripheral
import utime
import random
from machine import Timer


class Semaphore:
    NUM_LEDS = 192
    PIN_NUM = 28

    def __init__(self):
        with open("config.json", "r") as read_file:
            self.config = json.load(read_file)
        self.matrix = matrix_8x8(28, 3, brightness=self.config["brightness"])
        self.ble = bluetooth.BLE()
        self.conn = BLESimplePeripheral(self.ble, name=self.config["name"])
        self.tim = Timer()
        if self.config['role'] == 'commander':
            self.count = 0
            self.synchronized = True
        elif self.config['role'] == 'listener':
            self.count = -1
            self.synchronized = False
        else:
            print('error')
        self.init_timer()
        
    def do_traffic_control(self):
        pass

    def on_rx(self, data):
        print("Data received: ", data)
        if data[:3] == b'set':
            print('Set command received!')
            self.count = int(data[3:])
            self.synchronized = True
        elif data[:5] == b'reset':
            print('Reset command received!')
            self.count = -1
            self.synchronized = False
                    
    def send_command(self):
        if self.conn.is_connected():
            msg="pushbutton pressed\n"
            self.conn.send(f'set{self.count}')

    def listen(self):
        while True:
            if self.conn.is_connected():
                self.conn.on_write(self.on_rx)

    def init_timer(self):
        self.tim.init(freq=1, mode=Timer.PERIODIC, callback=self.periodic_callback)

    def periodic_callback(self, timer):
        if self.synchronized:
            # self.demo()
            i = 0
            for light in self.config["trafic_control"][str(self.count)][self.config["name"]]:
                print(f'light: {light}')
                if light:
                    print(f'after light: {light}')
                    if type(light) == str:
                        if light == "red":
                            self.matrix.show_symbol(circle, offset=i, color=RED)
                        elif light == "green":
                            self.matrix.show_symbol(circle, offset=i, color=GREEN)
                    elif type(light) == int:
                        self.matrix.show_number(light, offset=i, color=WHITE)
                else:
                    self.matrix.show_symbol(square, offset=i, color=BLACK)

                i += 1
            self.count += 1
            if self.count > 20:
                self.count = 0
            print(f'Count: {self.count}')
        else:
            self.matrix.show_symbol(square, offset=0, color=BLACK)
            self.matrix.show_symbol(square, offset=1, color=BLACK)
            self.matrix.show_symbol(square, offset=2, color=BLACK)
            if self.count == -1:
                self.matrix.show_symbol(square, offset=1, color=ORANGE)
                self.count -= 1
            else:
                self.count = -1
            
    def demo(self):
        if self.count == 0:
            self.matrix.show_symbol(circle, color=RED)
        elif self.count == 1:

            self.matrix.show_symbol(circle, color=ORANGE)
        elif self.count == 2:
            self.matrix.show_symbol(circle, color=GREEN)


if __name__ == "__main__":
    semaphore = Semaphore()
    # i = 0
    # while True:
    #     with open('data.txt', 'a') as file:
    #         file.write(str(i) + '\n')
    #     if i > 100:
    #         break
    #     i += 1

    while True:
        if not semaphore.synchronized:
            if semaphore.config['role'] == 'commander':
                semaphore.send_command()
            elif semaphore.config['role'] == 'listener':
                semaphore.listen()
        utime.sleep(0.25)
