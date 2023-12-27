from ws2812 import ws2812
# import picow_ble_temp_sensor
import json

from machine import Pin


class Semaphore:
    NUM_LEDS = 192
    PIN_NUM = 28
    brightness = 1.0

    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    YELLOW = (255, 150, 0)
    ORANGE = (255, 60, 0)
    GREEN = (0, 255, 0)
    CYAN = (0, 255, 255)
    BLUE = (0, 0, 255)
    PURPLE = (180, 0, 255)
    WHITE = (255, 255, 255)
    COLORS = (BLACK, RED, YELLOW, ORANGE, GREEN, CYAN, BLUE, PURPLE, WHITE)

    def __init__(self):
        with open("config.json", "r") as read_file:
            self.config = json.load(read_file)
        self.ws2812 = ws2812(self.NUM_LEDS, self.PIN_NUM, self.config["brightness"])

        
        
    def traffic_control(self):
        pass

    def demo(self):
        self.ws2812.demo()


    



if __name__ == "__main__":
    semaphore = Semaphore()
    # semaphore.demo()

    print('Finished!')
