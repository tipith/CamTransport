import Messaging
import LightControl
import Timekeeper
import Imaging

import logging
import cam_config

main_logger = logging.getLogger('Main')
lights = None
client_messaging = None
camera = None


def get_uptime():
    try:
        with open('/proc/uptime', 'r') as f:
            return int(float(f.readline().split()[0]))
    except IOError:
        return 0


def on_cmd_received(msg):
    global lights
    main_logger.info('command received')
    if lights is not None and msg['command'] == 'lights':
        if msg['parameter'] == 'on':
            lights.turn_on()
        else:
            lights.turn_off()


def client_messaging_start():
    _messaging = Messaging.ClientMessaging()
    _messaging.start()
    _messaging.install(Messaging.Message.Command, on_cmd_received)
    return _messaging


def local_messaging_start():
    _messaging = Messaging.LocalServerMessaging()
    return _messaging


def on_movement(state):
    global client_messaging
    if client_messaging is not None:
        client_messaging.send(Messaging.Message.msg_movement(state))


def on_light_control(state):
    global client_messaging, camera
    if client_messaging is not None:
        client_messaging.send(Messaging.Message.msg_light_control(state))
    if camera is not None:
        camera.light_control(state)


if __name__ == "__main__":
    main_logger.info('starting up %s' % cam_config.cam_id)
    client_messaging = client_messaging_start()
    local_messaging = local_messaging_start()
    timer = Timekeeper.Timekeeper()
    lights = LightControl.LightControl(on_movement, on_light_control, timer)
    camera = Imaging.Camera(timer)
    lights.start()

    client_messaging.send(Messaging.Message.msg_text('start'))

    try:
        while True:
            msg = local_messaging.wait()
            if Messaging.Message.verify(msg):
                main_logger.info('forward %s' % Messaging.Message.msg_info(msg))
                client_messaging.send(msg)
                client_messaging.send(Messaging.Message.msg_variable('uptime', get_uptime()))
    finally:
        client_messaging.stop()
        local_messaging.stop()
        lights.stop()
