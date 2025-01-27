from i2c_gpio import  I2CGPIOController, IO, DIR, Expander
import time

i2cBus = 0

expander1 = Expander(Expander.PCA9535)
expander2 = Expander(Expander.PCF8574)

class Main:
    def __init__(self):
        self.gpio = I2CGPIOController(i2cBus)
        self.btnS1 = IO(expander = expander1, portNum = 0, pinNum = 0, pinDir=DIR.INPUT)
        self.btnS2 = IO(expander = expander1, portNum = 0, pinNum = 1, pinDir=DIR.INPUT)
        self.btnS3 = IO(expander = expander1, portNum = 0, pinNum = 2, pinDir=DIR.INPUT)

        self.led1 = IO(expander = expander1, portNum = 0, pinNum = 3, pinDir=DIR.OUTPUT)
        self.led2 = IO(expander = expander1, portNum = 0, pinNum = 4, pinDir=DIR.OUTPUT)

        self.out1 = IO(expander = expander1, portNum = 0, pinNum = 5, pinDir=DIR.OUTPUT)
        self.out2 = IO(expander = expander1, portNum = 0, pinNum = 6, pinDir=DIR.OUTPUT)
        self.out3 = IO(expander = expander1, portNum = 0, pinNum = 7, pinDir=DIR.OUTPUT)

        self.io2 = IO(expander = expander1, portNum = 1, pinNum = 2, pinDir=DIR.OUTPUT)
        
        self.gpio.addExpandersInfo(expander1)
        #gpio.addExpandersInfo(expander2)

        self.gpio.setPinDirection(self.btnS1, False)
        self.gpio.setPinDirection(self.btnS2, False)
        self.gpio.setPinDirection(self.btnS3, False)
        self.gpio.setPinDirection(self.led1, False)
        self.gpio.setPinDirection(self.led2, False)
        self.gpio.setPinDirection(self.out1, False)
        self.gpio.setPinDirection(self.out2, False)
        self.gpio.setPinDirection(self.out3, False)
        
        self.gpio.startController()
        self.loop()


    def loop(self):
        muxVal = True
        while(True):
            self.gpio.pinWrite(self.led1, muxVal)
            self.gpio.pinWrite(self.led2, self.gpio.pinRead(self.btnS1))
            self.gpio.pinWrite(self.io2, muxVal)

            if self.gpio.pinRead(self.btnS1):
                print("S1")   
            if self.gpio.pinRead(self.btnS2):
                print("S2")
            if self.gpio.pinRead(self.btnS3):
                print("S3")
            muxVal = not muxVal
            time.sleep(0.1)



if __name__ == '__main__':
    Main()
        
    
    
