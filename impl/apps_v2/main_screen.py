from InputStatus import InputStatusEnum
from PIL import Image, ImageFont, ImageDraw
from datetime import datetime
from dateutil import tz
import time
import threading

from apps_v2 import pomodoro

light_pink = (255,219,218)
dark_pink = (219,127,142)
white = (230,255,255)

salmon = (255,150,162)
tan = (255,205,178)
orange_tinted_white = (248,237,235)

washed_out_navy = (109,104,117)

discordColor = (150,170,255)
messengerColor = (60, 220, 255)
snapchatColor = (255, 252, 0)
smsColor = (110, 255, 140)

spotify_color = (0,255,0)

class MainScreen:
    def __init__(self, config, modules, default_actions):
        self.font = ImageFont.truetype("fonts/tiny.otf", 5)
        self.modules = modules
        self.default_actions = default_actions

        self.canvas_width = config.getint('System', 'canvas_width', fallback=64)
        self.canvas_height = config.getint('System', 'canvas_height', fallback=32)
        self.cycle_time = config.getint('Main Screen', 'cycle_time', fallback=20)
        self.use_24_hour = config.getboolean('Main Screen', 'use_24_hour', fallback=False)

        self.vertical = pomodoro.PomodoroScreen(config, modules, default_actions)

        self.lastGenerateCall = None
        self.on_cycle = True

        self.bgs = {'sakura' : Image.open('apps_v2/res/main_screen/sakura-bg.png').convert("RGB"),
                    'cloud' : Image.open('apps_v2/res/main_screen/cloud-bg-clear.png').convert("RGBA"),
                    'forest' : Image.open('apps_v2/res/main_screen/forest-bg.png').convert("RGB")}
        self.theme_list = [self.generateSakura, self.generateCloud, self.generateForest]

        self.currentIdx = 0
        self.selectMode = False

        self.old_noti_list = []
        self.queued_frames = []
    
    def generate(self, isHorizontal, inputStatus):
        if not isHorizontal:
            return self.vertical.generate(isHorizontal, inputStatus)
        
        if (inputStatus == InputStatusEnum.LONG_PRESS):
            self.selectMode = not self.selectMode

        if self.selectMode:
            if (inputStatus is InputStatusEnum.ENCODER_INCREASE):
                self.currentIdx += 1
                self.queued_frames = []
            elif (inputStatus is InputStatusEnum.ENCODER_DECREASE):
                self.currentIdx -= 1
                self.queued_frames = []
        else:
            if (inputStatus is InputStatusEnum.SINGLE_PRESS):
                self.default_actions['toggle_display']()
            elif (inputStatus is InputStatusEnum.ENCODER_INCREASE):
                self.default_actions['switch_next_app']()
            elif (inputStatus is InputStatusEnum.ENCODER_DECREASE):
                self.default_actions['switch_prev_app']()

        if (self.lastGenerateCall == None):
            self.lastGenerateCall = time.time()
        if (time.time() - self.lastGenerateCall >= self.cycle_time):
            self.on_cycle = not self.on_cycle
            self.lastGenerateCall = time.time()

        frame = self.theme_list[self.currentIdx % len(self.theme_list)]()
        
        if (self.selectMode):
            draw = ImageDraw.Draw(frame)
            draw.rectangle((0,0,self.canvas_width-1,self.canvas_height-1), outline=white)
        
        return frame
    
    def generateSakura(self):
        currentTime = datetime.now(tz=tz.tzlocal())
        month = currentTime.month
        day = currentTime.day
        dayOfWeek = currentTime.weekday() + 1
        hours = currentTime.hour
        if not self.use_24_hour:
            hours = hours % 12
            if (hours == 0):
                hours += 12 
        minutes = currentTime.minute

        frame = self.bgs['sakura'].copy()
        draw = ImageDraw.Draw(frame)

        draw.text((3, 6), padToTwoDigit(hours), light_pink, font=self.font)
        draw.text((10, 6), ":", light_pink, font=self.font)
        draw.text((13, 6), padToTwoDigit(minutes), light_pink, font=self.font)
        
        if (self.on_cycle):
            #date
            draw.text((23, 6), padToTwoDigit(month), dark_pink, font=self.font)
            draw.text((30, 6), ".", dark_pink, font=self.font)
            draw.text((33, 6), padToTwoDigit(day), dark_pink, font=self.font)
        else:
            #dayOfWeek
            draw.text((23, 6), padToTwoDigit(dayOfWeek), dark_pink, font=self.font)
            #weather
            weather = self.modules['weather']
            one_call = weather.getWeather()
            if (one_call != None):
                curr_temp = round(one_call.current.temperature('fahrenheit')['temp'])
                draw.text((33, 6), padToTwoDigit(curr_temp), white, font=self.font)
                draw.point((41,6), fill=white)
        
        #notifications
        noti_list = self.modules['notifications'].getNotificationList()
        counts = countList(noti_list)

        if (counts['Discord'] > 0):
            draw.rectangle((37,26,38,27), fill=discordColor)
        if (counts['SMS'] > 0):
            draw.rectangle((34,26,35,27), fill=smsColor)
        if (counts['Snapchat'] > 0):
            draw.rectangle((34,29,35,30), fill=snapchatColor)
        if (counts['Messenger'] > 0):
            draw.rectangle((37,29,38,30), fill=messengerColor)
        
        self.old_noti_list = noti_list
        
        return frame
    
    def generateCloud(self):
        currentTime = datetime.now(tz=tz.tzlocal())
        month = currentTime.month
        day = currentTime.day
        hours = currentTime.hour
        if not self.use_24_hour:
            hours = hours % 12
            if (hours == 0):
                hours += 12 
        minutes = currentTime.minute
        seconds = currentTime.second

        noti_list = self.modules['notifications'].getNotificationList()

        threading.Thread(target=generateNotiFramesAsync, 
            args=(self.queued_frames, noti_list, self.old_noti_list.copy(), self.font, self.canvas_width, self.canvas_height)).start()
        
        self.old_noti_list = noti_list.copy()

        if len(self.queued_frames) == 0:
            frame = Image.new('RGBA',(self.canvas_width, self.canvas_height),washed_out_navy)
        else:
            frame = self.queued_frames.pop(0)
        draw = ImageDraw.Draw(frame)

        frame.paste(self.bgs['cloud'], (0,0), self.bgs['cloud'])

        time_x_off = 2
        time_y_off = 25
        draw.text((time_x_off, time_y_off), padToTwoDigit(hours), orange_tinted_white, font=self.font)
        draw.text((time_x_off+7, time_y_off), ":", orange_tinted_white, font=self.font)
        draw.text((time_x_off+10, time_y_off), padToTwoDigit(minutes), orange_tinted_white, font=self.font)
        draw.text((time_x_off+17, time_y_off), ":", orange_tinted_white, font=self.font)
        draw.text((time_x_off+20, time_y_off), padToTwoDigit(seconds), orange_tinted_white, font=self.font)

        date_x_off = 45
        date_y_off = 25
        draw.text((date_x_off, date_y_off), padToTwoDigit(month), orange_tinted_white, font=self.font)
        draw.text((date_x_off+7, date_y_off), ".", orange_tinted_white, font=self.font)
        draw.text((date_x_off+10, date_y_off), padToTwoDigit(day), orange_tinted_white, font=self.font)

        return frame.convert("RGB")

    def generateForest(self):
        frame = self.bgs['forest'].copy()
        return frame


