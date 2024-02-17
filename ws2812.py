# Example using PIO to drive a set of WS2812 LEDs.

import array, time
from machine import Pin
import rp2

@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)
def ws2812_asm():
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1)               .side(0)    [T3 - 1]
    jmp(not_x, "do_zero")   .side(1)    [T1 - 1]
    jmp("bitloop")          .side(1)    [T2 - 1]
    label("do_zero")
    nop()                   .side(0)    [T2 - 1]
    wrap()

class ws2812:
    
    def __init__(self, num_leds, pin_num, brightness):
        self.num_leds = num_leds
        self.brightness = brightness
        self.sm = rp2.StateMachine(0, ws2812_asm, freq=8_000_000, sideset_base=Pin(pin_num, Pin.PULL_DOWN))
        self.ar = array.array("I", [0 for _ in range(self.num_leds)])
        self.sm.active(1)

    def pixels_show(self):
        dimmer_ar = array.array("I", [0 for _ in range(self.num_leds)])
        for i,c in enumerate(self.ar):
            r = int(((c >> 8) & 0xFF) * self.brightness)
            g = int(((c >> 16) & 0xFF) * self.brightness)
            b = int((c & 0xFF) * self.brightness)
            dimmer_ar[i] = (g<<16) + (r<<8) + b
        self.sm.put(dimmer_ar, 8)
        time.sleep_ms(10)

    def pixel_set(self, i, color):
        self.ar[i] = (color[1]<<16) + (color[0]<<8) + color[2]

    def pixels_fill(self, color):
        for i in range(len(self.ar)):
            self.pixel_set(i, color)

    def pixels_fill_range(self, start, num_elements, color):
        for i in range(start, num_elements, 1):
            self.pixel_set(i, color)
