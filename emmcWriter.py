
import os
import subprocess
import time
import re
import gpiod
import json

from PyIODriver.i2c_gpio import  I2CGPIOController, IO, DIR, Expander
from remoteCtrlServer.httpserver import start_server_in_thread
from remoteCtrlServer.udpService import UdpAsyncClient
from uboot import UbootWorker


i2cBus = 0
remCtrlPort = 8080


class NetConn:
    interface_name = "Wired connection 1"
    ipAddr = [192,168,1,114]
    netMask = 24
    gatewayIp = [192,168,1,1]
    dns1ip = [8,8,8,8]
    dns2ip = [8,8,4,4]
    upLinkRequest = True


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
    verifyBoot = "verifyboot"
    eraseBoot = "eraseboot"
    passed = "passed"
    failed = "failed"
    idle = "idle"

class SDCtrld:
    CD = chip1.get_line(11)
class StatusLED:
    GRN = chip0.get_line(10)
    RED = chip1.get_line(10)


StatusLED.GRN.request(consumer=deviceDescriptor, type=gpiod.LINE_REQ_DIR_OUT)
StatusLED.RED.request(consumer=deviceDescriptor, type=gpiod.LINE_REQ_DIR_OUT)

SDCtrld.CD.request(consumer=deviceDescriptor, type=gpiod.LINE_REQ_DIR_OUT)
SDCtrld.CD.set_value(True)

