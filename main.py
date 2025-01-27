import gpiod
import time
import serial

# NanoPi NEO Core
# https://wiki.friendlyelec.com/wiki/index.php/NanoPi_NEO_Core
# sudo apt install python3-libgpiod
# pip install pyserial  # Для роботи з ttyS0

# rules
# /etc/udev/rules.d/99-gpiochip.rules
# /etc/udev/rules.d/99-mmcblk-devices.rules

# sudo mmc extcsd read /dev/mmcblk0 | grep PARTITION_CONFIG

# Ініціалізація чіпа GPIO
# GRN Led gpio num - gpiochip0.10
# GRN Led gpio num - gpiochip1.10
deviceDescriptor = 'emmcWriter'


chip0 = gpiod.Chip('gpiochip0')
chip1 = gpiod.Chip('gpiochip1')


#chip0
#64 - PC0
#65 - PC1
#66 - PC2
#67 - PC3
#1  - PA1

#chip1
#9  - PG9
#

#gld = chip0.get_line(10)

gld = chip0.get_line(1)
rld = chip1.get_line(10)

cmdRun = chip0.get_line(64)
cmdModifier = chip0.get_line(65)

statusOut = chip0.get_line(66)
statusPassFail = chip0.get_line(67)





gld.request(consumer=deviceDescriptor, type=gpiod.LINE_REQ_DIR_OUT)
rld.request(consumer=deviceDescriptor, type=gpiod.LINE_REQ_DIR_OUT)


cmdRun.request(consumer=deviceDescriptor, type=gpiod.LINE_REQ_DIR_IN)
cmdModifier.request(consumer=deviceDescriptor, type=gpiod.LINE_REQ_DIR_IN)

statusOut.request(consumer=deviceDescriptor, type=gpiod.LINE_REQ_DIR_OUT)
statusPassFail.request(consumer=deviceDescriptor, type=gpiod.LINE_REQ_DIR_OUT)

procCmdTimeout = 10

# Ініціалізація серійного порту


def init_serial():
    try:
        ser = serial.Serial(
            port='/dev/ttyS0',
            baudrate=115200,
            timeout=1
        )
        return ser
    except Exception as e:
        print(f"Помилка ініціалізації серійного порту: {e}")
        return None

def print_debug(arg):
    print(arg)
    if ser:
        try:
            ser.write(f"[EMMC] {arg}\n\r".encode())
        except Exception as e:
            print(f"Помилка запису в ttyS0: {e}")
ser = 0 #init_serial()


def writeBoot() -> bool :
    tmpcount = 10
    while (tmpcount != 0):
        tmpcount -=1
        print(f"write boot {tmpcount}")
        time.sleep(.2)
    return True

def readBoot() -> bool :
    tmpcount = 10
    while (tmpcount != 0):
        tmpcount -=1
        print(f"read boot {tmpcount}")
        time.sleep(.2)
    return True


class Main:
    def __init__(self):
        print("Run app...")
        self.run()

    def run(self):
        try:
            while True:
                ioStatus = f"cmdRun: {cmdRun.get_value()} cmdModifier: {cmdModifier.get_value()}"
                if (cmdRun.get_value() == 1):
                    cmd = 1
                    if cmdModifier.get_value():
                        cmd = 0
                    timeout = 0
                    while cmdModifier.get_value():
                        timeout += 1
                        if timeout == procCmdTimeout:
                            cmd = False
                            break
                    print_debug(f"cmd: {cmd}")      
                    if cmd:
                        readBoot()
                    else: 
                        writeBoot()    

                
                
                
                print_debug(ioStatus)
                # Запис у ttyS0
                
                statusPassFail.set_value(1)
                gld.set_value(1)
                statusOut.set_value(1)
                time.sleep(.2)
                gld.set_value(0)
                statusOut.set_value(0)
                time.sleep(.2)

            print("Finish...")
            gld.set_value(0)
            rld.set_value(0)
            statusOut.set_value(0)

        except KeyboardInterrupt:
            print("End of program")
        finally:
            gld.set_value(0)
            rld.set_value(0)
            statusOut.set_value(0)
            statusPassFail.set_value(0)


            gld.release()
            rld.release()
            statusOut.release()
            statusPassFail.release()    
            print_debug("Release GPIO")
            if ser:
                ser.close()

if __name__ == "__main__":
    Main()

