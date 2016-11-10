import Messaging
import Datastore
import logging

main_logger = logging.getLogger('Main')


def on_image_received(msg):
    Datastore.add_image(msg['src'], msg['time'], msg['data'])


def on_variable_received(msg):
    Datastore.set_variable(msg['src'], msg['name'], msg['value'])


def on_movement_received(msg):
    pass


def on_text_received(msg):
    pass


def server_messaging_start():
    _messaging = Messaging.ServerMessaging()
    _messaging.start()
    _messaging.install(Messaging.Message.Image, on_image_received)
    _messaging.install(Messaging.Message.Variable, on_variable_received)
    _messaging.install(Messaging.Message.Movement, on_movement_received)
    _messaging.install(Messaging.Message.Text, on_text_received)
    return _messaging


def local_messaging_start():
    _messaging = Messaging.LocalServerMessaging()
    return _messaging


if __name__ == "__main__":
    server_messaging = server_messaging_start()
    local_messaging = local_messaging_start()

    try:
        while True:
            msg = local_messaging.wait()
            if Messaging.Message.verify(msg):
                main_logger.info('forward %s' % Messaging.Message.msg_info(msg))
                server_messaging.send(msg)
    finally:
        server_messaging.stop()
        local_messaging.stop()
