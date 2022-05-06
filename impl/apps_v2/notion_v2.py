import time
from PIL import Image, ImageFont, ImageDraw
import threading
from queue import LifoQueue
from InputStatus import InputStatusEnum
import requests, json
from datetime import date
from datetime import timedelta
from ast import literal_eval

class NotionScreen:
    def __init__(self, config, modules, default_actions):
        self.modules = modules
        self.default_actions = default_actions

        self.font = ImageFont.truetype("fonts/tiny.otf", 5)
        self.queue = LifoQueue()
        self.tasks = None
        self.animation_cnt = [0,0,0,0,0]

        self.canvas_width = config.getint('System', 'canvas_width', fallback=64)
        self.canvas_height = config.getint('System', 'canvas_height', fallback=32)

        notion_token = config.get('Notion', 'token', fallback=None)
        notion_database_id = config.get('Notion', 'database_id', fallback=None)
        
        self.text_color = literal_eval(config.get('Notion', 'text_color',fallback="(255,255,255)"))
        self.todo_color = literal_eval(config.get('Notion', 'todo_color',fallback="(255,100,140)"))
        self.doing_color = literal_eval(config.get('Notion', 'doing_color',fallback="(255,202,0)"))

        self.paused = False

        if notion_token is None or notion_database_id is None:
            print("[Notion] Notion token and/or databaseID is not specified in config")
        else:
            threading.Thread(target=fetchNotionAsync, args=(self.queue, notion_token, notion_database_id)).start()
    
    def generate(self, isHorizontal, inputStatus):
        while not self.queue.empty():
            new_tasks = self.queue.get()
            if (self.tasks != new_tasks):
                self.tasks = new_tasks
                self.queue.queue.clear()
                self.animation_cnt = [0,0,0,0,0,0,0,0,0,0]

        if (inputStatus is InputStatusEnum.SINGLE_PRESS):
            self.paused = not self.paused
            self.animation_cnt = [0,0,0,0,0,0,0,0,0,0]
        elif (inputStatus is InputStatusEnum.ENCODER_INCREASE):
            self.default_actions['switch_next_app']()
        elif (inputStatus is InputStatusEnum.ENCODER_DECREASE):
            self.default_actions['switch_prev_app']()

        frame = None
        if isHorizontal:
            frame = Image.new("RGB", (self.canvas_width, self.canvas_height), (0,0,0))
            draw = ImageDraw.Draw(frame)

            if self.tasks is None or len(self.tasks) == 0:
                draw.text((0, 0), "NO TASKS YET.", self.text_color, font = self.font)
            else:
                for i in range(len(self.tasks[0:5])):
                    task_desc = self.tasks[i]["properties"]["Name"]["title"][0]["plain_text"].upper()
                    task_desc_len = self.font.getsize(self.tasks[i]["properties"]["Name"]["title"][0]["plain_text"].upper())[0]

                    if task_desc_len >= self.canvas_width - 3:
                        spacer = "     "
                        draw.text((3-self.animation_cnt[i], 6*i), task_desc + spacer + task_desc, self.text_color, font=self.font)
                        if not self.paused:
                            self.animation_cnt[i] += 1
                        if self.animation_cnt[i] == self.font.getsize(self.tasks[i]["properties"]["Name"]["title"][0]["plain_text"].upper() + spacer)[0]:
                            self.animation_cnt[i] = 0
                    else:
                        draw.text((3, 6*i), task_desc, self.text_color, font=self.font)

                    task_status = self.tasks[i]["properties"]["Status"]["select"]["name"]
                    if task_status == 'To Do':
                        status_color = self.todo_color
                    elif task_status == 'Doing':
                        status_color = self.doing_color
                    else:
                        status_color = (0,0,0)

                    draw.rectangle((0, 6*i, 1, 6*i+4), fill=status_color)
                    draw.rectangle((2, 6*i, 2, 6*i+4), fill=(0,0,0))
        else:
            frame = Image.new("RGB", (self.canvas_height, self.canvas_width), (0,0,0))
            draw = ImageDraw.Draw(frame)

            if self.tasks is None or len(self.tasks) == 0:
                draw.text((0, 26), "NO TASKS", self.text_color, font = self.font)
            else:
                for i in range(len(self.tasks[0:9])):
                    task_desc = self.tasks[i]["properties"]["Name"]["title"][0]["plain_text"].upper()
                    task_desc_len = self.font.getsize(self.tasks[i]["properties"]["Name"]["title"][0]["plain_text"].upper())[0]

                    if task_desc_len >= self.canvas_height - 3:
                        spacer = "     "
                        draw.text((3-self.animation_cnt[i], 6*i), task_desc + spacer + task_desc, self.text_color, font=self.font)
                        if not self.paused:
                            self.animation_cnt[i] += 1
                        if self.animation_cnt[i] == self.font.getsize(self.tasks[i]["properties"]["Name"]["title"][0]["plain_text"].upper() + spacer)[0]:
                            self.animation_cnt[i] = 0
                    else:
                        draw.text((3, 6*i), task_desc, self.text_color, font=self.font)

                    task_status = self.tasks[i]["properties"]["Status"]["select"]["name"]
                    if task_status == 'To Do':
                        status_color = self.todo_color
                    elif task_status == 'Doing':
                        status_color = self.doing_color
                    else:
                        status_color = (0,0,0)

                    draw.rectangle((0, 6*i, 1, 6*i+4), fill=status_color)
                    draw.rectangle((2, 6*i, 2, 6*i+4), fill=(0,0,0))

            frame = frame.rotate(angle=90, expand=True)
        return frame


def fetchNotionAsync(queue, token, databaseID):
    headers = {
        "Authorization" : "Bearer " + token,
        "Notion-Version" : "2021-08-16",
        "Content-Type" : "application/json"
    }
    queryURL = f"https://api.notion.com/v1/databases/{databaseID}/query"

    while True:
        yesterday = date.today() - timedelta(days=1)
        week_from_now = date.today() + timedelta(days=7)

        query_params = {
            "sorts" : [
                {
                    "property" : "Date Due",
                    "timestamp" : "created_time",
                    "direction" : "ascending"
                },
            ],
            "filter" : {
                "or" : [
                    {
                        "and" : [
                            {
                                "property" : "Date Due",
                                "date" : {
                                    "on_or_before" : week_from_now.isoformat()
                                }
                            },
                            {
                                "property" : "Status",
                                "select" : {
                                    "equals" : "Doing"
                                }
                            }
                        ]
                    },
                    {
                        "and" : [
                            {
                                "property" : "Date Due",
                                "date" : {
                                    "on_or_before" : week_from_now.isoformat()
                                }
                            },
                            {
                                "property" : "Status",
                                "select" : {
                                    "equals" : "To Do"
                                }
                            }
                        ]
                    },
                    {
                        "property" : "Status",
                        "select" : {
                            "equals" : "Unassigned"
                        }
                    },
                    {
                        "property" : "Date Due",
                        "date" : {
                            "on_or_after" : yesterday.isoformat()
                        }
                    }
                ]
            }
        }

        res = requests.request("POST", queryURL, headers=headers, data = json.dumps(query_params))
        if res.status_code is not 200:
            print("[Notion] Status Returned is " + str(res.status_code))
            print(res.json())
        else:
            tasks = res.json()["results"]
            queue.put(tasks)
            time.sleep(30)

