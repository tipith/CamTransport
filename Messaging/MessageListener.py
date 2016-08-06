import threading
from .MessageSubscriber import MessageSubscriber


class MessageListener(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.sub = MessageSubscriber()
        self.is_running = True
        self.handlers = {}

    def run(self):
        print("MessageListener: started")
        while self.is_running:
            msg = self.sub.wait_for_pub()
            if msg is not None:
                if 'id' in msg:
                    if msg['id'] in self.handlers:
                        self.handlers[msg['id']](msg)
                    else:
                        print('MessageListener: no handler found for frame')
                else:
                    print('MessageListener: message does not contain frame id')
        self.sub.close()
        print("MessageListener: stopped")

    def install(self, frame, handler):
        self.handlers[frame] = handler

    def stop(self):
        self.is_running = False
