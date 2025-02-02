#!/bin/bash

#UBOOT_FILE="/home/pi/automatic-TS-emmc-Writer/u-boot-nxs-0.1.bin"
#!/bin/bash

UBOOT_PATH="/home/pi/automatic-TS-emmc-Writer/"
UBOOT_FILE="mmcblk0boot0.bin"

verify_write() {
    local expected_file="$1"
    local actual_file="$2"
    local expected_size=$(stat --format=%s "$expected_file")
    head -c "$expected_size" "$actual_file" | cmp -s - "$expected_file"
    return $?
}

erase_boot0() {
    sudo sh -c 'echo 0 > /sys/block/mmcblk0boot0/force_ro'
    echo "Erasing boot0..."
    sudo dd if=/dev/zero of=/dev/mmcblk0boot0 bs=1M count=4 status=progress
    echo "Verifying erase..."
    sudo dd if=/dev/mmcblk0boot0 of=boot0_verify_zero.bin bs=1M count=4 status=progress
    if [ "$(head -c 4194304 /dev/zero | cmp -s - boot0_verify_zero.bin; echo $?)" -eq 0 ]; then
        echo "Erase completed"
    else
        echo "Erase failed"
        exit 1
    fi
}

write_boot0() {
    sudo sh -c 'echo 0 > /sys/block/mmcblk0boot0/force_ro'
    echo "Writing U-Boot to boot0...$UBOOT_PATH$UBOOT_FILE"
    sudo dd if="$UBOOT_PATH$UBOOT_FILE" of=/dev/mmcblk0boot0 bs=1M count=4 status=progress
    sleep 2
    echo "Readback U-Boot to verify..."
    sudo dd if=/dev/mmcblk0boot0 of=boot0_verify_write.bin bs=1M count=4 status=progress
    
    if verify_write "$UBOOT_PATH$UBOOT_FILE" boot0_verify_write.bin; then
        echo "Write verification successful."
    else
        echo "Write verification failed."
        exit 1
    fi
}

dump_boot0() {
    echo "Dumping boot0 to $UBOOT_PATH$UBOOT_FILE..."
    sudo dd if=/dev/mmcblk0boot0 of="$UBOOT_PATH$UBOOT_FILE" bs=1M count=4 status=progress
    echo "Dump saved as $UBOOT_PATH$UBOOT_FILE."
}

# Обробка аргументів
while getopts "fwed" opt; do
    case $opt in
        f|w|d)
            ACTION=$opt
            ;;
        e)
            ACTION=$opt
            ;;
        *)
            echo "Invalid option. Use:"
            echo "-f: Full operation (erase, write, verify)"
            echo "-e: Erase boot0"
            echo "-w: Write boot0 and verify"
            echo "-d: Dump boot0 to file"
            exit 1
            ;;
    esac
done

shift $((OPTIND - 1))

if [[ $ACTION == "f" || $ACTION == "w" || $ACTION == "d" ]]; then
    if [[ -n $1 ]]; then
        UBOOT_FILE="$1"
        echo "UBOOT_FILE set to $UBOOT_PATH$UBOOT_FILE"
    fi
fi

case $ACTION in
    f)
        sudo sh -c 'echo 0 > /sys/block/mmcblk0boot0/force_ro'
        echo "File to write: $UBOOT_PATH$UBOOT_FILE"
        erase_boot0
        write_boot0
        ;;
    e)
        sudo sh -c 'echo 0 > /sys/block/mmcblk0boot0/force_ro'
        erase_boot0
        ;;
    w)
        sudo sh -c 'echo 0 > /sys/block/mmcblk0boot0/force_ro'
        write_boot0
        ;;
    d)
        dump_boot0
        ;;
    *)
        echo "Invalid option. Use:"
        echo "-f: Full operation (erase, write, verify)"
        echo "-e: Erase boot0"
        echo "-w: Write boot0 and verify"
        echo "-d: Dump boot0 to file"
        exit 1
        ;;
esac

# Заборонити запис після завершення
#sudo sh -c 'echo 1 > /sys/block/mmcblk0boot0/force_ro'

#sudo cat /sys/kernel/debug/mmc0/ios


#sudo mmc extcsd read /dev/mmcblk0 | grep PARTITION_CONFIG
#sudo mmc bootpart enable 2 0 /dev/mmcblk0
#sudo dd if=u-boot-nxs-0.1.bin of=/dev/mmcblk0boot
#sudo mmc bootpart enable 1 1 /dev/mmcblk0
#sudo sh -c 'echo 0 > /sys/block/mmcblk0boot0/force_ro'

#sudo dd if=boot0_1.img of=/dev/mmcblk0boot0 bs=1M status=progress
#sudo dd if=/dev/zero of=/dev/mmcblk0boot0 bs=1M status=progress

#sudo nano /etc/systemd/system/emmcWriter.service
#sudo systemctl daemon-reload
#sudo systemctl restart emmcWriter.service