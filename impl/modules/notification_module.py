from threading import Thread
from queue import Queue
import websocket
import json
import time
from functools import cmp_to_key

class NotificationModule:
    def __init__(self, config):
        app_white_list = parseWhiteList(config.get('Notification Module', 'white_list', fallback=None))
        pushbullet_ws = config.get('Notification Module', 'pushbullet_ws', fallback=None)

        if pushbullet_ws is None or app_white_list is None or len(app_white_list) == 0:
            print("[Notification Module] pushbullet websocket url or app white list is not specified in config")
        else:
            self.noti_list = []
            self.noti_queue = Queue()
            Thread(target = startService, args=(self.noti_queue, pushbullet_ws, app_white_list,)).start()
    
    def getNotificationList(self):
        needToSort = False
        while not self.noti_queue.empty():
            new_noti = self.noti_queue.get()
            if new_noti.addToCount:
                found = False
                for noti in self.noti_list:
                    if noti.noti_id == new_noti.noti_id:
                        found = True
                if not found:
                    needToSort = True
                    self.noti_list.append(new_noti)
            else:
                for idx, noti in enumerate(self.noti_list):
                    if noti.noti_id == new_noti.noti_id:
                        self.noti_list.pop(idx)
        if needToSort:
            self.noti_list.sort(key=cmp_to_key(Notification.compare))
        
        return self.noti_list

class Notification:
    def __init__(self, application, addToCount, noti_id, title, body, noti_time):
        self.application = application
        self.addToCount = addToCount
        self.noti_id = noti_id
        self.title = title
        self.body = body
        self.noti_time = noti_time
    
    def compare(noti1, noti2):
        if noti1.noti_time > noti2.noti_time:
            return -1
        elif noti1.noti_time < noti2.noti_time:
            return 1
        else:
            return 0

def on_message(_, message, noti_queue, app_white_list):
    message = json.loads(message)

    if (message['type'] == 'push'):
        contents = message['push']
        if contents['package_name'] in app_white_list.keys():
            if contents['type'] == 'mirror':
                noti_queue.put(Notification(app_white_list[contents['package_name']], True,\
                    int(contents['notification_id']), contents['title'], contents['body'], time.time()))
            elif contents['type'] == 'dismissal':
                noti_queue.put(Notification(app_white_list[contents['package_name']], False,\
                    int(contents['notification_id']), '', '', time.time()))

def on_error(_, error, noti_queue, pushbullet_ws, app_white_list):
    print(error)
    time.sleep(1000)
    startService(noti_queue, pushbullet_ws, app_white_list)

def on_close(_):
    print("### websocket closed ###")

def startService(noti_queue, pushbullet_ws, app_white_list):        
    ws = websocket.WebSocketApp(pushbullet_ws,
                            on_message = lambda ws, message : on_message(ws, message, noti_queue, app_white_list),
                            on_error = lambda ws, error : on_error(ws, error, noti_queue, pushbullet_ws, app_white_list),
                            on_close = on_close)
    ws.run_forever()

def parseWhiteList(strList):
    if strList is None:
        return None

    result = {}
    pairs = strList.split(',')
    for pair in pairs:
        pkg, name = pair.split(':')
        result[pkg] = name
    return result
