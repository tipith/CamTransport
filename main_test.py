import Messaging
import CamUtilities
import Imaging
import time

import logging
import config

main_logger = logging.getLogger('Main')
client_messaging = None


def on_movement(detector, state, uuid):
    pass


def on_any_local(msg):
    main_logger.info('local -> server %s' % Messaging.Message.msg_info(msg))
    client_messaging.send(msg, serialize=False)


if __name__ == "__main__":
    main_logger.info('starting up %s' % config.cam_id)

    client_messaging = Messaging.WanClient()
    client_messaging.start()

    local_messaging = Messaging.LocalServer()
    local_messaging.start()
    local_messaging.install('*', on_any_local)

    client_messaging.send(Messaging.TextMessage('start tester'))

    timer = CamUtilities.Timekeeper()
    camera = Imaging.Camera(timer, on_movement, Imaging.PiCam(), test_mode=True)

    try:
        while True:
            time.sleep(1.0)
    finally:
        client_messaging.stop()
        local_messaging.stop()
        camera.stop()
