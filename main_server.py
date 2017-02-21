import Messaging
import Datastore
import config
import gmail

import logging

main_logger = logging.getLogger('Main')
email_alert = {}

def on_image(msg):
    filename = Datastore.add_image(msg['src'], msg['time'], msg['data'])
    Datastore.db_store_image(msg['src'], msg['time'], filename, len(msg['data']))


def on_variable(msg):
    Datastore.set_variable(msg['src'], msg['name'], msg['value'])


def on_movement(msg):
    Datastore.db_store_movement(msg['src'], msg['time'], msg['detector'], msg['state'], msg['uuid'])


def on_text(msg):
    pass


def on_light_control(msg):
    Datastore.db_store_light_control(msg['src'], msg['time'], msg['state'], msg['uuid'])


def on_image_movement(msg):
    global email_alert
    filename = Datastore.add_image_movement(msg['src'], msg['time'], msg['uuid'], msg['data'])
    Datastore.db_store_image_movement(msg['src'], msg['time'], filename, msg['uuid'], len(msg['data']))
    # send only the first picture belonging to a group of pictures from a source. uuid is the group identifier
    if msg['src'] not in email_alert or email_alert[msg['src']] != msg['uuid']:
        email_alert[msg['src']] = msg['uuid']
        gmail.send('Activity from cam %i' % msg['src'], 'See attachment.', msg['data'])


def on_any(msg):
    Datastore.set_variable(msg['src'], 'uptime', msg['uptime'])


def server_messaging_start():
    _messaging = Messaging.ServerMessaging()
    _messaging.start()
    _messaging.install(Messaging.Message.Image, on_image)
    _messaging.install(Messaging.Message.Variable, on_variable)
    _messaging.install(Messaging.Message.Movement, on_movement)
    _messaging.install(Messaging.Message.Text, on_text)
    _messaging.install(Messaging.Message.LightControl, on_light_control)
    _messaging.install(Messaging.Message.ImageMovement, on_image_movement)
    _messaging.install('*', on_any)
    return _messaging


def local_messaging_start():
    _messaging = Messaging.LocalServerMessaging()
    return _messaging


if __name__ == "__main__":
    server_messaging = server_messaging_start()
    local_messaging = local_messaging_start()

    try:
        while True:
            message = local_messaging.wait()
            if Messaging.Message.verify(message):
                main_logger.info('forward %s' % Messaging.Message.msg_info(message))
                server_messaging.send(message)
    finally:
        server_messaging.stop()
        local_messaging.stop()
