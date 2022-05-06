import numpy as np
import random
from InputStatus import InputStatusEnum
from datetime import datetime, timedelta
from PIL import Image, ImageSequence, ImageDraw
import os
from scipy.signal import convolve2d

canvas_height = 32
canvas_width = 64

class GameOfLifeScreen:
    def __init__(self, config, modules, default_actions):
        self.modules = modules
        self.default_actions = default_actions
        self.color = (255,255,255)
        self.init_states = [generateRandomState,
                            lambda : fetchPattern('apps_v2/res/life_patterns/centinal'),
                            lambda : fetchPattern('apps_v2/res/life_patterns/achim_p144'),
                            lambda : fetchPattern('apps_v2/res/life_patterns/pboj_p22')]
        self.curr_state_idx = 0
        self.state = self.init_states[self.curr_state_idx]()

    def generate(self, isHorizontal, inputStatus):
        if (inputStatus is InputStatusEnum.SINGLE_PRESS or inputStatus is InputStatusEnum.LONG_PRESS):
            if (inputStatus is InputStatusEnum.LONG_PRESS):
                self.curr_state_idx = (self.curr_state_idx + 1) % len(self.init_states)
            self.state = self.init_states[self.curr_state_idx]()
            self.color = generateNewColor()
        elif (inputStatus is InputStatusEnum.ENCODER_INCREASE):
            self.default_actions['switch_next_app']()
        elif (inputStatus is InputStatusEnum.ENCODER_DECREASE):
            self.default_actions['switch_prev_app']()
        
        end_time = datetime.now() + timedelta(seconds=0.1)

        old_state = self.state
        frame = Image.new("RGB", (canvas_width, canvas_height), (0,0,0)) #np.zeros((canvas_height, canvas_width, 3), dtype=int)
        draw = ImageDraw.Draw(frame)

        new_state = life_step_2(old_state)
        for i in range(canvas_height):
            for j in range(canvas_width):
                if new_state[i][j] == 1:
                    draw.point((j,i), fill = self.color)
                    #frame[i][j] = self.color

        self.state = new_state

        while datetime.now() < end_time:
            pass

        return frame

def life_step_2(X):
    """Game of life step using scipy tools"""
    nbrs_count = convolve2d(X, np.ones((3, 3)), mode='same', boundary='wrap') - X
    return (nbrs_count == 3) | (X & (nbrs_count == 2))

def getNumNeighbors(state, i, j):
    num_on = 0
    adjusted_i = i+1 if i+1 < canvas_height else 0
    adjusted_j = j+1 if j+1 < canvas_width else 0
    
    if state[i-1][j-1] == 1:
        num_on += 1
    if state[i-1][j] == 1:
        num_on += 1
    if state[i-1][adjusted_j] == 1:
        num_on += 1
    if state[i][j-1] == 1:
        num_on += 1
    if state[i][adjusted_j] == 1:
        num_on += 1
    if state[adjusted_i][j-1] == 1:
        num_on += 1
    if state[adjusted_i][j] == 1:
        num_on += 1
    if state[adjusted_i][adjusted_j] == 1:
        num_on += 1
    return num_on

def generateRandomState():
    init_state = np.zeros((canvas_height, canvas_width), dtype=int)
    for i in range(canvas_height):
        for j in range(canvas_width):
            init_state[i][j] = random.randint(0,1)
    return init_state

def generateNewColor():
    return (random.randint(50,255), random.randint(50,255), random.randint(50,255))

def fetchPattern(fileLocation):
    if not os.path.exists(fileLocation + ".npy"):
        convertImage(fileLocation)
    return np.load(fileLocation + ".npy")

def convertImage(location):
    image = Image.open(location + '.png')
    width, height = image.size
    image_array = np.array(image.convert("RGB"), dtype=int)
    np.save(location + '.npy', (image_array[0:height,0:width,0]//255).astype('int32'))