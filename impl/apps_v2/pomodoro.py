from InputStatus import InputStatusEnum
import time
from datetime import timedelta, datetime
from PIL import Image, ImageFont, ImageDraw

class PomodoroScreen:
    def __init__(self, config, modules, default_actions):
        self.modules = modules
        self.default_actions = default_actions
        
        self.active = False
        self.font = ImageFont.truetype("fonts/tiny.otf", 5)
        self.canvas_width = config.getint('System', 'canvas_width', fallback=64)
        self.canvas_height = config.getint('System', 'canvas_height', fallback=32)

        self.work_duration = timedelta(minutes = 25)
        self.short_duration = timedelta(minutes = 5)
        self.long_duration = timedelta(minutes = 15)
        self.cycle_order = "WSWSWL"
        self.cycle_idx = 0
        self.status = ''

        self.time_left = None
        self.last_update_time = None

    def generate(self, isHorizontal, inputStatus):
        if (inputStatus is InputStatusEnum.SINGLE_PRESS):
            self.active = not self.active
            self.last_update_time = time.time()
            if self.active and self.time_left is None:
                status = self.cycle_order[self.cycle_idx]
                if status == 'W':
                    self.status = "W"
                    self.time_left = self.work_duration
                elif status == 'S':
                    self.status = "S"
                    self.time_left = self.short_duration
                elif status == 'L':
                    self.status = "L"
                    self.time_left = self.long_duration
                self.cycle_idx += 1
                if self.cycle_idx >= len(self.cycle_order):
                    self.cycle_idx = 0
        elif (inputStatus is InputStatusEnum.ENCODER_INCREASE):
            self.default_actions['switch_next_app']()
        elif (inputStatus is InputStatusEnum.ENCODER_DECREASE):
            self.default_actions['switch_prev_app']()
        
        if self.active:
            self.time_left = self.time_left - timedelta(seconds = (time.time() - self.last_update_time))
            self.last_update_time = time.time()

            if self.time_left <= timedelta(seconds=0):
                print("time is up")
                self.active = False
                self.time_left = None
                self.last_update_time = None

        # if isHorizontal:
        #     frame = Image.new("RGB", (self.canvas_width, self.canvas_height), (0,0,0))
        #     draw = ImageDraw.Draw(frame)

        #     if self.time_left is not None:
        #         minutes, seconds = divmod(self.time_left.total_seconds(), 60)
        #         time_str = str(int(round(minutes))) + "m " + str(int(round(seconds))) + "s"
        #         draw.text((0,0), time_str, (255,255,255), font=self.font)
                
        #         if self.status != '':
        #             draw.text((0,7), self.status, (255,255,255), font=self.font)
        #     else:
        #         if self.status != '':
        #             draw.text((0,7), self.status + " is Over", (255,255,255), font=self.font)
        # else:
        bg_color = (255,126,109)
        if self.status == "W":
            bg_color = (255,126,109)
        elif self.status == "S":
            bg_color = (142,202,255)
        elif self.status == "L":
            bg_color = (43,156,255)

        frame = Image.new("RGB", (self.canvas_height, self.canvas_width), bg_color)
        draw = ImageDraw.Draw(frame)

        if self.status != '':
            if self.status == "W":
                draw.text((1,7), 'Work', (255,255,255), font=self.font)
            elif self.status == "S":
                draw.text((1,7), 'Short', (255,255,255), font=self.font)
                draw.text((1,13), 'Break', (255,255,255), font=self.font)
            elif self.status == "L":
                draw.text((1,7), 'Long', (255,255,255), font=self.font)
                draw.text((1,13), 'Break', (255,255,255), font=self.font)

            if self.time_left is None:
                y_loc = 19
                if self.status == "W":
                    y_loc = 13
                draw.text((1, y_loc), "Is Over", (255,255,255), font=self.font)
            else:
                minutes, seconds = divmod(self.time_left.total_seconds(), 60)
                time_str = str(int(round(minutes))) + "m " + str(int(round(seconds))) + "s"
                draw.text((1,1), time_str, (255,255,255), font=self.font)
        else:
            draw.text((0,10), "POMODORO", (255,255,255), font=self.font)
            draw.text((7,26), "PRESS", (255,255,255), font=self.font)
            draw.text((13,32), "TO", (255,255,255), font=self.font)
            draw.text((7,38), "START", (255,255,255), font=self.font)

        frame = frame.rotate(90, expand=True)


        return frame

            
