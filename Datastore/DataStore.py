import os
import json
import time
import logging

import config


data_logger = logging.getLogger('DataStore')


def _store_image(path, filename, data):
    if not os.path.exists(path):
        data_logger.info("creating path %s" % path)
        os.makedirs(path)
    with open(os.path.join(path, filename), 'wb') as f:
        f.write(data)
    return os.path.join(path, filename)


def add_test_image(cam_id, timestamp, data):
    filename = 'test_cam{}_{}.jpg'.format(cam_id, timestamp.strftime('%Y-%m-%d_%H%M%S'))
    path = os.path.join(config.image_path, 'test')
    print(filename, path)
    return _store_image(path, filename, data)


def add_image(cam_id, timestamp, data):
    '''This function adds JPG image contents to a directory structure
    <src>/year/month/day/ with an example file name 2016-12-24_1200.jpg.

    :param cam_id: integer representing camera id
    :param timestamp: python datetime object telling the image timestamp
    :param data: JPG image contents as bytes
    :return:
    '''
    filename = '{}.jpg'.format(timestamp.strftime('%Y-%m-%d_%H%M'))
    path = os.path.join(config.image_path, 'images', 'cam' + str(cam_id), str(timestamp.year), str(timestamp.month), str(timestamp.day))
    return _store_image(path, filename, data)


def add_image_movement(cam_id, timestamp, uuid, data):
    '''This function adds JPG image contents to a directory structure
    /movement/<src>/uuid/ with an example file name 2016-12-24_120054.jpg.

    :param cam_id: integer representing camera id
    :param timestamp: python datetime object telling the image timestamp
    :param uuid: unique identifier string for the movement entity this image belongs
    :param data: JPG image contents as bytes
    :return:
    '''
    filename = '{}.jpg'.format(timestamp.strftime('%Y-%m-%d_%H%M'))
    path = os.path.join(config.image_path, 'movement', 'cam' + str(cam_id), uuid)
    return _store_image(path, filename, data)


def set_variable(cam_id, name, value):
    var_file = os.path.join(config.variable_path, 'vars.json')
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

    if not os.path.exists(config.variable_path):
        data_logger.info("set_variable: creating path %s" % config.variable_path)
        os.makedirs(config.variable_path)

    with open(var_file, 'w') as f:
        json.dump(data, f)


if __name__ == '__main__':
    import datetime
    config.image_path = 'C:\data'
    add_test_image(1, datetime.datetime.now(), b'12345')
