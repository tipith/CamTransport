import Messaging
import LightControl
import CamUtilities
import Imaging
import json
import time

import logging
import config

main_logger = logging.getLogger('Main')
lights = None
client_messaging = None
camera = None


def on_cmd_received(msg):
    if lights is not None and msg['command'] == 'lights':
        if msg['parameter'] == 'on':
            lights.turn_on()
        else:
            lights.turn_off()
    elif camera is not None and msg['command'] == 'livestream':
        if msg['parameter'] == 'on':
            client_messaging.send(Messaging.TextMessage('streaming for 10 minutes'))
            camera.livestream(600)
        else:
            client_messaging.send(Messaging.TextMessage('stop streaming'))
            camera.livestream(0)


def on_movement(detector, state, uuid):
    main_logger.info('on_movement: %s from %s with uuid %s' % (state, detector, uuid))
    if client_messaging is not None:
        client_messaging.send(Messaging.MovementEventMessage(detector, state, uuid))


def on_light_control(state, uuid):
    main_logger.info('on_light_control: %s, uuid %s' % (state, uuid))
    if client_messaging is not None:
        client_messaging.send(Messaging.LightControlEventMessage(state, uuid))
    if camera is not None:
        camera.light_control(state)


def check_rpi():
    temperature = CamUtilities.rpi_temp()
    if temperature is not None:
        client_messaging.send(Messaging.VariableMessage('temperature', temperature))


def check_uplink():
    stats = CamUtilities.dlink_dwr921_stats('192.168.0.1')
    if stats is not None:
        client_messaging.send(Messaging.TextMessage(json.dumps(stats)))
    else:
        main_logger.warn('could not read uplink stats')


def on_any_local(msg):
    main_logger.info('local -> server %s' % Messaging.Message.msg_info(msg))
    client_messaging.send(msg, serialize=False)


if __name__ == "__main__":
    main_logger.info('starting up %s' % config.cam_id)

    client_messaging = Messaging.WanClient()
    client_messaging.start()
    client_messaging.install(Messaging.Message.Command, on_cmd_received)

    local_messaging = Messaging.LocalServer()
    local_messaging.start()
    local_messaging.install('*', on_any_local)

    client_messaging.send(Messaging.TextMessage('start'))

    timer = CamUtilities.Timekeeper()
    timer.add_cron_job(check_rpi, [], '*/10')
    if config.cam_id == 1:
        timer.add_cron_job(check_uplink, [], '*/10')

    camera = Imaging.Camera(timer, on_movement, Imaging.USBCam())
    camera.start()

    if config.lights_enabled == 1:
        lights = LightControl.LightControl(on_movement, on_light_control, timer, pir_enabled=True)
        lights.start()

    try:
        while True:
            time.sleep(1.0)
    finally:
        client_messaging.stop()
        local_messaging.stop()
        if lights is not None:
            lights.stop()
        camera.stop()
