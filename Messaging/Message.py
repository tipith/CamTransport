from datetime import datetime
import logging

import cam_config

message_logger = logging.getLogger('Message')


class AlhoMessageException(Exception):
    pass


class Message:
    Image = 1
    Variable = 2
    Command = 3
    Movement = 4
    Text = 5
    LightControl = 6
    ImageMovement = 7

    known_messages = [Image, Variable, Command, Movement, Text, LightControl, ImageMovement]
    header_fields = ['src', 'time', 'uptime', 'id']

    @staticmethod
    def _uptime():
        try:
            with open('/proc/uptime', 'r') as f:
                return int(float(f.readline().split()[0]))
        except IOError:
            return 0

    @staticmethod
    def _header(src, id):
        return dict(zip(Message.header_fields, [src, datetime.now().replace(microsecond=0), Message._uptime(), id]))

    @staticmethod
    def verify(msg):
        if msg is not None:
            if all(k in msg for k in Message.header_fields):
                if msg['id'] in Message.known_messages:
                    return True
                else:
                    message_logger.warn('Error: message id is not known: %i' % (msg['id']))
            else:
                message_logger.warn('Error: invalid header fields')
        return False

    @staticmethod
    def msg_image(img):
        msg = Message._header(cam_config.cam_id, Message.Image)
        msg['data'] = img
        return msg

    @staticmethod
    def msg_variable(name, value):
        msg = Message._header(cam_config.cam_id, Message.Variable)
        msg['name'] = name
        msg['value'] = value
        return msg

    @staticmethod
    def msg_command(command, parameter):
        msg = Message._header('server', Message.Command)
        msg['command'] = command
        msg['parameter'] = parameter
        return msg

    @staticmethod
    def msg_movement(detector, state, uuid):
        msg = Message._header(cam_config.cam_id, Message.Movement)
        msg['detector'] = detector
        msg['state'] = state
        msg['uuid'] = uuid
        return msg

    @staticmethod
    def msg_text(text):
        msg = Message._header(cam_config.cam_id, Message.Text)
        msg['text'] = text
        return msg

    @staticmethod
    def msg_light_control(state, uuid):
        msg = Message._header(cam_config.cam_id, Message.LightControl)
        msg['state'] = state
        msg['uuid'] = uuid
        return msg

    @staticmethod
    def msg_movement_image(img, uuid):
        msg = Message._header(cam_config.cam_id, Message.ImageMovement)
        msg['uuid'] = uuid
        msg['img'] = img
        return msg

    @staticmethod
    def msg_info(msg):
        src = msg['src']
        timestamp = msg['time'].strftime("%Y-%m-%d %H:%M:%S")

        if msg['id'] == Message.Image:
            return 'image from %s, %s, length %i B' % (src, timestamp, len(msg['data']))
        if msg['id'] == Message.Variable:
            return 'variable from %s, %s, %s -> %s' % (src, timestamp, msg['name'], msg['value'])
        if msg['id'] == Message.Command:
            return 'command from %s, %s, %s -> %s' % (src, timestamp, msg['command'], msg['parameter'])
        if msg['id'] == Message.Movement:
            return 'movement from %s, %s, detector %s, state %s' % (src, timestamp, msg['detector'], msg['state'])
        if msg['id'] == Message.Text:
            return 'text from %s, %s: %s' % (src, timestamp, msg['text'])
        if msg['id'] == Message.LightControl:
            return 'lightcontrol from %s, %s, %s' % (src, timestamp, msg['state'])
        if msg['id'] == Message.ImageMovement:
            return 'image from %s, %s, uuid %s, length %i B' % (src, timestamp, msg['uuid'], len(msg['data']))
        return 'unknown message'
