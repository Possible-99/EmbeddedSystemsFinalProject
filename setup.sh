#!/bin/bash

# Update package list and upgrade all packages
sudo apt-get update
sudo apt-get upgrade -y

# Install system dependencies
sudo apt-get install -y python3-pip python3-pygame fim libsdl1.2-dev mednafen xboxdrv joystick fbi 
# Setup xboxdrv
sudo xboxdrv --detach-kernel-driver

# Install Python dependencies
pip3 install -r requirements.txt

export SDL_VIDEODRIVER=fbcon
export SDL_FBDEV=/dev/fb0

echo "Setup complete!"
echo "Now you can run the app.py file with the next command : sudo python3 app.py
