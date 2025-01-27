#!/bin/bash

# Paths to Device Tree Source (DTS) and Device Tree Blob (DTB) files
DTS_FILE=/home/pi/sun8i-h3-nanopi-neo.dts
DTB_FILE=/boot/dtb/sun8i-h3-nanopi-neo.dtb

# Check if arguments are provided
if [ $# -eq 0 ]; then
    echo "Error: No arguments provided!"
    echo "Usage:"
    echo "  -c  Compile DTS to DTB"
    echo "  -d  Decompile DTB to DTS"
    echo "  -r  Show current MMC settings"
    exit 1
fi

# Process command-line arguments
case "$1" in
    -c)
        echo "Compiling DTS to DTB..."
        dtc -I dts -O dtb -o "$DTB_FILE" "$DTS_FILE"
        ;;
    -d)
        echo "Decompiling DTB to DTS..."
        dtc -I dtb -O dts -o "$DTS_FILE" "$DTB_FILE"
        ;;
    -r)
        echo "Displaying current MMC settings..."
        cat /sys/kernel/debug/mmc0/ios
        ;;    
    *)
        echo "Error: Unknown argument $1"
        echo "Usage: $0 -c (compile) | -d (decompile) | -r (show MMC settings)"
        exit 1
        ;;
esac

echo "Operation completed successfully."
