from ws2812 import ws2812
from graphics import *
# import picow_ble_temp_sensor
import json
import time
from machine import Pin


class Semaphore:
    NUM_LEDS = 192
    PIN_NUM = 28

    def __init__(self):
        with open("config.json", "r") as read_file:
            self.config = json.load(read_file)
        self.ws2812 = ws2812(self.NUM_LEDS, self.PIN_NUM, self.config["brightness"])
    
    def _translate_4x8_to_led(self, symbol):
        return [
            symbol[31], symbol[27], symbol[23], symbol[19], symbol[15], symbol[11], symbol[ 7], symbol[ 3],
            symbol[ 2], symbol[ 6], symbol[10], symbol[14], symbol[18], symbol[22], symbol[26], symbol[30],
            symbol[29], symbol[25], symbol[21], symbol[17], symbol[13], symbol[ 9], symbol[ 5], symbol[ 1],
            symbol[ 0], symbol[ 4], symbol[ 8], symbol[12], symbol[16], symbol[20], symbol[24], symbol[28]
        ]
    
    def show_symbol(self, start, stop, color=WHITE):
        self.ws2812.pixels_fill_range(start, stop, color)
        self.ws2812.pixels_show()

    
    def show_number(self, number, offset=0, color=WHITE):
        if number < 0 and number > 99 :
            print(f'Given number is outside range 0-99: {number}')
            return 
        
        digits = [int(x) for x in str(number)]
        digits.reverse()

        i = 0
        for digit in digits:
            self._set_digit(raw_digits[digit], i, offset, color)
            i += 1

        if len(digits) == 1:
            self._set_digit(raw_blank, i, offset, color)

        self.ws2812.pixels_show()

    def _set_digit(self, digit_matrix, i, offset, color, lenght=32):
        matrix = self._translate_4x8_to_led(digit_matrix)
        for pixel in range(len(matrix)):
            if matrix[pixel] == 1:
                self.ws2812.pixels_set(pixel + (i * lenght) + offset, color)
            elif matrix[pixel] == 0:
                self.ws2812.pixels_set(pixel + (i * lenght) + offset, BLACK)

        
    def traffic_control(self):
        pass

    def demo(self):
        while True:
            # Red + count down
            j = 10
            self.show_symbol(0, 64, color=RED)
            # self.show_symbol(64, 128, color=BLACK)
            self.show_symbol(128, 192, color=BLACK)
            while j > 1: 
                self.show_number(j, offset=64, color=WHITE)
                j -= 1
                time.sleep(1)

            # Red + Orange
            self.show_symbol(0, 64, color=RED)
            self.show_symbol(64, 128, color=ORANGE)
            self.show_symbol(128, 192, color=BLACK)
            time.sleep(1)

            # Green + count down
            j = 10
            self.show_symbol(0, 64, color=BLACK)
            self.show_symbol(64, 128, color=BLACK)
            self.show_symbol(128, 192, color=GREEN)
            while j > 1: 
                self.show_number(j, offset=64, color=WHITE)
                j -= 1
                time.sleep(1)

            # Orange
            self.show_symbol(0, 64, color=BLACK)
            self.show_symbol(64, 128, color=ORANGE)
            self.show_symbol(128, 192, color=BLACK)
            time.sleep(1)

            


if __name__ == "__main__":
    semaphore = Semaphore()
    semaphore.demo()
