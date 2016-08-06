import time
import Messaging
import Datastore


def on_image_received(msg):
    print('on_image_received: from', msg['src'], msg['time'])
    Datastore.add_image(msg['src'], msg['time'], msg['data'])


def on_variable_received(msg):
    print('on_variable_received: from', msg['src'], msg['name'], ':', msg['value'])
    Datastore.set_variable(msg['src'], msg['name'], msg['value'])


def listener_start():
    listener = Messaging.MessageListener()
    listener.start()
    listener.install(Messaging.Message.Image, on_image_received)
    listener.install(Messaging.Message.Variable, on_variable_received)
    return listener


if __name__ == "__main__":
    listener = listener_start()
    while True:
        time.sleep(1)
    listener.stop()
