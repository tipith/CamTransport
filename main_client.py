import Messaging
import LightControl
import CamUtilities
import Imaging
import json

import logging
import config

main_logger = logging.getLogger('Main')
lights = None
client_messaging = None
camera = None


def on_cmd_received(msg):
    global lights
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


def on_movement(detector, state, uuid):
    global client_messaging
    main_logger.info('on_movement: %s from %s with uuid %s' % (state, detector, uuid))
    if client_messaging is not None:
        client_messaging.send(Messaging.Message.msg_movement(detector, state, uuid))


def on_light_control(state, uuid):
    global client_messaging, camera
    main_logger.info('on_light_control: %s, uuid %s' % (state, uuid))
    if client_messaging is not None:
        client_messaging.send(Messaging.Message.msg_light_control(state, uuid))
    if camera is not None:
        camera.light_control(state)


def check_uplink(local_comm):
    stats = CamUtilities.dlink_dwr921_stats('192.168.0.1')
    if stats is not None:
        main_logger.info(stats)
        local_comm.send(Messaging.Message.msg_text(json.dumps()))
    else:
        main_logger.info('could not read uplink stats')


if __name__ == "__main__":
    main_logger.info('starting up %s' % config.cam_id)
    client_messaging = client_messaging_start()
    local_messaging = local_messaging_start()
    timer = CamUtilities.Timekeeper()

    if config.cam_id == 1:
        timer.add_cron_job(check_uplink, [local_messaging], '*/1')

    camera = Imaging.Camera(timer, on_movement)
    camera.start()

    if config.lights_enabled == 1:
        lights = LightControl.LightControl(on_movement, on_light_control, timer)
        lights.start()

    client_messaging.send(Messaging.Message.msg_text('start'))

    try:
        while True:
            msg = local_messaging.wait()
            if Messaging.Message.verify(msg):
                main_logger.info('%s' % Messaging.Message.msg_info(msg))
                client_messaging.send(msg)
    finally:
        client_messaging.stop()
        local_messaging.stop()
        if lights is not None:
            lights.stop()
        camera.stop()
