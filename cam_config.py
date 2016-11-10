try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import os
import sys
import inspect
import logging
import logging.handlers

conf_logger = logging.getLogger('Config')


# realpath() will make your script run, even if you symlink it :)
cmd_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

# use this if you want to include modules from a subfolder
cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile(inspect.currentframe()))[0], "subfolder")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def except_logger(type, value, tb):
    conf_logger.exception("Uncaught exception: {0}".format(str(value)))


def setup_logging():
    fmt = logging.Formatter('%(asctime)s %(name)14s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

    rootlog = logging.getLogger()
    rootlog.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    rootlog.addHandler(ch)

    fh = logging.handlers.RotatingFileHandler(os.path.join(__location__, 'log.txt'), maxBytes=100*1024, backupCount=10)
    fh.setFormatter(fmt)
    rootlog.addHandler(fh)

    #sys.excepthook = except_logger


config = configparser.RawConfigParser()
config.read(os.path.join(__location__, 'cam_transport.cfg'))

image_path = config.get('SERVER', 'path_images')
variable_path = config.get('SERVER', 'path_variables')
db_host = config.get('SERVER', 'db_host')
db_user = config.get('SERVER', 'db_user')
db_pass = config.get('SERVER', 'db_pass')

cam_id = config.getint('CAMERA', 'cam_id')
upload_ip = config.get('CAMERA', 'upload_ip')
upload_port = config.getint('CAMERA', 'upload_port')
msg_port = config.getint('CAMERA', 'msg_port')

gpio_relay = config.getint('LIGHTCONTROL', 'gpio_relay')
gpio_detector = config.getint('LIGHTCONTROL', 'gpio_detector')
lights_on_time = config.getint('LIGHTCONTROL', 'lights_on_time')

setup_logging()

