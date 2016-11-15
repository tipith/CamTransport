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

    known_messages = [Image, Variable, Command, Movement, Text, LightControl]

    @staticmethod
    def verify(msg):
        if msg is not None:
            if 'id' in msg:
                if msg['id'] in Message.known_messages:
                    if 'src' in msg:
                        if 'time' in msg:
                            return True
                        else:
                            message_logger.warn('Error: message does not contain time field')
                    else:
                        message_logger.warn('Error: message does not contain source field')
                else:
                    message_logger.warn('Error: message id is not known: %i' % (msg['id']))
            else:
                message_logger.warn('Error: message does not contain frame id field')
        return False

    @staticmethod
    def msg_image(data):
        return {'src': cam_config.cam_id,
                'time': datetime.now(),
                'id': Message.Image,
                'data': data}

    @staticmethod
    def msg_variable(name, value):
        return {'src': cam_config.cam_id,
                'time': datetime.now().replace(microsecond=0),
                'id': Message.Variable,
                'name': name,
                'value': value}

    @staticmethod
    def msg_command(command, parameter):
        return {'src': 'server',
                'time': datetime.now().replace(microsecond=0),
                'id': Message.Command,
                'command': command,
                'parameter': parameter}

    @staticmethod
    def msg_movement(detector, state):
        return {'src': cam_config.cam_id,
                'time': datetime.now().replace(microsecond=0),
                'id': Message.Movement,
                'detector': detector,
                'state': state}

    @staticmethod
    def msg_text(text):
        return {'src': cam_config.cam_id,
                'time': datetime.now().replace(microsecond=0),
                'id': Message.Text,
                'text': text}

    @staticmethod
    def msg_light_control(state):
        return {'src': cam_config.cam_id,
                'time': datetime.now().replace(microsecond=0),
                'id': Message.LightControl,
                'state': state}

    @staticmethod
    def msg_info(msg):
        timestamp = msg['time'].strftime("%Y-%m-%d %H:%M:%S")

        if msg['id'] == Message.Image:
            return 'image from %s, %s, length %i B' % (msg['src'], timestamp, len(msg['data']))
        if msg['id'] == Message.Variable:
            return 'variable from %s, %s, %s -> %s' % (msg['src'], timestamp, msg['name'], msg['value'])
        if msg['id'] == Message.Command:
            return 'command from %s, %s, %s -> %s' % (msg['src'], timestamp, msg['command'], msg['parameter'])
        if msg['id'] == Message.Movement:
            return 'movement from %s, %s, detector %s, state %s' % (msg['src'], timestamp, msg['detector'], msg['state'])
        if msg['id'] == Message.Text:
            return 'text from %s, %s: %s' % (msg['src'], timestamp, msg['text'])
        if msg['id'] == Message.LightControl:
            return 'lightcontrol from %s, %s, %s' % (msg['src'], timestamp, msg['state'])
        return 'unknown message'
