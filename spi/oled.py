import spidev
import gpiod
import time
import logging
import os
import sys
from PIL import Image,ImageDraw,ImageFont
import cv2

picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
#libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
#print(f"Lib directory: {libdir}")  # Додаємо для перевірки шляху
#if os.path.exists(libdir):
#    sys.path.append(libdir)
#else:
#    print("Directory does not exist!")
from lib.OLED_1in5_rgb import OLED_1in5_rgb





class Main:
    def __init__(self):
        self.disp = OLED_1in5_rgb()
        self.disp.Init()
        self.disp.clear()
        font = ImageFont.truetype(os.path.join("pic", 'Font.ttc'), 12)
        #font1 = ImageFont.truetype(os.path.join("pic", 'Font.ttc'), 18)
        #font2 = ImageFont.truetype(os.path.join("pic", 'Font.ttc'), 24)
        #image1 = Image.new('RGB', (self.disp.width, self.disp.height), 0)
        #draw = ImageDraw.Draw(image1)

        
        #draw.line([(0,0),(127,0)], fill = "CYAN")
        #draw.line([(0,127),(127,127)],  fill = "RED",   width = 46)
        #draw.text((20,0), 'Waveshare ', font = font, fill = "BLUE")
        #draw.text((20,30), 'Waveshare ', font1 = font, fill = "BLUE")
        #draw.text((20,60), 'Waveshare ', font2 = font, fill = "BLUE")
        #image1 = image1.rotate(0)
        #self.disp.ShowImage(self.disp.getbuffer(image1))
        #time.sleep(2)


        Himage2 = Image.new('RGB', (self.disp.width, self.disp.height), 0)  # 0: clear the frame
        draw = ImageDraw.Draw(Himage2)
        bmp = Image.open(os.path.join("pic", '1in5_rgb.bmp'))
        Himage2.paste(bmp, (0,0))
        draw.text((20,0), 'EMMC Writer ', font = font, fill = "BLUE")
        draw.line([(0,127),(127,127)],  fill = "RED",   width = 2)

        Himage2=Himage2.rotate(0) 	
        self.disp.ShowImage(self.disp.getbuffer(Himage2)) 


if __name__ == "__main__":
    Main()
