# sudo apt-get install python-dev
# pip install pyzmq
#

import time
import glob
import logging
import queue
import threading
from functools import wraps

import Messaging
import config

test_logger = logging.getLogger('test')

client_q = queue.Queue()
server_q = queue.Queue()


def test_decorator(q):
    def real_decorator(func):
        @wraps(func)
        def wrapped(msg):
            r = func(msg)
            test_logger.info('{} {} {}'.format(threading.currentThread().getName(), func.__name__, msg))
            q.put(msg)
            return r
        return wrapped
    return real_decorator


@test_decorator(client_q)
def cam_on_cmd_received(msg):
    pass


@test_decorator(server_q)
def backend_on_pic_received(msg):
    pass


@test_decorator(server_q)
def backend_on_variable_received(msg):
    pass


if __name__ == "__main__":
    config.upload_ip = 'localhost'

    # server needs to be on before client. otherwise PUBs are lost
    backend_wan = Messaging.WanServer()
    backend_wan.install(Messaging.Message.Image, backend_on_pic_received)
    backend_wan.install(Messaging.Message.Variable, backend_on_variable_received)
    backend_wan.start()

    cam_wan = Messaging.WanClient()
    cam_wan.install(Messaging.Message.Command, cam_on_cmd_received)
    cam_wan.start()

    pics = glob.glob('test_data/*.png')

    # with curve encryption, it takes some time to connect and negotiate session key
    time.sleep(0.5)

    try:
        for i, pic in enumerate(pics):
            cam_wan.send(Messaging.ImageMessagePeriodical(pic))
            cam_wan.send(Messaging.VariableMessage('index', i))

        backend_wan.send(Messaging.CommandMessage('lights', 'on'))
        backend_wan.send(Messaging.CommandMessage('lights', 'off'))

        test_cases = [
            {
                'input_queue': client_q,
                'expected_ids': [Messaging.Message.Command, Messaging.Message.Command]
            },
            {
                'input_queue': server_q,
                'expected_ids': [Messaging.Message.Image, Messaging.Message.Variable] * len(pics)
            }
        ]

        test_status = 'SUCCESS'

        for test_case in test_cases:
            for expected_id in test_case['expected_ids']:
                try:
                    received_item = test_case['input_queue'].get(timeout=1.0)
                except queue.Empty:
                    test_status = 'FAILED'
                    break
                if received_item is None or received_item['id'] != expected_id:
                    test_status = 'FAILED'
                    break
    finally:
        cam_wan.stop()
        backend_wan.stop()
        print(test_status)


