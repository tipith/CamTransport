from datetime import datetime
import ntpath
import re
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

    known_messages = [Image, Variable, Command, Movement]

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
    def msg_image(filename):
        with open(filename, 'rb') as f:
            #timestamp = datetime.strptime(m.group(1), '%Y%m%d_%H%M%S')
            return {'src': cam_config.cam_name,
                    'time': datetime.now().time(),
                    'id': Message.Image,
                    'data': f.read()}
            # /var/www/html/media/im_2436_20160806_191001.jpg
            #m = re.match('im_\d+_(\d{8}_\d{6}).(jpg|png)', ntpath.basename(file))
            #if m:
            #    timestamp = datetime.strptime(m.group(1), '%Y%m%d_%H%M%S')
            #    return {'src': cam_config.cam_name,
            #            'time': timestamp,
            #            'id': Message.Image,
            #            'data': f.read()}
            #else:
            #    message_logger.warn('Error: invalid image name')
            #    raise AlhoMessageException()

    @staticmethod
    def msg_variable(name, value):
        return {'src': cam_config.cam_name,
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
    def msg_movement(state):
        return {'src': cam_config.cam_name,
                'time': datetime.now().replace(microsecond=0),
                'id': Message.Movement,
                'state': state}

    @staticmethod
    def msg_info(msg):
        if msg['id'] == Message.Image:
            return 'Message.Image,    from %s, %s, length %i B' % (msg['src'], msg['time'], len(msg['data']))
        if msg['id'] == Message.Variable:
            return 'Message.Variable, from %s, %s, %s -> %s' % (msg['src'], msg['time'], msg['name'], msg['value'])
        if msg['id'] == Message.Command:
            return 'Message.Command,  from %s, %s, %s -> %s' % (msg['src'], msg['time'], msg['command'], msg['parameter'])
        if msg['id'] == Message.Movement:
            return 'Message.Movement, from %s, %s, %s' % (msg['src'], msg['time'], msg['state'])
