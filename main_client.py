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


def check_rpi():
    global client_messaging
    temperature = CamUtilities.rpi_temp()
    if temperature is not None:
        client_messaging.send(Messaging.Message.msg_variable('temperature', temperature))


def check_uplink():
    global client_messaging
    stats = CamUtilities.dlink_dwr921_stats('192.168.0.1')
    if stats is not None:
        client_messaging.send(Messaging.Message.msg_text(json.dumps(stats)))
    else:
        main_logger.warn('could not read uplink stats')


if __name__ == "__main__":
    main_logger.info('starting up %s' % config.cam_id)
    client_messaging = client_messaging_start()
    local_messaging = local_messaging_start()
    timer = CamUtilities.Timekeeper()

    timer.add_cron_job(check_rpi, [], '*/10')

    if config.cam_id == 1:
        timer.add_cron_job(check_uplink, [], '*/10')

    camera = Imaging.Camera(timer, on_movement)
    camera.start()

    if config.lights_enabled == 1:
        lights = LightControl.LightControl(on_movement, on_light_control, timer, pir_enabled=False)
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
