import Messaging
import LightControl
import Timekeeper
import Imaging

from datetime import timedelta
import logging
import cam_config

main_logger = logging.getLogger('Main')
lights = None
client_messaging = None


def strfdelta(tdelta, fmt):
    d = {"days": tdelta.days}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    return fmt.format(**d)


def get_uptime():
    uptime_string = 'none'
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            uptime_string = strfdelta(timedelta(seconds=uptime_seconds), "{days} paivaa {hours}:{minutes}:{seconds}")
    except IOError:
        pass
    return uptime_string


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


def on_movement_detected(state):
    global client_messaging
    if client_messaging is not None:
        client_messaging.send(Messaging.Message.msg_movement(state))


if __name__ == "__main__":
    main_logger.info('starting up %s' % cam_config.cam_name)
    client_messaging = client_messaging_start()
    local_messaging = local_messaging_start()
    timer = Timekeeper.Timekeeper()
    lights = LightControl.LightControl(on_movement_detected, timer)
    camera = Imaging.Camera(timer)
    lights.start()

    try:
        while True:
            msg = local_messaging.wait()
            if Messaging.Message.verify(msg):
                main_logger.info('forwarding %s' % Messaging.Message.msg_info(msg))
                client_messaging.send(msg)
                client_messaging.send(Messaging.Message.msg_variable('uptime', get_uptime()))
    finally:
        client_messaging.stop()
        local_messaging.stop()
        lights.stop()
