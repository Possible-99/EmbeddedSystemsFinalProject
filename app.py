"""
Author: Juan Sanchez
License: MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated 
documentation files (the "Software"), to deal in the Software without restriction, including without limitation 
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, 
and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE 
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR 
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR 
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
from abc import ABC, abstractmethod
import os
import pygame
from utils.roms import get_names_in_folder
import threading
import subprocess
import pyudev
import shutil
import psutil
import time

# State interface
class State(ABC):
    @abstractmethod
    def handle_event(self, context, event):
        # Manage state transitions based on the event
        pass

# Flag to signal stopping the Mednafen thread
stop_thread = False

# Function to run the Mednafen emulator with a specified game
def run_mednafen(game_path):
    global stop_thread
    print("Executing on this game path " + game_path)
    process = subprocess.Popen(["sudo", '/usr/games/mednafen', game_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc = psutil.Process(process.pid)  # Get the process ID
    
    # Periodically check if the process should be stopped
    while process.poll() is None:
        if stop_thread:
            for child in proc.children(recursive=True):  # Kill child processes
                subprocess.run(["sudo", "kill", "-9", str(child.pid)])
            subprocess.run(["sudo", "kill", "-9", str(proc.pid)])  # Kill main process
            break
    process.wait()
    stop_thread = False
    return process.returncode

# Function to handle the event after Mednafen has finished running
def mednafen_finished_event():
    other_events.append(Event(Event.GAME_CLOSED))

# Function to run Mednafen in a separate thread
def mednafen_thread(game_name):
    result = run_mednafen("./roms/" + game_name)
    mednafen_finished_event()

# Function to stop the Mednafen thread
def stop_mednafen_thread():
    global stop_thread
    stop_thread = True

# State representing the game menu
class GameMenuState(State):
    def __init__(self):
        self.pointer_x = None
        self.pointer_y = None

    def handle_event(self, context, event):
        global games_list
        if event.event_type == Event.JOYSTICK_MOVED:
            self.render(context, event.data['games_list'])  # Render game list on joystick movement
        elif event.event_type == Event.USB_DETECTED:
            mount_point = mount_usb(event.data["device"])
            copy_roms(mount_point , "./roms")
            unmount_usb(mount_point)
            games_list = get_names_in_folder("./roms/")
            context.state.render(context, games_list)  # Re-render game list after USB detection
        elif event.event_type == Event.PRESSED_BUTTON:
            pygame.quit()  # Quit pygame to launch the game
            mednafen_process_thread = threading.Thread(target = mednafen_thread , args = (event.data["name"], ))
            mednafen_process_thread.start()  # Start Mednafen thread
            context.state = PlayingGameState()  # Transition to PlayingGameState

    def render(self, context, games_list):
        info = pygame.display.Info()
        screen_width = info.current_w
        screen_height = info.current_h
        screen = pygame.display.get_surface()
        joystick = pygame.joystick.Joystick(0)
        font = pygame.font.SysFont('Arial', 16)
        pygame.display.set_caption("Game List")
        colors = {
            "background": (46, 52, 64),
            "list_bg": (59, 66, 82),
            "list_element_bg": (76, 86, 106),
            "list_element_hover_bg": (94, 129, 172),
            "text": (236, 239, 244),
            "instruction_text": (136, 192, 208)
        }

        # Function to draw text on the screen
        def draw_text(text, color, surface, x, y):
            textobj = font.render(text, True, color)
            textrect = textobj.get_rect()
            textrect.topleft = (x, y)
            surface.blit(textobj, textrect)

        margin = 0.01 * screen_width
        list_bg_width = screen_width - 2 * margin
        list_bg_height = screen_height - 2 * margin
        list_bg_x = margin
        list_bg_y = margin

        if self.pointer_x is None or self.pointer_y is None:
            self.pointer_x = screen_width // 2
            self.pointer_y = screen_height // 2

        axis_x = joystick.get_axis(0)
        axis_y = joystick.get_axis(1)

        # Update pointer position based on joystick input
        self.pointer_x += int(axis_x * 10)
        self.pointer_y += int(axis_y * 10)

        self.pointer_x = max(0, min(screen_width, self.pointer_x))
        self.pointer_y = max(0, min(screen_height, self.pointer_y))

        screen.fill(colors["background"])
        list_bg_rect = pygame.Rect(list_bg_x, list_bg_y, list_bg_width, list_bg_height)
        pygame.draw.rect(screen, colors["list_bg"], list_bg_rect)
        instruction_x = list_bg_x + 20
        instruction_y = list_bg_y + 20
        draw_text("Please select a game:", colors["instruction_text"], screen, instruction_x, instruction_y)

        element_height = 40
        element_margin_y = 60
        for i, game in enumerate(games_list):
            element_y = instruction_y + element_margin_y + i * (element_height + 10)
            element_rect = pygame.Rect(instruction_x, element_y, list_bg_width - 40, element_height)

            if element_rect.collidepoint((self.pointer_x, self.pointer_y)):
                pygame.draw.rect(screen, colors["list_element_hover_bg"], element_rect)  # Highlight hovered element
            else:
                pygame.draw.rect(screen, colors["list_element_bg"], element_rect)

            draw_text(game, colors["text"], screen, element_rect.x + 10, element_rect.y + 10)

            if joystick.get_button(0) and element_rect.collidepoint((self.pointer_x, self.pointer_y)):
                pygame.event.post(pygame.event.Event(pygame.USEREVENT, name=game))  # Post event if button is pressed
                return

        pygame.draw.circle(screen, colors["text"], (self.pointer_x, self.pointer_y), 5)

# State representing the game being played
class PlayingGameState(State):
    def handle_event(self, context, event):
        global games_list
        if event.event_type == Event.GAME_CLOSED:
            # Output: Transition to Game Menu
            initialize_pygame()
            context.state = GameMenuState()
            context.state.render(context , games_list=games_list)
        elif event.event_type == Event.USB_DETECTED:
            # Output: Transition to Game Menu
            mount_point = mount_usb(event.data["device"])
            stop_mednafen_thread()
            copy_roms(mount_point , "./roms")
            unmount_usb(mount_point)
            games_list = get_names_in_folder("./roms/")
            initialize_pygame()
            context.state = GameMenuState()
            context.state.render(context, games_list)

# Event definitions
class Event:
    JOYSTICK_MOVED = 'Joystick Moved'
    USB_DETECTED = 'Usb detected'
    PRESSED_BUTTON = 'Pressed button'
    GAME_CLOSED = 'Game Closed'
    
    def __init__(self , event_type , **kwargs):
        self.event_type = event_type
        self.data = kwargs

# Context class to maintain current state
class Context:
    def __init__(self):
        self.state = GameMenuState()  # Initial state

    def handle_event(self, event):
        self.state.handle_event(self, event)

# Function to monitor USB device events
def monitor_usb():
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem='block', device_type='partition')
    observer = pyudev.MonitorObserver(monitor, lambda action, device: handle_device_event(action, device))
    observer.start()

# Function to handle USB device events
def handle_device_event(action, device):
    if action == "add":
        other_events.append(Event(Event.USB_DETECTED , device = device))

# Function to mount a USB device
def mount_usb(device):
    mount_point = f"/mnt/{device.device_node.split('/')[-1]}"
    os.makedirs(mount_point, exist_ok=True)
    try:
        subprocess.run(['sudo', 'mount', device.device_node, mount_point], check=True)
        return mount_point
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while trying to mount the device: {e}")
        return None

# Function to unmount a USB device
def unmount_usb(mount_point):
    try:
        subprocess.run(['sudo', 'umount', mount_point], check=True)
        os.rmdir(mount_point)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while trying to unmount the device: {e}")

# Function to copy ROM files from source to destination
def copy_roms(source_directory, destination_directory):
    print("Copying ROMs")
    for file in os.listdir(source_directory):
        if (file.endswith(".rom") or file.endswith(".nes") or file.endswith(".sfc") or file.endswith(".gba")) and not file.startswith("._"):  # Skip files starting with ._
            source_file = os.path.join(source_directory, file)
            destination_file = os.path.join(destination_directory, file)
            shutil.copy(source_file, destination_file)
            print(f"Copied {file} to {destination_file}")

# Function to display a startup image and play sound
def play_startup_image_and_sound(image_path, sound_path, display_time=None):
    pygame.display.set_caption("Startup")

    # Load the image
    image = pygame.image.load(image_path)
    screen = pygame.display.get_surface()
    image = pygame.transform.scale(image, (screen.get_width(), screen.get_height()))

    # Load the sound
    pygame.mixer.init()
    sound = pygame.mixer.Sound(sound_path)

    # Display the image
    pygame.mouse.set_visible(False)
    screen.blit(image, (0, 0))
    pygame.display.update()

    # Play the sound
    sound.play()

    # If display_time is specified, wait for that duration
    # Otherwise, wait for the duration of the sound
    if display_time is None:
        display_time = sound.get_length()

    time.sleep(display_time)

# Function to initialize Pygame
def initialize_pygame():
    try:
        pygame.init()  # Initialize Pygame
        pygame.joystick.init()  # Initialize joystick
        pygame.joystick.Joystick(0).init()
        pygame.display.set_mode((1920, 1080))
        pygame.font.init()

        info = pygame.display.Info()  # Get display info
        screen_width = info.current_w
        screen_height = info.current_h

        pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
        pygame.mouse.set_visible(False)  # Hide the system mouse cursor
    except Exception as e:
        print(f"Exception during initialization: {e}")

# Set environment variables for framebuffer
os.putenv('SDL_VIDEODRIVER', 'fbcon')
os.putenv('SDL_FBDEV', '/dev/fb0')
context = Context()
initialize_pygame()
play_startup_image_and_sound("./splash.jpg" , "./splash.wav", 2)
games_list = get_names_in_folder("./roms/")
context.state.render(context , games_list=games_list)
clock = pygame.time.Clock()
other_events = []
monitor_usb()

# Main event loop
while True:
    if isinstance(context.state , GameMenuState):
        for e in other_events:
            if Event.USB_DETECTED == e.event_type:  # Check for USB events
                context.handle_event(e)
                other_events.pop(0)

        pygame_events = pygame.event.get()
        for e in pygame_events:
            if e.type == pygame.JOYAXISMOTION:
                context.handle_event(Event(Event.JOYSTICK_MOVED,  games_list = games_list))  # Handle joystick movement
                break
        for e in pygame_events:
            if e.type == pygame.USEREVENT:
                context.handle_event(Event(Event.PRESSED_BUTTON , name = e.name))  # Handle button press
                break
        if isinstance(context.state , GameMenuState):
            pygame.display.flip()  # Update display
            clock.tick(60)

    if isinstance(context.state , PlayingGameState):
        # Handle events during PlayingGameState
        for e in other_events:
            context.handle_event(e)
            other_events.pop(0)
