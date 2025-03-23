import spidev
import gpiod
import time

#cs -PC3
# rst - PJ9
# dc - PA1








class Main:
    def __init__(self):
        self.deviceDescriptor = "any"
        self.spi = spidev.SpiDev()
        self.chip0 = gpiod.Chip('gpiochip0')
        self.chip1 = gpiod.Chip('gpiochip1')
        self.deviceDescriptor = 'oledLCD'
        self.spi_dc = self.chip0.get_line(1) #OK
        self.spi_rst = self.chip0.get_line(6) #OK
        self.spi_cs = self.chip0.get_line(3)

        self.spi_dc.request(consumer=self.deviceDescriptor, type=gpiod.LINE_REQ_DIR_OUT)
        self.spi_rst.request(consumer=self.deviceDescriptor, type=gpiod.LINE_REQ_DIR_OUT)
        self.spi_cs.request(consumer=self.deviceDescriptor, type=gpiod.LINE_REQ_DIR_OUT)
        
        

        
        
        
        self.loop()

    def loop(self):
        while (1):
            time.sleep(0.2)
            self.spi.open(0, 0)  # SPI0, CS0
            self.spi.max_speed_hz = 1000000  # 500 кГц

            self.spi_cs.set_value(0)
            data_to_send = [0xAA]  # Відправляємо байт 0xAA
            received_data = self.spi.xfer2(data_to_send)  # Передача та прийом
            self.spi_cs.set_value(1)
            print("Received:", received_data)
            self.spi.close()





if __name__ == "__main__":
    Main()