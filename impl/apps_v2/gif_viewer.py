import numpy as np
from InputStatus import InputStatusEnum
from PIL import Image, ImageSequence, ImageDraw
import time
import os

white = (230,255,255)

class GifScreen:
    def __init__(self, config, modules, default_actions):
        #save the numpy arrays to avoid conversion all the time
        self.canvas_width = config.getint('System', 'canvas_width', fallback=64)
        self.canvas_height = config.getint('System', 'canvas_height', fallback=32)

        location = config.get('Gif Viewer', 'location', fallback=None)
        if location is None:
            print("[Gif Viewer] Location of gifs is not specified in config")
            self.animations = []
        else:
            self.animations = loadAnimations(location)

        self.currentIdx = 0
        self.selectMode = False

        self.modules = modules
        self.default_actions = default_actions
        self.cnt = 0
        self.was_horizontal = True
    
    def generate(self, isHorizontal, inputStatus):
        if (inputStatus == InputStatusEnum.LONG_PRESS):
            self.selectMode = not self.selectMode
        
        if self.selectMode:
            if (inputStatus is InputStatusEnum.ENCODER_INCREASE):
                self.currentIdx += 1
                self.cnt = 0
            elif (inputStatus is InputStatusEnum.ENCODER_DECREASE):
                self.currentIdx -= 1
                self.cnt = 0
        else:
            if (inputStatus is InputStatusEnum.SINGLE_PRESS):
                self.default_actions['toggle_display']()
            elif (inputStatus is InputStatusEnum.ENCODER_INCREASE):
                self.default_actions['switch_next_app']()
            elif (inputStatus is InputStatusEnum.ENCODER_DECREASE):
                self.default_actions['switch_prev_app']()
        
        curr_gif = ImageSequence.Iterator(self.animations[self.currentIdx % len(self.animations)])
        try:
            frame = curr_gif[self.cnt].convert('RGB')
        except IndexError:
            self.cnt = 0
            frame = curr_gif[self.cnt].convert('RGB')
        self.cnt += 1

        draw = ImageDraw.Draw(frame)

        if (self.selectMode):
            draw.rectangle((0,0,self.canvas_width-1,self.canvas_height-1), outline=white)

        time.sleep(0.04)
        return frame

def loadAnimations(location):
    print(location)
    result = []
    for filename in os.listdir(location):
        if filename.endswith(".gif"):
            result.append(Image.open(location+'/'+filename))
    return result
