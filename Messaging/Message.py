from datetime import datetime
import ntpath
import re
import cam_config


class AlhoMessageException(Exception):
    pass


class Message:
    Image = 1
    Variable = 2


def image_message(file):
    with open(file, 'rb') as f:
        # /var/www/html/media/im_2436_20160806_191001.jpg
        m = re.match('im_\d+_(\d{8}_\d{6}).(jpg|png)', ntpath.basename(file))
        if m:
            timestamp = datetime.strptime(m.group(1), '%Y%m%d_%H%M%S')
            return {'src': cam_config.cam_name,
                    'time': timestamp,
                    'id': Message.Image,
                    'data': f.read()}
        else:
            print('image_message: invalid image name')
            raise AlhoMessageException()


def variable_message(name, value):
    return {'src': cam_config.cam_name,
            'time': datetime.now(),
            'id': Message.Variable,
            'name': name,
            'value': value}
