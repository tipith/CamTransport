from datetime import datetime
import logging

import config

message_logger = logging.getLogger('Message')


@staticmethod
def _uptime():
    try:
        with open('/proc/uptime', 'r') as f:
            return int(float(f.readline().split()[0]))
    except IOError:
        return 0


class AlhoMessageException(Exception):
    pass


class Message(object):

    Image = 1
    Variable = 2
    Command = 3
    MovementEvent = 4
    Text = 5
    LightControlEvent = 6
    Heartbeat = 8

    known_messages = [Image, Variable, Command, MovementEvent, Text, LightControlEvent, Heartbeat]
    header_fields = ['src', 'time', 'uptime', 'id']

    def __init__(self):
        pass

    def header(self, src, id):
        return dict(zip(Message.header_fields, [src, datetime.now().replace(microsecond=0), _uptime(), id]))

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
    def msg_info(msg):
        src = msg['src']
        timestamp = msg['time'].strftime("%Y-%m-%d %H:%M:%S")

        if msg['id'] == Message.Image:
            return 'image from %s, %s, length %i B' % (src, timestamp, len(msg['data']))
        if msg['id'] == Message.Variable:
            return 'variable from %s, %s, %s -> %s' % (src, timestamp, msg['name'], msg['value'])
        if msg['id'] == Message.Command:
            return 'command from %s, %s, %s -> %s' % (src, timestamp, msg['command'], msg['parameter'])
        if msg['id'] == Message.MovementEvent:
            return 'movement from %s, %s, detector %s, state %s' % (src, timestamp, msg['detector'], msg['state'])
        if msg['id'] == Message.Text:
            return 'text from %s, %s: %s' % (src, timestamp, msg['text'])
        if msg['id'] == Message.LightControlEvent:
            return 'lightcontrol from %s, %s, %s' % (src, timestamp, msg['state'])
        return 'unknown message'


class ImageMessage(Message):
    def __init__(self):
        super(ImageMessage, self).__init__()

    def __str__(self):
        return self.text

    def __call__(self):
        msg = self.header(config.cam_id, Message.Image)
        msg['type'] = self.type
        msg['data'] = self.img
        msg['uuid'] = self.uuid
        return msg


class ImageMessagePeriodical(ImageMessage):
    def __init__(self, img):
        self.type = 1
        self.img = img
        self.uuid = ''
        super(ImageMessagePeriodical, self).__init__()


class ImageMessageMovement(ImageMessage):
    def __init__(self, img, uuid):
        self.type = 2
        self.img = img
        self.uuid = uuid
        super(ImageMessageMovement, self).__init__()


class ImageMessageLive(ImageMessage):
    def __init__(self, img):
        self.type = 3
        self.img = img
        self.uuid = ''
        super(ImageMessageLive, self).__init__()


class VariableMessage(Message):
    def __init__(self, name, value):
        self.name = name
        self.value = value
        super(VariableMessage, self).__init__()

    def __call__(self):
        msg = self.header(config.cam_id, Message.Variable)
        msg['name'] = self.name
        msg['value'] = self.value
        return msg


class CommandMessage(Message):
    def __init__(self, command, parameter):
        self.command = command
        self.parameter = parameter
        super(CommandMessage, self).__init__()

    def __call__(self):
        msg = self.header('server', Message.Command)
        msg['command'] = self.command
        msg['parameter'] = self.parameter
        return msg


class MovementEventMessage(Message):
    def __init__(self, detector, state, uuid):
        self.detector = detector
        self.state = state
        self.uuid = uuid
        super(MovementEventMessage, self).__init__()

    def __call__(self):
        msg = self.header(config.cam_id, Message.MovementEvent)
        msg['detector'] = self.detector
        msg['state'] = self.state
        msg['uuid'] = self.uuid
        return msg


class TextMessage(Message):
    def __init__(self, text):
        self.text = text
        super(TextMessage, self).__init__()

    def __call__(self):
        msg = self.header(config.cam_id, Message.Text)
        msg['text'] = self.text
        return msg


class LightControlEventMessage(Message):
    def __init__(self, state, uuid):
        self.state = state
        self.uuid = uuid
        super(LightControlEventMessage, self).__init__()

    def __call__(self):
        msg = self.header(config.cam_id, Message.LightControlEvent)
        msg['state'] = self.state
        msg['uuid'] = self.uuid
        return msg


class HeartbeatMessage(Message):
    def __init__(self):
        super(HeartbeatMessage, self).__init__()

    def __call__(self):
        return self.header(config.cam_id, Message.Heartbeat)
