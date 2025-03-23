# /*****************************************************************************
# * | File        :	  OLED_1in5_rgb.py
# * | Author      :   Waveshare team
# * | Function    :   Driver for OLED_1in5_rgb
# * | Info        :
# *----------------
# * | This version:   V2.0
# * | Date        :   2020-08-17
# * | Info        :   
# ******************************************************************************/
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documnetation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to  whom the Software is
# furished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import time
import numpy as np
import spidev
import gpiod


OLED_WIDTH   = 128  #OLED width
OLED_HEIGHT  = 128  #OLED height

class OLED_1in5_rgb():
        
    """    Write register address and data     """
    def command(self, cmd):
        #self.digital_write(self.DC_PIN,False)
        self.spi_cs.set_value(0)
        self.spi_dc.set_value(0)
        #print("Command:", cmd)
        data_to_send = [cmd]  # Відправляємо байт 0xAA
        received_data = self.spi.xfer2(data_to_send)
        #self.spi_writebyte([cmd])
        self.spi_cs.set_value(1)
        pass

    """    Write data     """
    def data(self, data):
        #self.digital_write(self.DC_PIN,True)
        self.spi_cs.set_value(0)
        self.spi_dc.set_value(1)
        #print("Data:", data)
        data_to_send = [data]
        received_data = self.spi.xfer2(data_to_send)
        #received_data = self.spi.xfer2(data)
        #self.spi_writebyte([data])
        self.spi_cs.set_value(1)
        pass
    def dataBuffer(self, buf):
        MAX_BUFFER_SIZE = 2048  
        self.spi_cs.set_value(0)
        self.spi_dc.set_value(1)
        for i in range(0, len(buf), MAX_BUFFER_SIZE):
            chunk = buf[i:i + MAX_BUFFER_SIZE]
            received_data = self.spi.xfer2(chunk)
        self.spi_cs.set_value(1)


    def Init(self):
        #if (self.module_init() != 0):
        #    return -1
        self.deviceDescriptor = "any"
        self.spi = spidev.SpiDev()
        self.chip0 = gpiod.Chip('gpiochip0')
        self.chip1 = gpiod.Chip('gpiochip1')
        self.deviceDescriptor = 'oledLCD'
        self.spi_dc = self.chip0.get_line(1) #OK
        self.spi_rst = self.chip0.get_line(6) #OK
        self.spi_cs = self.chip0.get_line(3) #OK

        self.spi_dc.request(consumer=self.deviceDescriptor, type=gpiod.LINE_REQ_DIR_OUT)
        self.spi_rst.request(consumer=self.deviceDescriptor, type=gpiod.LINE_REQ_DIR_OUT)
        self.spi_cs.request(consumer=self.deviceDescriptor, type=gpiod.LINE_REQ_DIR_OUT)
        self.spi.open(0, 0)  # SPI0, CS0
        self.spi.max_speed_hz = 10000000

        self.width = OLED_WIDTH
        self.height = OLED_HEIGHT

        """Initialize dispaly"""    
        self.reset()

        
            
        self.command(0xfd) # command lock
        self.data(0x12)
        self.command(0xfd) # command lock
        self.data(0xB1)

        self.command(0xae) # display off
        self.command(0xa4) # Normal Display mode

        self.command(0x15) # set column address
        self.data(0x00)    # column address start 00
        self.data(0x7f)    # column address end 127
        self.command(0x75) # set row address
        self.data(0x00)    # row address start 00
        self.data(0x7f)    # row address end 127   

        self.command(0xB3)
        self.data(0xF1)

        self.command(0xCA)
        self.data(0x7F)

        self.command(0xa0) # set re-map & data format
        self.data(0x74)    # Horizontal address increment

        self.command(0xa1) # set display start line
        self.data(0x00)    # start 00 line

        self.command(0xa2) # set display offset
        self.data(0x00)

        self.command(0xAB)
        self.command(0x01)

        self.command(0xB4)
        self.data(0xA0)
        self.data(0xB5)
        self.data(0x55)

        self.command(0xC1)
        self.data(0xC8)
        self.data(0x80)
        self.data(0xC0)

        self.command(0xC7)
        self.data(0x0F)

        self.command(0xB1)
        self.data(0x32)

        self.command(0xB2)
        self.data(0xA4)
        self.data(0x00)
        self.data(0x00)

        self.command(0xBB)
        self.data(0x17)

        self.command(0xB6)
        self.data(0x01)

        self.command(0xBE)
        self.data(0x05)

        self.command(0xA6)

        time.sleep(0.1)
        self.command(0xAF);#--turn on oled panel
        
   
    def reset(self):
        """Reset the display"""
        self.spi_rst.set_value(1)
        time.sleep(0.1)
        self.spi_rst.set_value(0)
        time.sleep(0.1)
        self.spi_rst.set_value(1)
        time.sleep(0.1)

    def clear(self):
        _buffer = [0x00]*(self.width * self.height * 2)
        self.ShowImage(_buffer)             
    
    def getbuffer(self, image):
        buf = [0x00] * ((self.width*2) * self.height)
        imwidth, imheight = image.size
        pixels = image.load()
        for y in range(imheight):
            for x in range(imwidth):
                # Set the bits for the column of pixels at the current position.
                buf[x*2 + y*imwidth*2] = ((pixels[x,y][0] & 0xF8) | (pixels[x,y][1] >> 5))
                buf[x*2+1 + y*imwidth*2] = (((pixels[x,y][1]<<3) & 0xE0) | (pixels[x,y][2] >> 3))
        return buf   

    def ShowImage(self, pBuf):
        self.command(0x15) # set column address
        self.data(0x00)    # column address start 00
        self.data(0x7f)    # column address end 127
        self.command(0x75) # set row address
        self.data(0x00)    # row address start 00
        self.data(0x7f)    # row address end 127   
        self.command(0x5C); 
        self.dataBuffer(pBuf)
        #for i in range(0, self.height):
        #    for j in range(0, self.width*2):
        #        self.data(pBuf[j + self.width*2*i])
        return

       