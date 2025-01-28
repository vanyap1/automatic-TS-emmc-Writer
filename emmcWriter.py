
import os
import subprocess
import time
import re
import gpiod
import json

from PyIODriver.i2c_gpio import  I2CGPIOController, IO, DIR, Expander
from remoteCtrlServer.httpserver import start_server_in_thread
from remoteCtrlServer.udpService import UdpAsyncClient


i2cBus = 0
remCtrlPort = 8080
baseIpAddr = [192,168,1,114]
udpReporIp = [192,168,1,255]
udpReporIpPort = 8088


chip0 = gpiod.Chip('gpiochip0')
chip1 = gpiod.Chip('gpiochip1')
deviceDescriptor = 'emmcWriter'



class SlotStatus:
    connUSB = "crpi"
    connOPI = "copi"
    reset = "rst"
    writeBoot = "writeboot"
    readBoot = "readboot"
    passed = "passed"
    failed = "failed"
    idle = "idle"

class StatusLED:
    GRN = chip0.get_line(10)
    RED = chip1.get_line(10)

StatusLED.GRN.request(consumer=deviceDescriptor, type=gpiod.LINE_REQ_DIR_OUT)
StatusLED.RED.request(consumer=deviceDescriptor, type=gpiod.LINE_REQ_DIR_OUT)


