import Messaging
import LightControl
from datetime import timedelta
import logging

main_logger = logging.getLogger('Main')
lights = None


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
    main_logger.info('%s: command %s -> %s' % (msg['src'], msg['command'], msg['parameter']))
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


if __name__ == "__main__":
    client_messaging = client_messaging_start()
    local_messaging = local_messaging_start()
    lights = LightControl.LightControl()
    lights.start()

    try:
        while True:
            msg = local_messaging.wait()
            if Messaging.Message.verify(msg):
                main_logger.info('forwarding id %i with timestamp %s' % (msg['id'], msg['timestamp']))
                client_messaging.send(msg)
                client_messaging.send(Messaging.Message.msg_variable('uptime', get_uptime()))
    finally:
        client_messaging.stop()
        local_messaging.stop()
        lights.stop()
