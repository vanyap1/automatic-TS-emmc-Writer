import os
import subprocess
import time
import re
class UbootWorker:

    def ubootRead(self, targetDev, filename):
        filename = f"images/{filename}"
        tmpFile = "images/tmpFile.bin"
        if not os.path.exists(targetDev):
                return f"Target dev {targetDev} not found"
        if os.path.exists(tmpFile):
            print (f"File {tmpFile} found")
            os.remove(tmpFile)
        time.sleep(.5)
        result = subprocess.run(["dd", f"if={targetDev}",  f"of={tmpFile}"], capture_output=True, text=True)
        if result.returncode == 0:
            if os.path.exists(filename):
                os.remove(filename)
                time.sleep(.5)
            os.rename(tmpFile, filename)
            print("operation successful")
            return f"operation successful, {filename} created"
        else:
            print(f"error: {result.stderr}")
            return f"error: {result.stderr}"    
        
                      
        



    def ubootWrite(self, targetDev, filename):
        filename = f"images/{filename}"
        if not os.path.exists(filename):
                return f"File {filename} found"
        if not os.path.exists(targetDev):
            return f"Target dev {targetDev} not found"
        # Set force_ro to 0 before erasing
        force_ro_path = f"/sys/block/{os.path.basename(targetDev)}/force_ro"
        if os.path.exists(force_ro_path):
            subprocess.run(["sudo", "sh", "-c", f"echo 0 > {force_ro_path}"], capture_output=True, text=True)
        else:
            return f"force_ro not found: {force_ro_path}"
        result = subprocess.run(["dd", f"if={filename}", f"of={targetDev}", "bs=1M", "count=4" ], capture_output=True, text=True)
        if result.returncode == 0:
            return f"operation successful; {filename} written to {targetDev}"
        else:
            return f"Error writing {filename} to {targetDev}: {result.stderr}"
        
    
    def ubootVerify(self, targetDev, filename):
        filename = f"images/{filename}"
        tmpFile = "images/tmpFile.bin"
        if os.path.exists(tmpFile):
            print (f"File {tmpFile} found")
            os.remove(tmpFile)
        time.sleep(.5)

        if not os.path.exists(filename):
                return f"File {filename} found"
        if not os.path.exists(targetDev):
                return f"Target dev {targetDev} found"
        
        result = subprocess.run(["dd", f"if={targetDev}",  f"of={tmpFile}"], capture_output=True, text=True)
        if result.returncode == 0:
            with open(filename, 'rb') as f1, open(tmpFile, 'rb') as f2:
                if f1.read() == f2.read():
                    return f"Verification successful: {filename} matches {targetDev}"
                else:
                    return f"Verification failed: {filename} does not match {targetDev}"
        else:
            return f"Error reading from {targetDev}: {result.stderr}"
             
             


    def ubootErase(self, targetDev):
        if not os.path.exists(targetDev):
            return f"Target dev  {targetDev} not found"
        # Set force_ro to 0 before erasing
        force_ro_path = f"/sys/block/{os.path.basename(targetDev)}/force_ro"
        if os.path.exists(force_ro_path):
            subprocess.run(["sudo", "sh", "-c", f"echo 0 > {force_ro_path}"], capture_output=True, text=True)
        else:
            return f"force_ro not found: {force_ro_path}"
        result = subprocess.run(["dd", f"if=/dev/zero", f"of={targetDev}", "bs=1M", "count=4" ], capture_output=True, text=True)
        if result.returncode == 0:
            return f"{targetDev} erased successfully"
        else:
            return f"Error erasing {targetDev}: {result.stderr}"
    

    def getPartOptions(self, targetDev):
        try:
            result = subprocess.run(f"sudo mmc extcsd read /dev/{targetDev} | grep PARTITION_CONFIG", shell=True, capture_output=True, text=True)
            if result.stdout:
                return result.stdout
            else:
                return "No output"
        except subprocess.CalledProcessError as e:
            return f"Device {targetDev} not found"

    '''
        first value
            0 - disable boot partition
            1 - enable boot partition 1
            2 - enable boot partition 2
        second value
            0 - disable access to boot partition
            1 - enable read access to boot partition
            2 - enable write access to boot partition

        Example:
            sudo mmc bootpart enable 1 1 /dev/mmcblk0
            This command enables boot partition 1 and allows read access to it.
    '''
    def setPartOptions(self, targetDev, partConfig):
        targetDev = f"/dev/{targetDev}"
        if not os.path.exists(targetDev):
            return f"Target dev  {targetDev} not found"
        if len(partConfig) > 1:
            if not isinstance(partConfig, str) or len(partConfig) != 2 or partConfig[0] not in "012" or partConfig[1] not in "012":
                return "Invalid format. The format should be two digits, each between 0 and 2."
        try:
            result = subprocess.run(["sudo", "mmc", "bootpart", "enable", partConfig[0], partConfig[1], f"{targetDev}"], capture_output=True, text=True)
            if result.returncode == 0:
                return f"Register set to {partConfig}"
            else:
                return f"Failed to set register: {result.stderr}"
        except subprocess.CalledProcessError as e:
            return f"Error: {e}"

    '''
        Compile new settings to the device tree blob (DTB) file
    '''
    def DTS2DTB(self, dtsFilePath):
        dtbFilePath = "/boot/dtb/sun8i-h3-nanopi-neo.dtb"
        
        if not os.path.exists(dtsFilePath):
            return f"File {dtsFilePath} not found"
        try:
            result = subprocess.run(["sudo", "dtc", "-I", "dts", "-O", "dtb", "-o", dtbFilePath, dtsFilePath], capture_output=True, text=True)
            if result.returncode == 0:
                return f"Successfully compiled {dtsFilePath} to {dtbFilePath}"
            else:
                return f"Failed to compile {dtsFilePath} to {dtbFilePath}: {result.stderr}"
        except subprocess.CalledProcessError as e:
            return f"Error: {e}"
    
    '''
        Decompile the device tree blob (DTB) file to a device tree source (DTS) file
    '''
    def DTB2DTS(self, dtsFilePath):
        dtbFilePath = "/boot/dtb/sun8i-h3-nanopi-neo.dtb"
                
        if not os.path.exists(dtbFilePath):
            return f"File {dtbFilePath} not found"
        try:
            result = subprocess.run(["sudo", "dtc", "-I", "dtb", "-O", "dts", "-o", dtsFilePath, dtbFilePath], capture_output=True, text=True)
            if result.returncode == 0:
                subprocess.run(["sudo", "chmod", "666", dtsFilePath], capture_output=True, text=True)
                return f"Successfully decompiled {dtbFilePath} to {dtsFilePath}"
            else:
                return f"Failed to decompile {dtbFilePath} to {dtsFilePath}: {result.stderr}"
        except subprocess.CalledProcessError as e:
            return f"Error: {e}"
    
    def updateMaxFrequency(self, dtsFilePath, newFrequency, newBusWidth):
        if not os.path.exists(dtsFilePath):
            return f"File {dtsFilePath} not found"
        
        if not isinstance(newFrequency, int) or not (1000000 <= newFrequency <= 52000000):
            return "Invalid frequency value. It should be an integer between 1000000 and 52000000."
        
        if not isinstance(newBusWidth, int) or newBusWidth not in [1, 4, 8]:
            return "Invalid bus width value. It should be 1, 4, or 8."

        try:
            with open(dtsFilePath, 'r') as file:
                content = file.read()

            # Регулярний вираз для знаходження секції mmc@1c0f000
            section_pattern = re.compile(r'(mmc@1c0f000\s*{[^}]*})', re.DOTALL)
            match = section_pattern.search(content)
            if not match:
                return "Section mmc@1c0f000 not found"

            section = match.group(1)

            # Регулярний вираз для знаходження max-frequency
            frequency_pattern = re.compile(r'max-frequency\s*=\s*<0x[0-9a-fA-F]+>;')
            if frequency_pattern.search(section):
                # Заміна значення max-frequency
                updated_section = frequency_pattern.sub(f'max-frequency = <0x{newFrequency:x}>;', section)
            else:
                # Додавання max-frequency перед закриваючою дужкою
                updated_section = section.rstrip('}') + f'    max-frequency = <0x{newFrequency:x}>;\n}}'

            # Регулярний вираз для знаходження bus-width
            bus_width_pattern = re.compile(r'bus-width\s*=\s*<0x[0-9a-fA-F]+>;')
            if bus_width_pattern.search(updated_section):
                # Заміна значення bus-width
                updated_section = bus_width_pattern.sub(f'bus-width = <0x{newBusWidth:x}>;', updated_section)
            else:
                # Додавання bus-width перед закриваючою дужкою
                updated_section = updated_section.rstrip('}') + f'    bus-width = <0x{newBusWidth:x}>;\n}}'

            updated_content = content.replace(section, updated_section)

            with open(dtsFilePath, 'w') as file:
                file.write(updated_content)

            return f"Successfully updated max-frequency to {newFrequency} and bus-width to {newBusWidth} in {dtsFilePath}"
        except Exception as e:
            return f"Error: {e}"
        



    def mmcIfCurrentState(self):
        try:
            result = subprocess.run(["sudo", "cat", "/sys/kernel/debug/mmc0/ios"], capture_output=True, text=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return "Device mmc0 not found"