class Main:
    def __init__(self):
        self.expanderAddress = 0x20
        self.slotNum = 0
        self.slotIpAddr = baseIpAddr.copy()
        self.slotStatus = SlotStatus.idle
        self.gpio = I2CGPIOController(i2cBus)
        StatusLED.GRN.set_value(True)
        StatusLED.RED.set_value(True)
        '''
        IP config module
        '''
        boardAddr = self.gpio.scanI2CBus()
        print(boardAddr)
        if(len(boardAddr) and boardAddr[0] >= 0x20 and boardAddr[0] <= 0x27):
            self.expanderAddress = boardAddr[0]
            self.slotIpAddr = baseIpAddr.copy()
            print("Board address is valid")
            self.slotNum = boardAddr[0]-32
            print(f"Slot num: {self.slotNum}")
            self.slotIpAddr[3] = self.slotIpAddr[3]+(boardAddr[0]-32)  
            print(baseIpAddr)
            print(self.slotIpAddr)
            res = self.change_ip_address(f"{self.slotIpAddr[0]}.{self.slotIpAddr[1]}.{self.slotIpAddr[2]}.{self.slotIpAddr[3]}")
            print(res)

        StatusLED.RED.set_value(False)

        self.gpioExpander = Expander(Expander.PCA9535)
        self.gpioExpander.addr = self.expanderAddress
        self.runStateShield = IO(expander = self.gpioExpander, portNum = 0, pinNum = 6, pinDir=DIR.INPUT)
        self.passFailState = IO(expander = self.gpioExpander, portNum = 0, pinNum = 4, pinDir=DIR.INPUT)
        
        self.piShieldCmdRun = IO(expander = self.gpioExpander, portNum = 0, pinNum = 3, pinDir=DIR.OUTPUT)
        self.piShieldCmdModifier = IO(expander = self.gpioExpander, portNum = 0, pinNum = 5, pinDir=DIR.OUTPUT)
        
        
        self.p0 = IO(expander = self.gpioExpander, portNum = 0, pinNum = 0, pinDir=DIR.INPUT)
        self.p1 = IO(expander = self.gpioExpander, portNum = 0, pinNum = 1, pinDir=DIR.INPUT)
        self.p2 = IO(expander = self.gpioExpander, portNum = 0, pinNum = 2, pinDir=DIR.INPUT)
        self.p7 = IO(expander = self.gpioExpander, portNum = 0, pinNum = 7, pinDir=DIR.INPUT)

        self.jigSw = IO(expander = self.gpioExpander, portNum = 1, pinNum = 0, pinDir=DIR.INPUT)
        self.emmcDet = IO(expander = self.gpioExpander, portNum = 1, pinNum = 1, pinDir=DIR.INPUT)
        self.emmcChRel = IO(expander = self.gpioExpander, portNum = 1, pinNum = 2, pinDir=DIR.OUTPUT)
        self.okLED =IO(expander = self.gpioExpander, portNum = 1, pinNum = 3, pinDir=DIR.OUTPUT)
        self.busyLED =IO(expander = self.gpioExpander, portNum = 1, pinNum = 4, pinDir=DIR.OUTPUT)
        self.errLED =IO(expander = self.gpioExpander, portNum = 1, pinNum = 5, pinDir=DIR.OUTPUT)
        self.emmcCD = IO(expander = self.gpioExpander, portNum = 1, pinNum = 6, pinDir=DIR.OUTPUT)
        self.muxCtrl = IO(expander = self.gpioExpander, portNum = 1, pinNum = 7, pinDir=DIR.OUTPUT)

        #Add expanders to controller
        self.gpio.addExpandersInfo(self.gpioExpander)

        #IO direction and initial state setup
        self.gpio.setPinDirection(self.runStateShield, False)
        
        
        st = True
        self.gpio.setPinDirection(self.piShieldCmdRun, st)
        self.gpio.setPinDirection(self.piShieldCmdModifier, st)
        self.gpio.setPinDirection(self.p0, st)
        self.gpio.setPinDirection(self.p1, st)
        self.gpio.setPinDirection(self.p2, st)
        self.gpio.setPinDirection(self.p7, st)

        
        self.gpio.setPinDirection(self.emmcDet, False)
        self.gpio.setPinDirection(self.muxCtrl, True)
        self.gpio.setPinDirection(self.emmcCD, True)
        self.gpio.setPinDirection(self.jigSw, False)
        self.gpio.setPinDirection(self.busyLED, True)
        self.gpio.setPinDirection(self.okLED, False)
        self.gpio.setPinDirection(self.errLED, True)
        self.gpio.setPinDirection(self.emmcChRel, True)

        self.gpio.startController()
        self.server, self.server_thread = start_server_in_thread(remCtrlPort, self.remCtrlCB, self) #Start remote control server
        self.muxVal = True
        self.i2cDevList = self.gpio.scanI2CBus()
        print(f"i2c found {self.i2cDevList}")

        self.udpClient = UdpAsyncClient(self)                   #Start UDP report server
        self.loop()

        

    def remCtrlCB(self, arg):                                   #Remote control callback
        #['', 'slot', '0', 'status']
        reguest = arg.lower().split("/")                        #Split request to array
        print("CB arg-", reguest )
        if(reguest[0] == "crpi" or reguest[0] == "copi"):
            if self.isEmmcIncerted():
                if self.emmcConnInitConnection(reguest[0]):
                    self.slotStatus = reguest[0]
                    return "complete"
                else:
                    return "error"
            else:
                return "err; eMMC not inserted"
        elif(reguest[0] == "rst"):
            if self.emmcConnInitConnection(reguest[0]):
                self.slotStatus = reguest[0]
                return "complete"
            else:
                return "error"
    
        elif(reguest[0] == "jigsw"):
            if self.getJigSwithState():
                return "1"  
            else:
                return "0"
        
        elif(reguest[0] == "emmcins"):
            if self.isEmmcIncerted():
                return "1"
            else:
                return "0"
        
        elif(reguest[0] == "readboot"):
            StatusLED.RED.set_value(True)
            self.gpio.pinWrite(self.busyLED, True)
            self.slotStatus = SlotStatus.writeBoot
            res = self.bootImageHandle("read")
            self.gpio.pinWrite(self.busyLED, False)
            StatusLED.RED.set_value(False)
            return res
        elif(reguest[0] == "eraseboot"):
            self.gpio.pinWrite(self.busyLED, True)
            StatusLED.RED.set_value(True)
            self.slotStatus = SlotStatus.writeBoot
            res = self.bootImageHandle("erase")
            self.gpio.pinWrite(self.busyLED, False)
            StatusLED.RED.set_value(False)
            return res
        elif(reguest[0] == "writeboot"):
            StatusLED.RED.set_value(True)
            self.gpio.pinWrite(self.busyLED, True)
            self.slotStatus = SlotStatus.writeBoot
            res = self.bootImageHandle("write")
            self.gpio.pinWrite(self.busyLED, False)
            StatusLED.RED.set_value(False)
            return res
        elif reguest[0].startswith("led="):
            match = re.match(r"led=([0-7])$", reguest[0])
            if match:
                self.setStatusdisplay(int(match.group(1)))
                return f"LED value set to {int(match.group(1))}"
            else:
                return "Invalid LED value, must be between 0 and 7"

        elif reguest[0].startswith("setip="):
            ip_address = reguest[0].split("=")[1]
            if re.match(r"^192\.168\.1\.(1[0-9]{2}|200)$", ip_address):
                self.slotIpAddr = [int(octet) for octet in ip_address.split('.')]
                return self.change_ip_address(ip_address)
            else:
                return "err: Invalid IP address (Ip must be in range 192.168.1.100-200)"
        
        return "err: unknown command"


    def isEmmcIncerted(self):                                                   #Check eMMC card detection line
        return self.gpio.pinRead(self.emmcDet)
    def getJigSwithState(self):                                                 #Check Jig switch state
        return self.gpio.pinRead(self.jigSw)
    
    def emmcConnInitConnection(self, destIf):                                   #EMMC connection interface switcher
        '''
        Switching between OPI Shield and USB reader interfaces 
        connect eMMC card to OPI Shield or USB reader
            USB - cmd = "crpi"
                emmcChRel = False
                muxCtrl = True
                short delay
                emmcCD = True
            
            OPI Shield - cmd = "copi"
                emmcCD = False
                short delay
                emmcChRel = True
                muxCtrl = False
        '''
        if destIf == "copi":
            self.gpio.pinWrite(self.busyLED, True)        #
            self.gpio.pinWrite(self.emmcCD, False)        #Disable eMMC card detection line (USB reader)
            time.sleep(1.5)

            self.gpio.pinWrite(self.emmcChRel, True)      #EMMC Power switching relay, swtich to OPI Shield
            self.gpio.pinWrite(self.muxCtrl, False)       #EMMC data lines HS analog mux, swtich to OPI Shield
            
            return True
        elif destIf == "crpi":
            
            self.gpio.pinWrite(self.busyLED, True) 

            self.gpio.pinWrite(self.emmcChRel, False)     #EMMC Power switching relay, swtich to USB reader
            self.gpio.pinWrite(self.muxCtrl, True)        #EMMC data lines HS analog mux, swtich to USB reader
            time.sleep(.5)
            self.gpio.pinWrite(self.emmcCD, True)         #Enable eMMC card detection line (USB reader)
            return True
        elif destIf == "rst":
            
            self.gpio.pinWrite(self.busyLED, True) 

            self.gpio.pinWrite(self.emmcChRel, False)     #EMMC Power switching relay, swtich to USB reader
            self.gpio.pinWrite(self.muxCtrl, True)        #EMMC data lines HS analog mux, swtich to USB reader
            time.sleep(.5)
            self.gpio.pinWrite(self.emmcCD, False)         #Enable eMMC card detection line (USB reader)
            return True
        else:
            return False

    def bootImageHandle(self, opcode):
        if opcode == "write":
            if os.path.exists("/dev/mmcblk0"):
                result = subprocess.run(["./emmcPrepare.sh", "-w"], capture_output=True, text=True)
                return result.stdout
            else:
                return "Device /dev/mmcblk0 not found"
        elif opcode == "erase":
            if os.path.exists("/dev/mmcblk0"):
                result = subprocess.run(["./emmcPrepare.sh", "-e"], capture_output=True, text=True)
                return result.stdout
            else:
                return "Device /dev/mmcblk0 not found"
            
        elif opcode == "read":
            if os.path.exists("/dev/mmcblk0"):
                result = subprocess.run(["./emmcPrepare.sh", "-d"], capture_output=True, text=True)
                return result.stdout
            else:
                return "Device /dev/mmcblk0 not found"
        pass
        

    def setStatusdisplay(self, ledState: int):
        
        self.gpio.pinWrite(self.okLED, (ledState & 0x01) != 0)
        self.gpio.pinWrite(self.busyLED, (ledState & 0x02) != 0)
        self.gpio.pinWrite(self.errLED, (ledState & 0x04) != 0)

        pass

    def change_ip_address(self, ip_address: str):
        interface_name = "Wired connection 1"
        interface = "end0"
        gateway = "192.168.1.1"
        dns_servers = "8.8.8.8,8.8.4.4"

        try:
            result = subprocess.run(
                ["nmcli", "-g", "IP4.ADDRESS", "con", "show", interface_name],
                capture_output=True, text=True, check=True
            )
            current_ip = result.stdout.strip().split('/')[0]
            if current_ip == ip_address:
                return f"IP-not reason to change {ip_address} for if {interface}."
            subprocess.run(
                ["sudo", "nmcli", "con", "mod", interface_name, "ipv4.addresses", f"{ip_address}/24"],
                check=True
            )
            subprocess.run(
                ["sudo", "nmcli", "con", "mod", interface_name, "ipv4.gateway", gateway],
                check=True
            )
            subprocess.run(
                ["sudo", "nmcli", "con", "mod", interface_name, "ipv4.dns", dns_servers],
                check=True
            )
            subprocess.run(
                ["sudo", "nmcli", "con", "mod", interface_name, "ipv4.method", "manual"],
                check=True
            )
            subprocess.run(
                ["sudo", "nmcli", "con", "up", interface_name],
                check=True
            )
            return f"IP-адресу змінено на {ip_address} для інтерфейсу {interface}."
        except subprocess.CalledProcessError as e:
            return f"err: {e}"


    def loop(self):
                    
        self.udpReportIp = f"{udpReporIp[0]}.{udpReporIp[1]}.{udpReporIp[2]}.{udpReporIp[3]}"
        try:
        
            self.muxVal = True
            while(True):
                #print("RUN")
                #self.gpio.pinWrite(self.busyLED, self.muxVal)
                #self.muxVal = not self.muxVal

                self.data = {
                    "slotStatus": self.slotStatus,
                    "slotNum": self.slotNum,
                    "slotIp" : self.slotIpAddr,
                    "emmcDetect": self.isEmmcIncerted(),
                    "jigSwitch": self.getJigSwithState()
                }              
                json_data = json.dumps(self.data)
                self.udpClient.send_data(json_data, "192.168.1.255", udpReporIpPort)
                time.sleep(0.5)
        finally:
            self.emmcConnInitConnection("rst")
            StatusLED.GRN.set_value(False)
            StatusLED.RED.set_value(False)
            StatusLED.GRN.release()
            StatusLED.RED.release()


if __name__ == '__main__':
    Main()