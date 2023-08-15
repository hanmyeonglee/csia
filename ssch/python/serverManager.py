from threading import Thread, Event
from server import main
from time import sleep
from datetime import datetime

event = Event()

def startServer():
    return Thread(target=main, args=datetime.now().strftime("%Y.%m.%d"))


def stopServer(subthread: Thread):
    subthread.


while True:
    tmp = startServer()
    print("start")
    sleep(1)
    print("stop")
    stopServer(tmp)