class Main:
    def __init__(self):
        self.uboot = UbootWorker()
        self.expanderAddress = 0x20
        self.slotNum = 0
        self.slotStatus = SlotStatus.idle
        self.beacon = 0
        self.gpio = I2CGPIOController(i2cBus)
        StatusLED.GRN.set_value(True)
        StatusLED.RED.set_value(True)
        '''
        IP config module
        '''
        self.connectionInfo = NetConn()
        boardAddr = self.gpio.scanI2CBus()
        print(boardAddr)
        if(len(boardAddr) and boardAddr[0] >= 0x20 and boardAddr[0] <= 0x27):
            self.expanderAddress = boardAddr[0]
            
            print("Board address is valid")
            self.slotNum = boardAddr[0]-32
            print(f"Slot num: {self.slotNum}")
            
            
            self.connectionInfo.ipAddr[3] = self.connectionInfo.ipAddr[3]+(boardAddr[0]-32)
            print("IP address: ", self.connectionInfo.ipAddr)
            print("netmask: ", self.connectionInfo.netMask)
            print("gateway: ", self.connectionInfo.gatewayIp)
            print("dns1: ", self.connectionInfo.dns1ip)
            print("dns2: ", self.connectionInfo.dns2ip)

            
            
            res = self.change_ip_address(self.connectionInfo)
            self.lanUpLink(self.connectionInfo)
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
        elif(reguest[0] == "id"):
            self.beacon = 6 * 2
            return f"Beacon value set to 6" 
        elif reguest[0].startswith("id="):
            match = re.match(r"id=([0-9]{1,2})$", reguest[0])
            if match:
                self.beacon = int(match.group(1)) * 2
                return f"Beacon value set to {int(match.group(1))}"
            else:
                return "Invalid beacon value, must be between 0 and 9"

        elif(reguest[0] == "rst"):
            if self.emmcConnInitConnection(reguest[0]):
                self.slotStatus = reguest[0]
                return "complete"
            else:
                return "error"
    
        elif(reguest[0] == "jigsw"):
            if self.getJigSwithState():
                return "closed"  
            else:
                return "open"
        
        elif(reguest[0] == "emmcins"):
            if self.isEmmcIncerted():
                return "inserted"
            else:
                return "not inserted"
        elif(reguest[0] == "status"):
            return self.slotStatus
        elif(reguest[0] == "mmcifcheck"):
            return self.uboot.mmcIfCurrentState()
        
        elif(reguest[0] == "dtbsetmaxfreq"):
            return "err: missing value"
        
        elif reguest[0].startswith("dtbsetmaxfreq="):
            arg = reguest[0].split("=")
            try:
                freq = int(arg[1])
            except ValueError:
                return "err: invalid value"
            return self.uboot.updateMaxFrequency("sun8i-h3-nanopi-neo.dts", freq, 1)
        elif(reguest[0] == "restoredevblob"):
            return self.uboot.DTS2DTB("sun8i-h3-nanopi-neo_original.dts")
        
        elif(reguest[0] == "compiledevblob"):
            return self.uboot.DTS2DTB("sun8i-h3-nanopi-neo.dts")
        
        elif(reguest[0] == "decompiledevblob"):
            return self.uboot.DTB2DTS("sun8i-h3-nanopi-neo.dts")
        
        elif reguest[0] == "binlist":
            try:
                result = subprocess.run("ls *.bin", shell=True, capture_output=True, text=True)
                if result.stdout:
                    return result.stdout
                else:
                    return "No output"
            except subprocess.CalledProcessError as e:
                return "err: shell error"
        
        
        elif reguest[0] == "mmcbootoptset":
            return "err: missing value"    
        
        elif reguest[0].startswith("mmcbootoptset="):
            arg = reguest[0].split("=")
            return self.uboot.setPartOptions("mmcblk0", arg[1])
        
        elif(reguest[0] == "mmcbootoptget"):
            #sudo mmc extcsd read /dev/mmcblk0 | grep PARTITION_CONFIG
            return self.uboot.getPartOptions("mmcblk0")

        elif(reguest[0] == "readboot" or 
             reguest[0] == "writeboot" or
             reguest[0] == "eraseboot" or
             reguest[0] == "verifyboot"):
            return "err: incorrect command format. correct - readboot=filename.bin/bootpart0"

        elif(reguest[0].startswith("readboot=") and len(reguest) >= 2):
            self.gpio.pinWrite(self.busyLED, True)
            self.slotStatus = SlotStatus.readBoot
            targetDev = f"/dev/{reguest[0].split("=")[1]}"
            targetFile = reguest[1]
            if not targetFile.endswith(".bin"):
                return "Invalid file extension. Only .bin files are allowed."
            print(f"readboot targetDev: {targetDev}, targetFile: {targetFile}")
            res = self.uboot.ubootRead(targetDev, targetFile)
            self.gpio.pinWrite(self.busyLED, False)
            self.slotStatus = SlotStatus.idle
            return res
        
        elif(reguest[0].startswith("writeboot=") and len(reguest) >= 2):
            self.gpio.pinWrite(self.busyLED, True)
            self.slotStatus = SlotStatus.writeBoot
            targetDev = f"/dev/{reguest[0].split("=")[1]}"
            targetFile = reguest[1]
            if not targetFile.endswith(".bin"):
                return "Invalid file extension. Only .bin files are allowed."
            print(f"writeboot targetDev: {targetDev}, targetFile: {targetFile}")
            res = self.uboot.ubootWrite(targetDev, targetFile)
            self.gpio.pinWrite(self.busyLED, False)
            self.slotStatus = SlotStatus.idle
            return res
        
        elif(reguest[0].startswith("verifyboot=") and len(reguest) >= 2):
            self.gpio.pinWrite(self.busyLED, True)
            self.slotStatus = SlotStatus.verifyBoot
            targetDev = f"/dev/{reguest[0].split("=")[1]}"
            targetFile = reguest[1]
            if not targetFile.endswith(".bin"):
                return "Invalid file extension. Only .bin files are allowed."
            print(f"verifyboot targetDev: {targetDev}, targetFile: {targetFile}")
            res = self.uboot.ubootVerify(targetDev, targetFile)
            self.gpio.pinWrite(self.busyLED, False)
            self.slotStatus = SlotStatus.idle
            return res  
        
        elif(reguest[0].startswith("eraseboot=") and len(reguest) >= 1):
            self.gpio.pinWrite(self.busyLED, True)
            self.slotStatus = SlotStatus.eraseBoot
            targetDev = f"/dev/{reguest[0].split("=")[1]}"
            print(f"eraseboot targetDev: {targetDev}")
            res = self.uboot.ubootErase(targetDev)
            self.gpio.pinWrite(self.busyLED, False)
            self.slotStatus = SlotStatus.idle        
            return res
        

       
        elif(reguest[0] == "filecheck" or reguest[0].startswith("filecheck=")):
            arg = reguest[0].split("=")
            filename = arg[1] if len(arg) > 1 else "mmcblk0boot0.bin"
            if os.path.exists(filename):
                return f"File {filename} found"
            return "err: File not found"
        
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
                newNetConn = NetConn()
                newNetConn.ipAddr = [int(octet) for octet in ip_address.split('.')]
                print("New IP address: ", newNetConn.ipAddr)
                print("Current IP address: ", self.connectionInfo.ipAddr)
                print("netmask: ", self.connectionInfo.netMask)
                print("gateway: ", self.connectionInfo.gatewayIp)
                print("dns1: ", self.connectionInfo.dns1ip)
                print("dns2: ", self.connectionInfo.dns2ip)
                return self.change_ip_address(newNetConn)


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
            SDCtrld.CD.set_value(False)
            return True
        elif destIf == "crpi":
            SDCtrld.CD.set_value(True)
            time.sleep(.2)
            self.gpio.pinWrite(self.busyLED, True) 

            self.gpio.pinWrite(self.emmcChRel, False)     #EMMC Power switching relay, swtich to USB reader
            self.gpio.pinWrite(self.muxCtrl, True)        #EMMC data lines HS analog mux, swtich to USB reader
            time.sleep(.5)
            self.gpio.pinWrite(self.emmcCD, True)         #Enable eMMC card detection line (USB reader)
            return True
        elif destIf == "rst":
            SDCtrld.CD.set_value(True)
            self.gpio.pinWrite(self.busyLED, True) 

            self.gpio.pinWrite(self.emmcChRel, False)     #EMMC Power switching relay, swtich to USB reader
            self.gpio.pinWrite(self.muxCtrl, True)        #EMMC data lines HS analog mux, swtich to USB reader
            time.sleep(.5)
            self.gpio.pinWrite(self.emmcCD, False)         #Enable eMMC card detection line (USB reader)
            return True
        else:
            return False

        

    def setStatusdisplay(self, ledState: int):
        
        self.gpio.pinWrite(self.okLED, (ledState & 0x01) != 0)
        self.gpio.pinWrite(self.busyLED, (ledState & 0x02) != 0)
        self.gpio.pinWrite(self.errLED, (ledState & 0x04) != 0)

        pass

    def change_ip_address(self, connectionInfo: NetConn):
        
        try:
            result = subprocess.run(
                ["nmcli", "-g", "IP4.ADDRESS", "con", "show", connectionInfo.interface_name],
                capture_output=True, text=True, check=True
            )
            current_ip = list(map(int, result.stdout.strip().split('/')[0].split('.')))
    
            print(f"Current IP: {current_ip}")
            print(f"New IP: {connectionInfo.ipAddr}")
            
            if current_ip == connectionInfo.ipAddr:
                return f"IP-not reason to change {connectionInfo.ipAddr} for connection {connectionInfo.ipAddr}."
            
            subprocess.run(
                ["sudo", "nmcli", "con", "mod", connectionInfo.interface_name, "ipv4.addresses", f"{connectionInfo.ipAddr[0]}.{connectionInfo.ipAddr[1]}.{connectionInfo.ipAddr[2]}.{connectionInfo.ipAddr[3]}/{connectionInfo.netMask}"],
                check=True
            )
            subprocess.run(
                ["sudo", "nmcli", "con", "mod", connectionInfo.interface_name, "ipv4.gateway", f"{connectionInfo.gatewayIp[0]}.{connectionInfo.gatewayIp[1]}.{connectionInfo.gatewayIp[2]}.{connectionInfo.gatewayIp[3]}"],
                check=True
            )
            subprocess.run(
                ["sudo", "nmcli", "con", "mod", connectionInfo.interface_name, "ipv4.dns", f"{connectionInfo.dns1ip[0]}.{connectionInfo.dns1ip[1]}.{connectionInfo.dns1ip[2]}.{connectionInfo.dns1ip[3]}, {connectionInfo.dns2ip[0]}.{connectionInfo.dns2ip[1]}.{connectionInfo.dns2ip[2]}.{connectionInfo.dns2ip[3]}"],
                check=True
            )
            subprocess.run(
                ["sudo", "nmcli", "con", "mod", connectionInfo.interface_name, "ipv4.method", "manual"],
                check=True
            )
            self.connectionInfo.upLinkRequest = True
            return f"IP-changet to {connectionInfo.ipAddr} for connection: {connectionInfo.interface_name}."
        except subprocess.CalledProcessError as e:
            return f"err: {e}"

    def lanUpLink(self, connectionInfo: NetConn):
        try:
            subprocess.run(
                ["sudo", "nmcli", "con", "up", connectionInfo.interface_name],
                check=True
            )
            self.connectionInfo.upLinkRequest = False
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
                    "slotIp" : self.connectionInfo.ipAddr,
                    "emmcDetect": self.isEmmcIncerted(),
                    "jigSwitch": self.getJigSwithState()
                }              
                json_data = json.dumps(self.data)
                self.udpClient.send_data(json_data, "192.168.1.255", udpReporIpPort)
                if self.connectionInfo.upLinkRequest:
                    self.lanUpLink(self.connectionInfo)
                if self.beacon > 0:
                    self.gpio.pinWrite(self.busyLED, self.beacon % 2 == 0)
                    self.beacon -= 1
                time.sleep(0.5)
        
        finally:
            self.gpio.pinWrite(self.busyLED, False)
            self.gpio.pinWrite(self.okLED, False)
            self.gpio.pinWrite(self.errLED, False)
            self.gpio.pinWrite(self.emmcChRel, False)
            self.gpio.pinWrite(self.emmcCD, False)
            self.gpio.pinWrite(self.muxCtrl, False)
            time.sleep(0.3)
            self.gpio.stopController()
            self.udpClient.stopListener()
            self.server.shutdown()
            self.emmcConnInitConnection("rst")
            StatusLED.GRN.set_value(False)
            StatusLED.RED.set_value(False)
            SDCtrld.CD.set_value(True)
            StatusLED.GRN.release()
            StatusLED.RED.release()
            SDCtrld.CD.release()


if __name__ == '__main__':
    Main()