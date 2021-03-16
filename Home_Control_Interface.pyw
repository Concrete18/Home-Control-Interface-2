from tkinter import Tk, Button, Label, LabelFrame, messagebox
import tkinter as tk
from pyHS100 import SmartPlug
from pyHS100 import Discover  # unused normally
import PySimpleGUIWx as sg
from phue import Bridge
from time import sleep
from ahk import AHK
import subprocess
import threading
import socket
import psutil
import time
import sys
import os


class Home:

    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # settings
    debug = 0

    # defaults
    icon = 'bulb.ico'
    window_title = 'Home Control Interface'
    window_state = 0

    # device init
    Hue_Hub = Bridge('192.168.0.134')
    Heater = SmartPlug('192.168.0.146')
    Lighthouse = SmartPlug('192.168.0.197')
    ras_pi = '192.168.0.114'
    heater_plugged_in = 1
    lighthouse_plugged_in = 1
    check_pi_status = 1

    # ahk
    ahk = AHK(executable_path='C:/Program Files/AutoHotkey/AutoHotkey.exe')

    # python scripts
    switch_to_abc = "D:/Google Drive/Coding/Python/Scripts/1-Complete-Projects/Roku-Control/Instant_Set_to_ABC.py"
    timed_shutdown = "D:/Google Drive/Coding/Python/Scripts/1-Complete-Projects/Timed-Shutdown/Timed_Shutdown.pyw"

    # Status vars
    computer_status_interval = 1  # interval in seconds
    rpi_status = 'Checking Status'
    boot_time = psutil.boot_time()

    Tray = sg.SystemTray(
        menu=['menu',[
        'Lights On',
        'Lights Off',
        'Backlight Scene',
        'Heater Toggle',
        'Exit'
        ]],
        filename=icon,
        tooltip=window_title)


    @classmethod
    def update_tray(cls):
        event = cls.Tray.Read()
        if event == 'Exit':
            exit()
        elif event == 'Lights On':
            cls.Hue_Hub.run_scene('My Bedroom', 'Normal', 1)
        elif event == 'Lights Off':
            cls.Hue_Hub.set_group('My Bedroom', 'on', False)
        elif event == 'Backlight Scene':
            cls.Hue_Hub.run_scene('My Bedroom', 'Backlight', 1)
        elif event == 'Heater Toggle':
            cls.smart_plug_toggle(cls.Heater)
        elif event == '__ACTIVATED__':
            cls.create_window()
        cls.Home_Interface.after(0, cls.update_tray)


    @staticmethod
    def readable_time_since(seconds):
        '''
        Returns time since based on seconds argument in the unit of time that makes the most sense
        rounded to 1 decimal place.
        '''
        if seconds < (60 * 60):  # seconds in minute * minutes in hour
            minutes = round(seconds / 60, 1)  # seconds in a minute
            return f'{minutes} minutes'
        elif seconds < (60 * 60 * 24):  # seconds in minute * minutes in hour * hours in a day
            hours = round(seconds / (60 * 60), 1)  # seconds in minute * minutes in hour
            return f'{hours} hours'
        else:
            days = round(seconds / 86400, 1)  # seconds in minute * minutes in hour * hours in a day
            return f'{days} days'


    @classmethod
    def check_pi(cls):
        '''
        Checks if Pi is up.
        '''
        def callback():
            if cls.check_pi_status == 1:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex((cls.ras_pi, 22))
                if result == 0:
                    cls.rpi_status = 'Online'
                else:
                    cls.rpi_status = 'Offline'
                    messagebox.showwarning(title=cls.window_title, message=f'Raspberry Pi is not online.')
        pi_thread = threading.Thread(target=callback)
        pi_thread.start()


    @classmethod
    def check_computer_status(cls):
        mem = psutil.virtual_memory()
        virt_mem = f'{round(mem.used/1024/1024/1024, 1)}/{round(mem.total/1024/1024/1024, 1)}'
        cls.uptime.set(cls.readable_time_since(int(time.time() - cls.boot_time)))
        cls.cpu_util.set(f'{psutil.cpu_percent(interval=0.1)}%')
        cls.virt_mem.set(f'{virt_mem} GB')
        cls.Home_Interface.after(cls.computer_status_interval*1000, cls.check_computer_status)


    @staticmethod
    def smart_plug_toggle(device, name='device', button=0):
        '''
        Smart Plug toggle function.
        '''
        try:
            if device.get_sysinfo()["relay_state"] == 0:
                device.turn_on()
                if button != 0:
                    button.config(relief='sunken')  # On State
            else:
                device.turn_off()
                if button != 0:
                    button.config(relief='raised')  # Off State
        except Exception as error:
            print(f'Error toggling device\n{error}\n{name}')


    @classmethod
    def start_vr(cls):
        '''
        Runs SteamVR shortcut and turns on lighthouse plugged into smart plug for tracking if it is off.
        '''
        cls.Hue_Hub.run_scene('My Bedroom', 'Normal', 1)
        if cls.lighthouse_plugged_in and cls.Lighthouse.get_sysinfo()["relay_state"] == 0:
            cls.Lighthouse.turn_on()
            cls.LighthouseButton.config(relief='sunken')
        steamvr_path = "D:/My Installed Games/Steam Games/steamapps/common/SteamVR/bin/win64/vrstartup.exe"
        if os.path.isfile(steamvr_path):
            subprocess.call(steamvr_path)


    @classmethod
    def set_sound_device(cls, device):
        '''
        Set Sound Device Function. Requires AHK and NirCMD to work.
        '''
        cls.ahk.run_script(f'Run nircmd setdefaultsounddevice "{device}" 1', blocking=False)


    @classmethod
    def display_switch(cls, mode):
        '''
        Switches display to the mode entered as an argument. Works for PC and TV mode.
        '''
        def callback(mode):
            subprocess.call([f'{cls.script_dir}/Batches/{mode} Mode.bat'])
            sleep(10)
            if mode == 'PC':
                cls.set_sound_device('Logitech Speakers')
            else:
                cls.display_switch('SONY TV')
            print(f'{mode} Mode Set')
        Switch = threading.Thread(target=callback, args=(mode,))
        Switch.start()


    @staticmethod
    def python_script_runner(script):
        '''
        Runs script using full path after changing the working directory in case of relative paths in script.
        '''
        subprocess.run([sys.executable, script], cwd=os.path.dirname(script))


    @classmethod
    def create_window(cls):
        '''
        Creates Home Control Interface.
        '''
        cls.Home_Interface = Tk()
        cls.uptime = tk.StringVar()
        cls.cpu_util = tk.StringVar()
        cls.cpu_util.set('Checking')
        cls.virt_mem = tk.StringVar()
        cls.virt_mem.set('Checking')
        cls.pi_status = tk.StringVar()
        cls.pi_status.set(cls.rpi_status)
        window_height = 724
        window_width = 1108
        height = int((cls.Home_Interface.winfo_screenheight()-window_height)/2)
        width = int((cls.Home_Interface.winfo_screenwidth()-window_width)/2)
        cls.Home_Interface.geometry(f'+{width}+{height}')
        # cls.Home_Interface.geometry(f'{window_width}x{window_height}+{width}+{height}')
        cls.Home_Interface.title(cls.window_title)
        cls.Home_Interface.iconbitmap(cls.Home_Interface, cls.icon)
        cls.Home_Interface.configure(bg='white')
        cls.Home_Interface.resizable(width=False, height=False)

        # default values for interface
        background = 'white'
        bold_base_font = ('Arial Bold', 20)
        small_bold_base_font = ('Arial Bold', 16)
        small_base_font = ('Arial', 15)
        pad_x = 10
        pad_y = 10

        # Frames
        # Left Frames
        ComputerStatus = LabelFrame(cls.Home_Interface, text='Computer Status', bg=background,
            font=bold_base_font, padx=pad_x, pady=pad_y, width=300, height=150)
        ComputerStatus.grid(column=0, row=0, padx=pad_x, pady=pad_y, sticky='nsew')

        HueLightControlFrame = LabelFrame(cls.Home_Interface, text='Hue Light Control', bg=background,
            font=bold_base_font, padx=pad_x, pady=pad_y, width=300, height=400)
        HueLightControlFrame.grid(column=0, row=1, rowspan=2, padx=pad_x, pady=pad_y, sticky='nsew')

        Script_Shortcuts = LabelFrame(cls.Home_Interface, text='Script Shortcuts', bg=background, font=bold_base_font,
            padx=pad_x, pady=pad_y, width=300, height=200)
        Script_Shortcuts.grid(column=0, row=3, padx=pad_x, pady=pad_y, sticky='nsew')

        # Right Frames
        SmartPlugControlFrame = LabelFrame(cls.Home_Interface, text='Smart Plug Control', bg=background,
            font=bold_base_font, padx=pad_x, pady=pad_y, width=300, height=150)
        SmartPlugControlFrame.grid(column=1, row=0, padx=pad_x, pady=pad_y, sticky='nsew')

        AudioSettingsFrame = LabelFrame(cls.Home_Interface, text='Audio Settings', bg=background, font=bold_base_font,
            padx=pad_x, pady=pad_y, width=300, height=390)
        AudioSettingsFrame.grid(column=1, row=1, padx=pad_x, pady=pad_y, sticky='nsew')

        ProjectionFrame = LabelFrame(cls.Home_Interface, text='Projection', bg=background, font=bold_base_font,
            padx=pad_x, pady=pad_y, width=300, height=400)
        ProjectionFrame.grid(column=1, row=2, padx=pad_x, pady=pad_y, sticky='nsew')

        VRFrame = LabelFrame(cls.Home_Interface, text='VR Settings', bg=background, font=bold_base_font,
            padx=pad_x, pady=pad_y, width=300, height=400)
        VRFrame.grid(column=1, row=3, padx=pad_x, pady=pad_x, sticky='nsew')

        # Labels
        ci_padx = 13
        cls.ComputerInfo = Label(ComputerStatus, text='PC Uptime', bg=background, font=small_bold_base_font)
        cls.ComputerInfo.grid(column=0, row=0, padx=ci_padx)
        cls.ComputerInfo = Label(ComputerStatus, textvariable=cls.uptime, bg=background, font=small_base_font)
        cls.ComputerInfo.grid(column=0, row=1)

        cls.ComputerInfo = Label(ComputerStatus, text='CPU Util', bg=background, font=small_bold_base_font)
        cls.ComputerInfo.grid(column=1, row=0, padx=ci_padx)
        cls.ComputerInfo = Label(ComputerStatus, textvariable=cls.cpu_util, bg=background, font=small_base_font)
        cls.ComputerInfo.grid(column=1, row=1)

        cls.ComputerInfo = Label(ComputerStatus, text='Memory', bg=background, font=small_bold_base_font)
        cls.ComputerInfo.grid(column=2, row=0, padx=ci_padx)
        cls.ComputerInfo = Label(ComputerStatus, textvariable=cls.virt_mem, bg=background, font=small_base_font)
        cls.ComputerInfo.grid(column=2, row=1)

        cls.ComputerInfo = Label(ComputerStatus, text='Rasberry Pi', bg=background, font=small_bold_base_font)
        cls.ComputerInfo.grid(column=3, row=0, padx=ci_padx)
        cls.ComputerInfo = Label(ComputerStatus, textvariable=cls.pi_status, bg=background, font=small_base_font)
        cls.ComputerInfo.grid(column=3, row=1)

        # Buttons
        LightsOn = Button(HueLightControlFrame, text="Lights On",
            command=lambda: cls.Hue_Hub.run_scene('My Bedroom', 'Normal', 1), font=("Arial", 19), width=15)
        LightsOn.grid(column=0, row=1, padx=pad_x, pady=pad_y)

        TurnAllOff = Button(HueLightControlFrame, text="Lights Off",
            command=lambda: cls.Hue_Hub.set_group('My Bedroom', 'on', False), font=("Arial", 19), width=15)
        TurnAllOff.grid(column=1, row=1, padx=pad_x, pady=pad_y)

        BackLight = Button(HueLightControlFrame, text="BackLight Mode",
            command=lambda: cls.Hue_Hub.run_scene('My Bedroom', 'Backlight', 1), font=("Arial", 19), width=15)
        BackLight.grid(column=0, row=2, padx=pad_x, pady=pad_y)

        DimmedMode = Button(HueLightControlFrame, text="Dimmed Mode",
            command=lambda: cls.Hue_Hub.run_scene('My Bedroom', 'Dimmed', 1), font=("Arial", 19), width=15)
        DimmedMode.grid(column=1, row=2, padx=pad_x, pady=pad_y)

        Nightlight = Button(HueLightControlFrame, text="Night Light",
            command=lambda: cls.Hue_Hub.run_scene('My Bedroom', 'Night light', 1), font=("Arial", 19), width=15)
        Nightlight.grid(column=0, row=3, padx=pad_x, pady=pad_y)

        cls.HeaterButton = Button(SmartPlugControlFrame, text="Heater Toggle", font=("Arial", 19), width=15,
            command=lambda: cls.smart_plug_toggle(name='Heater', device=cls.Heater, button=cls.HeaterButton),
            state='disabled')
        cls.HeaterButton.grid(column=0, row=5, padx=pad_x, pady=pad_y)

        UnsetButton = Button(SmartPlugControlFrame, text="Unset", state='disabled',
            command='ph', font=("Arial", 19), width=15)
        UnsetButton.grid(column=1, row=5, padx=pad_x, pady=pad_y)

        RokuButton = Button(Script_Shortcuts, text="Set Roku to ABC",
            command=lambda: cls.python_script_runner(cls.switch_to_abc), font=("Arial", 19), width=15)
        RokuButton.grid(column=0, row=0, padx=pad_x, pady=pad_y)

        TimerControl = Button(Script_Shortcuts, text="Power Control",
            command=lambda: cls.python_script_runner(cls.timed_shutdown), font=("Arial", 19), width=15)
        TimerControl.grid(column=1, row=0, padx=pad_x, pady=pad_y)

        current_pc = socket.gethostname()
        if current_pc == 'Aperture-Two':
            StartVRButton = Button(VRFrame, text="Start VR",
                command=cls.start_vr, font=("Arial", 19), width=15)
            StartVRButton.grid(column=0, row=9, padx=pad_x, pady=pad_y)

            cls.LighthouseButton = Button(VRFrame, text="Lighthouse Toggle", state='disabled', font=("Arial", 19),
                command=lambda: cls.smart_plug_toggle(name='Lighthouse', device=cls.Lighthouse,
                button=cls.LighthouseButton), width=15)
            cls.LighthouseButton.grid(column=1, row=9, padx=pad_x, pady=pad_y)

            AudioToSpeakers = Button(AudioSettingsFrame, text="Speaker Audio",
                command=lambda: cls.set_sound_device('Logitech Speakers'), font=("Arial", 19), width=15)
            AudioToSpeakers.grid(column=0, row=7, padx=pad_x, pady=pad_y)

            AudioToHeadphones = Button(AudioSettingsFrame, text="Headphone Audio",
                command=lambda: cls.set_sound_device('Headphones'), font=("Arial", 19),width=15)
            AudioToHeadphones.grid(column=1, row=7, padx=pad_x, pady=pad_y)

            SwitchToPCMode = Button(ProjectionFrame, text="PC Mode", command=lambda: cls.display_switch('PC'),
                font=("Arial", 19), width=15)
            SwitchToPCMode.grid(column=0, row=9, padx=pad_x, pady=pad_y)

            SwitchToTVMode = Button(ProjectionFrame, text="TV Mode", command=lambda: cls.display_switch('SONY TV'),
                font=("Arial", 19), width=15)
            SwitchToTVMode.grid(column=1, row=9, padx=pad_x, pady=pad_y)
        elif current_pc == 'Surface-1':
            AudioToSpeakers = Button(AudioSettingsFrame, text="Speaker Audio",
                command=lambda: cls.set_sound_device('Speakers'), font=("Arial", 19), width=15)
            AudioToSpeakers.grid(column=0, row=7, padx=pad_x, pady=pad_y)

            AudioToHeadphones = Button(AudioSettingsFrame, text="Headphone Audio",
                command=lambda: cls.set_sound_device('Aux'), font=("Arial", 19),width=15)
            AudioToHeadphones.grid(column=1, row=7, padx=pad_x, pady=pad_y)
        else:
            messagebox.showwarning(title=cls.window_title, message='Current PC is unknown.')

        #  Smart Plugs running through state check function.
        # cls.update_tray()
        cls.plug_state_check()
        cls.check_computer_status()

        # TODO Fix incorrect height
        if cls.debug:
            cls.Home_Interface.update()
            print(cls.Home_Interface.winfo_width())
            print(cls.Home_Interface.winfo_height())

        cls.Home_Interface.mainloop()


    @classmethod
    def plug_state_check(cls):
        '''
        Gets current state of entered device and updates button relief.
        '''
        def callback():
            buttons = {}
            if cls.lighthouse_plugged_in:
                buttons[cls.Lighthouse] = cls.LighthouseButton
                cls.LighthouseButton.config(state='normal')
            if cls.heater_plugged_in:
                buttons[cls.Heater] = cls.HeaterButton
                cls.HeaterButton.config(state='normal')
            for device, button in buttons.items():
                try:
                    if device.get_sysinfo()["relay_state"] == 1:
                        button.config(relief='sunken')  # On State
                    else:
                        button.config(relief='raised')  # Off State
                except Exception as e:
                    print('Smart Plug', e)
                    messagebox.showwarning(title=cls.window_title, message=f'Error communicating with {device}.')
        pi_thread = threading.Thread(target=callback, daemon=True)
        pi_thread.start()


    @classmethod
    def create_tray(cls):
        '''
        Creates the system tray. Clicking the Lightbulb ones the interface and right clicking it shows quick
        lighting control options.
        '''
        # TODO fix issue where tray does not work when interface is open
        # TODO open/close window when icon pressed
        print('Tray Created')
        while True:
            event = cls.Tray.Read()
            if event == 'Exit':
                exit()
            elif event == 'Lights On':
                cls.Hue_Hub.run_scene('My Bedroom', 'Normal', 1)
            elif event == 'Lights Off':
                cls.Hue_Hub.set_group('My Bedroom', 'on', False)
            elif event == 'Backlight Scene':
                cls.Hue_Hub.run_scene('My Bedroom', 'Backlight', 1)
            elif event == 'Heater Toggle':
                cls.smart_plug_toggle(cls.Heater)
            elif event == '__ACTIVATED__':
                cls.create_window()


if __name__ == "__main__":
    Home.check_pi()
    Home.create_tray()
