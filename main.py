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
    
    def show_number(self, number, offset=0, color=WHITE):
        """
        todo: now the full area is blinking, 
        should save last digit to some memory and update only diffs ??
        """
        if number < 0 and number > 99 :
            print(f'Given number is outside range 0-99: {number}')
            return 
        
        digits = [int(x) for x in str(number)]
        digits.reverse()

        # First clear space for the number
        self.ws2812.pixels_fill_range(0 + offset, 64 + offset, BLACK)
        self.ws2812.pixels_show()


        i = 0
        for digit in digits:
            a = self._translate_4x8_to_led(raw_digits[digit])
            for pixel in range(len(a)):
                if a[pixel] == 1:
                    self.ws2812.pixels_set(pixel + (i * 32) + offset, color)
            i += 1

        self.ws2812.pixels_show()
    
      
        
    def traffic_control(self):
        pass

    def demo(self):
        pass


if __name__ == "__main__":
    semaphore = Semaphore()
    while True:
        b = 10
        while b >= 0:
            semaphore.show_number(b)
            b -= 1
            time.sleep(1)

        b = 10
        while b >= 0:
            semaphore.show_number(b, offset=64, color=GREEN)
            b -= 1
            time.sleep(1)

        b = 10
        while b >= 0:
            semaphore.show_number(b, offset=128, color=RED)
            b -= 1
            time.sleep_ms(500)


    print('Finished!')
































    # pixels_fill_range(RED, 0, 64)
    # pixels_fill_range(BLACK, 64, 128)
    # pixels_fill_range(BLACK, 128, 192)
    # pixels_show()
    # time.sleep(5)

    # pixels_fill_range(RED, 0, 64)
    # pixels_fill_range(ORANGE, 64, 128)
    # pixels_fill_range(BLACK, 128, 192)
    # pixels_show()
    # time.sleep(2)

    # pixels_fill_range(BLACK, 0, 64)
    # pixels_fill_range(BLACK, 64, 128)
    # pixels_fill_range(GREEN, 128, 192)
    # pixels_show()
    # time.sleep(5)

    # pixels_fill_range(BLACK, 0, 64)
    # pixels_fill_range(BLACK, 64, 128)
    # pixels_fill_range(BLACK, 128, 192)
    # pixels_show()
    # time.sleep(0.5)

    # pixels_fill_range(BLACK, 0, 64)
    # pixels_fill_range(BLACK, 64, 128)
    # pixels_fill_range(GREEN, 128, 192)
    # pixels_show()
    # time.sleep(0.5)

    # pixels_fill_range(BLACK, 0, 64)
    # pixels_fill_range(BLACK, 64, 128)
    # pixels_fill_range(BLACK, 128, 192)
    # pixels_show()
    # time.sleep(0.5)

    # pixels_fill_range(BLACK, 0, 64)
    # pixels_fill_range(BLACK, 64, 128)
    # pixels_fill_range(GREEN, 128, 192)
    # pixels_show()
    # time.sleep(0.5)

    # pixels_fill_range(BLACK, 0, 64)
    # pixels_fill_range(BLACK, 64, 128)
    # pixels_fill_range(BLACK, 128, 192)
    # pixels_show()
    # time.sleep(0.5)

    # pixels_fill_range(BLACK, 0, 64)
    # pixels_fill_range(BLACK, 64, 128)
    # pixels_fill_range(GREEN, 128, 192)
    # pixels_show()
    # time.sleep(0.5)

    # pixels_fill_range(BLACK, 0, 64)
    # pixels_fill_range(ORANGE, 64, 128)
    # pixels_fill_range(BLACK, 128, 192)
    # pixels_show()
    # time.sleep(2)