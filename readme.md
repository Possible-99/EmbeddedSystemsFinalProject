# Retro Game Console

The Retro Game Console project aims to create an interactive and immersive experience by using a joystick and displaying a list of retro games. It provides functionality to select and play games using the Mednafen emulator. Additionally, it supports USB detection to automatically copy new ROMs to the system.

## Features

### Game List Interface
The system displays a list of available games, allowing users to navigate using a joystick. The interface is designed to be user-friendly with visual cues for game selection.

### Mednafen Emulator Integration
The project integrates the Mednafen emulator to run retro games. It supports various ROM file formats, ensuring a wide range of game compatibility.

### USB Detection and ROM Management
When a USB device is detected, the system mounts it, copies new ROMs to the designated directory, and unmounts the USB. This process is automated to ensure a seamless user experience.

### Startup Sequence
The system plays a startup image and sound when it is initialized, enhancing the retro gaming ambiance.

## Getting Started

### Prerequisites
Ensure the following software is installed on your system:
- Python 3.x

### Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/Possible-99/EmbeddedSystemsFinalProject.git
    cd EmbeddedSystemsFinalProject
    ```

2. Give permissions and run setup script for installing dependencies and loading some settings
    ```bash
        chmod +x setup.sh
        sudo ./setup.sh
    ```

### Running the Project

1. Run the app:
    ```bash
    sudo python app.py
    ```

### Usage

- Navigate the game list using the joystick.
- Press A button for selecting a game.
- Insert a USB device with new ROMs to automatically copy them to the system.

## Code Overview

### State Management
The project uses a state pattern to manage different states of the application:
- `GameMenuState`: Displays the game list and handles game selection.
- `PlayingGameState`: Manages the state when a game is being played.

### USB Handling
The system uses `pyudev` to monitor USB events and handle the mounting, copying, and unmounting of USB devices.

### Mednafen Integration
A separate thread is used to run the Mednafen emulator, ensuring the main application remains responsive.


## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.


