# sudo apt-get install python-dev
# pip install pyzmq
#

import glob
import time

from main_subscriber import listener_start
from main_publisher import publish_image
import cam_config

if __name__ == "__main__":
    listener = listener_start()
    pics = glob.glob('test_data/*.png')
    cam_config.upload_ip = 'localhost'

    try:
        for pic in pics:
            publish_image(pic)
            time.sleep(1)
    finally:
        listener.stop()
