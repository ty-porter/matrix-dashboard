import numpy as np
from PIL import Image, ImageFont, ImageDraw
import requests
from io import BytesIO
from InputStatus import InputStatusEnum
from ast import literal_eval

class SpotifyScreen:
    def __init__(self, config, modules, default_actions):
        self.modules = modules
        self.default_actions = default_actions

        self.font = ImageFont.truetype("fonts/tiny.otf", 5)
        
        self.canvas_width = config.getint('System', 'canvas_width', fallback=64)
        self.canvas_height = config.getint('System', 'canvas_height', fallback=32)
        self.title_color = literal_eval(config.get('Spotify Player', 'title_color',fallback="(255,255,255)"))
        self.artist_color = literal_eval(config.get('Spotify Player', 'artist_color',fallback="(255,255,255)"))
        self.play_color = literal_eval(config.get('Spotify Player', 'play_color',fallback="(255,255,255)"))

        self.current_art_url = ''
        self.current_art_img = None
        self.current_title = ''
        self.current_artist = ''

        self.title_animation_cnt = 0
        self.artist_animation_cnt = 0

        self.is_playing = False
        self.control_mode = False
    
    def generate(self, isHorizontal, inputStatus):
        if (inputStatus is InputStatusEnum.LONG_PRESS):
            self.control_mode = not self.control_mode

        spotify_module = self.modules['spotify']
        
        if not self.control_mode:
            if (inputStatus is InputStatusEnum.SINGLE_PRESS):
                self.default_actions['toggle_display']()
                self.title_animation_cnt = 0
                self.artist_animation_cnt = 0
            elif (inputStatus is InputStatusEnum.ENCODER_INCREASE):
                self.default_actions['switch_next_app']()
            elif (inputStatus is InputStatusEnum.ENCODER_DECREASE):
                self.default_actions['switch_prev_app']()
        else:
            if (inputStatus is InputStatusEnum.SINGLE_PRESS):
                if self.is_playing:
                    spotify_module.pause_playback()
                else:
                    spotify_module.resume_playback()
            elif (inputStatus is InputStatusEnum.DOUBLE_PRESS):
                spotify_module.next_track()
            elif (inputStatus is InputStatusEnum.TRIPLE_PRESS):
                spotify_module.previous_track()
            elif (inputStatus is InputStatusEnum.ENCODER_INCREASE and self.is_playing):
                spotify_module.increase_volume()
            elif (inputStatus is InputStatusEnum.ENCODER_DECREASE and self.is_playing):
                spotify_module.decrease_volume()

        response = spotify_module.getCurrentPlayback()
        if response is not None:
            (artist,title,art_url,self.is_playing, progress_ms, duration_ms) = response

            if (self.current_title != title or self.current_artist != artist):
                self.current_artist = artist
                self.current_title = title
                self.title_animation_cnt = 0
                self.artist_animation_cnt = 0
            if self.current_art_url != art_url:
                self.current_art_url = art_url

                response = requests.get(self.current_art_url)
                img = Image.open(BytesIO(response.content))
                self.current_art_img = img.resize((self.canvas_height, self.canvas_height), resample=Image.LANCZOS)

            frame = Image.new("RGB", (self.canvas_width, self.canvas_height), (0,0,0))
            draw = ImageDraw.Draw(frame)

            draw.line((38,15,58,15), fill=(100,100,100))
            draw.line((38,15,38+round(((progress_ms / duration_ms) * 100) // 5),15), fill=(180,180,180))

            title_len = self.font.getsize(self.current_title)[0]
            if title_len > 31:
                spacer = "   "
                draw.text((34-self.title_animation_cnt, 0), self.current_title + spacer + self.current_title, self.title_color, font = self.font)
                self.title_animation_cnt += 1
                if self.title_animation_cnt == self.font.getsize(self.current_title + spacer)[0]:
                    self.title_animation_cnt = 0
            else:
                draw.text((34-self.title_animation_cnt, 0), self.current_title, self.title_color, font = self.font)

            artist_len = self.font.getsize(self.current_artist)[0]
            if artist_len > 31:
                spacer = "     "
                draw.text((34-self.artist_animation_cnt, 7), self.current_artist + spacer + self.current_artist, self.artist_color, font = self.font)
                self.artist_animation_cnt += 1
                if self.artist_animation_cnt == self.font.getsize(self.current_artist + spacer)[0]:
                    self.artist_animation_cnt = 0
            else:
                draw.text((34-self.artist_animation_cnt, 7), self.current_artist, self.artist_color, font = self.font)

            draw.rectangle((32,0,33,32), fill=(0,0,0))

            if self.current_art_img is not None:
                frame.paste(self.current_art_img, (0,0))

            drawPlayPause(draw, self.control_mode, self.is_playing, self.play_color)

            return frame
        else:
            #not active
            frame = Image.new("RGB", (self.canvas_width, self.canvas_height), (0,0,0))
            draw = ImageDraw.Draw(frame)
            self.current_art_url = ''
            self.is_playing = False
            drawPlayPause(draw, self.control_mode, self.is_playing, self.play_color)
            draw.text((0,3), "No Devices", self.title_color, font = self.font)
            draw.text((0,10), "Currently Active", self.title_color, font = self.font)

            return frame

def drawPlayPause(draw, control_mode, is_playing, color):
    if control_mode:
        if not is_playing:
            draw.line((45,19,45,25), fill = color)
            draw.line((46,20,46,24), fill = color)
            draw.line((47,20,47,24), fill = color)
            draw.line((48,21,48,23), fill = color)
            draw.line((49,21,49,23), fill = color)
            draw.line((50,22,50,22), fill = color)
        else:
            draw.line((45,19,45,25), fill = color)
            draw.line((46,19,46,25), fill = color)
            draw.line((49,19,49,25), fill = color)
            draw.line((50,19,50,25), fill = color)

