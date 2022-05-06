import time
import urllib.request
import json
from PIL import Image, ImageFont, ImageDraw
import threading
import numpy as np
from InputStatus import InputStatusEnum
from queue import LifoQueue
from ast import literal_eval

class SubcountScreen:
    def __init__(self, config, modules, default_actions):
        self.modules = modules
        self.default_actions = default_actions
        self.bg = Image.open('apps_v2/res/pixel_logo_flipped.png').convert('RGB')
        self.font = ImageFont.truetype("fonts/tiny.otf", 5)
        self.queue = LifoQueue()

        self.canvas_width = config.getint('System', 'canvas_width', fallback=64)
        self.canvas_height = config.getint('System', 'canvas_height', fallback=32)
        self.subs = 0

        self.name_color = literal_eval(config.get('Youtube', 'name_color',fallback="(255,255,255)"))
        self.sub_color = literal_eval(config.get('Youtube', 'sub_color',fallback="(255,255,255)"))

        yt_token = config.get("Youtube", "key", fallback=None)
        if yt_token is None:
            print("[Subcount] Youtube token is not specified in config")
        else:
            self.channel_id = config.get('Youtube', 'channel_id', fallback = None)
            if self.channel_id is None:
                print("[Subcount] Youtube channel id is not specified in config")
            else:
                self.display_name = config.get('Youtube', 'display_name', fallback=self.channel_id)
            threading.Thread(target=fetchYoutubeSubsAsync, args=(self.queue, yt_token, self.channel_id)).start()
    
    def generate(self, isHorizontal, inputStatus):
        if (not self.queue.empty()):
            self.subs = self.queue.get()
            self.queue.queue.clear()

        if (inputStatus is InputStatusEnum.SINGLE_PRESS):
            self.default_actions['toggle_display']()
        elif (inputStatus is InputStatusEnum.ENCODER_INCREASE):
            self.default_actions['switch_next_app']()
        elif (inputStatus is InputStatusEnum.ENCODER_DECREASE):
            self.default_actions['switch_prev_app']()

        frame = self.bg.copy()
        draw = ImageDraw.Draw(frame)
        if self.display_name == "bit of a ch.allen.ge":
            draw.text((0, 11), "BIT OF A", self.name_color, font=self.font)
            draw.text((0, 18), "CH.ALLEN.GE", self.name_color, font=self.font)
        else:
            draw.text((0, 18), self.display_name.upper(), self.name_color, font=self.font)
        draw.text((0, 25), self.subs + " SUBS", self.sub_color, font=self.font)

        return frame

def fetchYoutubeSubsAsync(queue, key, channel_id):
    while True:
        data = urllib.request.urlopen("https://www.googleapis.com/youtube/v3/channels?part=statistics&id="+channel_id+"&key="+key).read()
        subs = json.loads(data)["items"][0]["statistics"]["subscriberCount"]
        queue.put(subs)
        time.sleep(60)
