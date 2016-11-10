import os
import json
import time
import logging

import cam_config


data_logger = logging.getLogger('DataStore')


def add_image(cam_id, timestamp, data):
    '''This function adds JPG image contents to a directory structure
    <src>/year/month/day/ with an example file name 2016-12-24_1200.jpg.

    :param cam_id: integer representing camera id
    :param timestamp: python datetime object telling the image timestamp
    :param data: JPG image contents as bytes
    :return:
    '''
    filename = timestamp.strftime('%Y-%m-%d_%H%M') + '.jpg'
    path = os.path.join(cam_config.image_path, 'cam' + str(cam_id), str(timestamp.year), str(timestamp.month), str(timestamp.day))

    if not os.path.exists(path):
        data_logger.info("add_image: creating path %s" % path)
        os.makedirs(path)

    with open(os.path.join(path, filename), 'wb') as f:
        f.write(data)

    return os.path.join(path, filename)


def set_variable(cam_id, name, value):
    var_file = os.path.join(cam_config.variable_path, 'vars.json')
    data = {}

    try:
        with open(var_file, 'r') as f:
            data = json.loads(f.read())
    except IOError:
        data_logger.warn('no variables file')
    except ValueError:
        data_logger.warn('invalid data file')

    cam_name = 'cam' + str(cam_id)

    data.setdefault(cam_name, {})
    data[cam_name][name] = value
    data[cam_name]["last_heard"] = time.strftime("%Y-%m-%d %H:%M:%S")

    if not os.path.exists(cam_config.variable_path):
        data_logger.info("set_variable: creating path %s" % cam_config.variable_path)
        os.makedirs(cam_config.variable_path)

    with open(var_file, 'w') as f:
        json.dump(data, f)
