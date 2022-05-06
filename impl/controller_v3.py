import queue
import sys, os, time, copy, inspect
from InputStatus import InputStatusEnum
from gpiozero import Button, RotaryEncoder
import configparser
from PIL import Image

import select

from apps_v2 import main_screen, notion_v2, subcount, gif_viewer, weather, life, spotify_player
from modules import weather_module, notification_module, spotify_module

sw = 13
enc_A = 5
enc_B = 6
tilt = 19

def main():
    brightness = 100
    displayOn = True

    config = configparser.ConfigParser()
    parsed_configs = config.read('../config.ini')
    if len(parsed_configs) == 0:
        print("no config file found")
        sys.exit()

    canvas_width = config.getint('System', 'canvas_width', fallback=64)
    canvas_height = config.getint('System', 'canvas_height', fallback=32)

    black_screen = Image.new("RGB", (canvas_width, canvas_height), (0,0,0))

    encButton = Button(sw, pull_up = True)
    inputStatusDict = {"value" : InputStatusEnum.NOTHING}
    encButton.when_pressed = lambda button : encButtonFunc(button, inputStatusDict)

    encoderQueue = queue.Queue()
    encoder = RotaryEncoder(enc_A, enc_B)
    encoder.when_rotated_clockwise = lambda enc : rotate_clockwise(enc, encoderQueue)
    encoder.when_rotated_counter_clockwise = lambda enc : rotate_counter_clockwise(enc, encoderQueue)
    encoder_state = 0

    tilt_switch = Button(tilt, pull_up = True)
    isHorizontalDict = {'value': True}
    tilt_switch.when_pressed = lambda button : tilt_callback(button, isHorizontalDict)
    tilt_switch.when_released = lambda button : tilt_callback(button, isHorizontalDict)

    def toggle_display():
        nonlocal displayOn
        displayOn = not displayOn
        print("Display On: " + str(displayOn))

    def increase_brightness():
        nonlocal brightness
        brightness = min(100, brightness + 5)

    def decrease_brightness():
        nonlocal brightness
        brightness = max(0, brightness - 5)

    current_app_idx = 0
    def switch_next_app():
        nonlocal current_app_idx
        current_app_idx += 1
    
    def switch_prev_app():
        nonlocal current_app_idx
        current_app_idx -= 1

    callbacks = {
                    'toggle_display' : toggle_display,
                    'increase_brightness' : increase_brightness,
                    'decrease_brightness' : decrease_brightness,
                    'switch_next_app' : switch_next_app,
                    'switch_prev_app' : switch_prev_app
                }
    
    modules =   {
                    'weather' : weather_module.WeatherModule(config),
                    'notifications' : notification_module.NotificationModule(config),
                    'spotify' : spotify_module.SpotifyModule(config)
                }

    app_list = [main_screen.MainScreen(config, modules, callbacks),
                notion_v2.NotionScreen(config, modules, callbacks),
                weather.WeatherScreen(config, modules, callbacks),
                subcount.SubcountScreen(config, modules, callbacks),
                gif_viewer.GifScreen(config, modules, callbacks),
                life.GameOfLifeScreen(config, modules, callbacks),
                spotify_player.SpotifyScreen(config, modules, callbacks)]

    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)
    sys.path.append(parentdir+"/rpi-rgb-led-matrix/bindings/python")
    from rgbmatrix import RGBMatrix, RGBMatrixOptions

    options = RGBMatrixOptions()
    options.rows = 32
    options.cols = 64
    options.chain_length = 1
    options.parallel = 1
    options.brightness = brightness
    options.pixel_mapper_config = "U-mapper;Rotate:180"
    options.gpio_slowdown = 1
    options.pwm_lsb_nanoseconds = 80
    options.limit_refresh_rate_hz = 150
    options.hardware_mapping = 'regular'  # If you have an Adafruit HAT: 'adafruit-hat'
    options.drop_privileges = False
    matrix = RGBMatrix(options = options)

    while(True):
        while (not encoderQueue.empty()):
            encoder_state += encoderQueue.get()
        if (encoder_state > 1):
            print("encoder increased")
            inputStatusDict['value'] = InputStatusEnum.ENCODER_INCREASE
            encoder_state = 0
        elif (encoder_state < -1):
            print("encoder decreased")
            inputStatusDict['value'] = InputStatusEnum.ENCODER_DECREASE
            encoder_state = 0

        inputStatusSnapshot = copy.copy(inputStatusDict['value'])
        inputStatusDict['value'] = InputStatusEnum.NOTHING

        isHorizontalSnapshot = copy.copy(isHorizontalDict['value'])

        while sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            cmd = sys.stdin.readline()
            if cmd:
                print("detected: " + cmd)
                if cmd == 'SP\n':
                    inputStatusSnapshot = InputStatusEnum.SINGLE_PRESS
                elif cmd == 'DP\n':
                    inputStatusSnapshot = InputStatusEnum.DOUBLE_PRESS
                elif cmd == 'TP\n':
                    inputStatusSnapshot = InputStatusEnum.TRIPLE_PRESS
                elif cmd == 'LP\n':
                    inputStatusSnapshot = InputStatusEnum.LONG_PRESS
                elif cmd == 'EI\n':
                    inputStatusSnapshot = InputStatusEnum.ENCODER_INCREASE
                elif cmd == 'ED\n':
                    inputStatusSnapshot = InputStatusEnum.ENCODER_DECREASE

        frame = app_list[current_app_idx % len(app_list)].generate(isHorizontalSnapshot, inputStatusSnapshot)
        if not displayOn:
            frame = black_screen
        
        #matrix.brightness = 100
        matrix.SetImage(frame)
        time.sleep(0.05)

def encButtonFunc(enc_button, inputStatusDict):
    start_time = time.time()
    time_diff = 0
    hold_time = 1
    
    while enc_button.is_active and (time_diff < hold_time):
        time_diff = time.time() - start_time

    if (time_diff >= hold_time):
        print("long press detected")
        inputStatusDict['value'] = InputStatusEnum.LONG_PRESS
    else:
        enc_button.when_pressed = None
        start_time = time.time()
        while (time.time() - start_time <= 0.3):
            time.sleep(0.1)
            if (enc_button.is_pressed):
                time.sleep(0.1)
                new_start_time = time.time()
                while (time.time() - new_start_time <= 0.3):
                    time.sleep(0.1)
                    if (enc_button.is_pressed):
                        print("triple press detected")
                        inputStatusDict['value'] = InputStatusEnum.TRIPLE_PRESS
                        enc_button.when_pressed = lambda button : encButtonFunc(button, inputStatusDict)
                        return
                print("double press detected")
                inputStatusDict['value'] = InputStatusEnum.DOUBLE_PRESS
                enc_button.when_pressed = lambda button : encButtonFunc(button, inputStatusDict)
                return
        print("single press detected")
        inputStatusDict['value'] = InputStatusEnum.SINGLE_PRESS
        enc_button.when_pressed = lambda button : encButtonFunc(button, inputStatusDict)
        return

def rotate_clockwise(encoder, encoderQueue):
    encoderQueue.put(1)
    encoder.value = 0

def rotate_counter_clockwise(encoder, encoderQueue):
    encoderQueue.put(-1)
    encoder.value = 0

def tilt_callback(tilt_switch, isHorizontalDict):
    startTime = time.time()
    while (time.time() - startTime < 0.25):
        pass
    isHorizontalDict['value'] = tilt_switch.is_pressed

def reduceFrameToString(frame):
    res = frame.flatten()
    return ' '.join(map(str, res))

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted with Ctrl-C')
        sys.exit(0)
