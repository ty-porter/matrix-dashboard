from PIL import Image, ImageFont, ImageDraw
import numpy as np
import yfinance as yf
import time
import threading
from queue import LifoQueue

white = (255,255,255)
red = (255,0,0)
green = (0,255,0)
up_arrow = np.asarray([[0,0,1,0,0],[0,1,1,1,0],[1,1,1,1,1]])
down_arrow = np.asarray([[1,1,1,1,1],[0,1,1,1,0],[0,0,1,0,0]])

class StocksVerticalScreen:
    def __init__(self, config, modules, default_actions):
        self.ticker_symbols = ['DOGE-USD', 'GME', 'AMC', 'TSM', 'AMD']
        self.tiny_font = ImageFont.truetype("fonts/tiny.otf", 5)
        self.bg = Image.open('apps_v2/res/tothemoon_darker.png').convert('RGB')
        self.queue = LifoQueue()
        self.thread = threading.Thread(target=generateFrameAsync, 
                        args=(self.queue, self.ticker_symbols, self.tiny_font, self.bg))
        self.thread.start()
        self.frame = self.bg.rotate(90, expand=True)
    
    def generate(self, isHorizontal, inputStatus):
        if not self.queue.empty():
            self.frame = self.queue.get()
            self.queue.queue.clear()
        return self.frame

def get_price(symbol):
    ticker = yf.Ticker(symbol)
    week_data = ticker.history(period='5d')
    if (int(week_data['Close'][-1]) < 1.0):
        current = "{:.4f}".format(week_data['Close'][-1])
        last_close = "{:.4f}".format(week_data['Close'][-2])
    else:  
        current = "{:.2f}".format(week_data['Close'][-1])
        last_close = "{:.2f}".format(week_data['Close'][-2])
    return (current, last_close)

def generateLineArray(text, font):
    img = Image.new("RGB", (100,500), (0,0,0))
    draw = ImageDraw.Draw(img)
    draw.text((0,0), text, (255,255,255), font=font)
    img = img.crop(img.getbbox())
    return np.array(img)[:,:,0]/255

def placeText(frame, x, y, color, text_arr, isLeftReference):
    arr_height = text_arr.shape[0]
    arr_width = text_arr.shape[1]
    values = np.ones((1, arr_height * arr_width), dtype='uint8')
    if (isLeftReference):
        np.putmask(frame[y:y+arr_height, x:x+arr_width, 0], text_arr.astype(bool), values * color[0])
        np.putmask(frame[y:y+arr_height, x:x+arr_width, 1], text_arr.astype(bool), values * color[1])
        np.putmask(frame[y:y+arr_height, x:x+arr_width, 2], text_arr.astype(bool), values * color[2])
    else:
        np.putmask(frame[y:y+arr_height, x-arr_width:x, 0], text_arr.astype(bool), values * color[0])
        np.putmask(frame[y:y+arr_height, x-arr_width:x, 1], text_arr.astype(bool), values * color[1])
        np.putmask(frame[y:y+arr_height, x-arr_width:x, 2], text_arr.astype(bool), values * color[2])

def generateFrameAsync(queue, ticker_symbols, font, bg):
    while True:
        frame = np.copy(bg)
        for i in range(len(ticker_symbols)):
            symbol = ticker_symbols[i]
            (current, last_close) = get_price(symbol)

            stock_symbol_arr = generateLineArray(symbol.split("-")[0], font)
            stock_price_arr = generateLineArray(current, font)
            (arrow_color, arrow_arr) = (green, up_arrow) if float(current) - float(last_close) >= 0 else (red, down_arrow)

            placeText(frame, 0, 13*i, white, stock_symbol_arr, True)
            placeText(frame, 31, 6+13*i, white, stock_price_arr, False)
            placeText(frame, 25, 1+13*i, arrow_color, arrow_arr, True)

        frame = np.rot90(frame)
        queue.put(Image.fromarray(frame,'RGB'))
        time.sleep(5)