# sudo apt-get install python-dev
# pip install pyzmq
#

import glob
import time

from main_server import messaging_start as server_messaging
from main_client import messaging_start as client_messaging
import Messaging

import config

if __name__ == "__main__":
    config.upload_ip = 'localhost'

    client = client_messaging()
    server = server_messaging()

    pics = glob.glob('test_data/*.png')

    try:
        for pic in pics:
            client.send(Messaging.image_message(pic))
            client.send(Messaging.variable_message('uptime', 'test uptime'))
            time.sleep(1)

        server.send(Messaging.command_message('lights', 'on'))
        server.send(Messaging.command_message('lights', 'off'))
        time.sleep(1)
    finally:
        client.stop()
        server.stop()
