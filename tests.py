import Messaging
import time
import multiprocessing
from zmq.devices.basedevice import ProcessDevice

import config


def on_text(msg):
    assert Messaging.Message.verify(msg)
    assert msg['text'] == 'test'
    print('passed')


def test1():
    c = Messaging.ClientMessaging()
    s = Messaging.ServerMessaging()
    c.start()
    s.start()

    s.install(Messaging.Message.Text, on_text)

    try:
        c.send(Messaging.Message.msg_text('test'))
        time.sleep(1)
    finally:
        c.stop()
        s.stop()


def test2():
    monitoring_p = multiprocessing.Process(target=Messaging.ClientDevice)
    monitoring_p.start()


def test_heartbeat():
    c = Messaging.ClientMessaging()
    s = Messaging.ServerMessaging()
    c.start()
    s.start()

    s.install(Messaging.Message.Text, on_text)

    try:
        c.send(Messaging.Message.msg_text('test'))
        time.sleep(100)
    finally:
        c.stop()
        s.stop()


if __name__ == '__main__' and __package__ is None:
    #test1()
    test_heartbeat()

