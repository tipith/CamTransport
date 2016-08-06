import os
import cam_config

def add_image(src, time, data):
    '''This function adds JPG image contents to a directory structure
    <src>/year/month/day/ with an example file name 2016-12-24_1200.jpg.

    :param src: string representing the name of data source
    :param time: python datetime object telling the image timestamp
    :param data: JPG image contents as bytes
    :return:
    '''
    file = time.strftime('%Y-%m-%d_%H%M') + '.jpg'
    path = os.path.join(cam_config.image_path, src, str(time.year), str(time.month), str(time.day))

    if not os.path.exists(path):
        print("add_image: creating path", path)
        os.makedirs(path)

    with open(os.path.join(path, file), 'wb') as f:
        f.write(data)