def padToTwoDigit(num):
    if num < 10:
        return "0" + str(num)
    else:
        return str(num)

def countList(noti_list):
    counts = {'Discord':0, 'SMS':0, 'Snapchat':0, 'Messenger':0}
    for noti in noti_list:
        if noti.application in counts.keys():
            counts[noti.application] = counts[noti.application] + 1
    return counts

def generateNotiFramesAsync(queue, noti_list, old_noti_list, font, canvas_width, canvas_height):
    for noti in noti_list:
        found = False
        for old_noti in old_noti_list:
            if noti.noti_id == old_noti.noti_id:
                found = True
        if not found:
            color = (0,0,0)
            if noti.application == 'Discord':
                color = discordColor
            elif noti.application == 'SMS':
                color = smsColor
            elif noti.application == 'Snapchat':
                color = snapchatColor
            elif noti.application == 'Messenger':
                color = messengerColor

            for _ in range(3):
                queue.append(Image.new('RGB', (canvas_width, canvas_height), color))
                queue.append(Image.new('RGB', (canvas_width, canvas_height), color))
                queue.append(Image.new('RGB', (canvas_width, canvas_height), (0,0,0)))
                queue.append(Image.new('RGB', (canvas_width, canvas_height), (0,0,0)))

            noti_str = noti.application + " | Title: " + noti.title + " | Body: " + noti.body
            noti_len = font.getsize(noti_str)[0]

            for i in range(noti_len+canvas_width):
                noti_frame = Image.new('RGB', (canvas_width, canvas_height), color)
                noti_draw = ImageDraw.Draw(noti_frame)
                noti_draw.text((canvas_width-i,1), noti_str, orange_tinted_white, font)
                queue.append(noti_frame)

            for _ in range(3):
                queue.append(Image.new('RGB', (canvas_width, canvas_height), color))
                queue.append(Image.new('RGB', (canvas_width, canvas_height), color))
                queue.append(Image.new('RGB', (canvas_width, canvas_height), (0,0,0)))
                queue.append(Image.new('RGB', (canvas_width, canvas_height), (0,0,0)))