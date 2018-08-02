try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import os
import sys
import inspect
import logging
import logging.handlers
import stat

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


class LoggerWriter:
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())


def setup_logging():
    log_file = os.path.join(__location__, 'log.txt')
    #numeric_level = getattr(logging, loglevel.upper(), logging.DEBUG)

    fmt = logging.Formatter('%(levelname)8s %(asctime)s %(name)14s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

    rootlog = logging.getLogger()
    rootlog.setLevel(logging.INFO)

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    rootlog.addHandler(ch)

    fh = logging.handlers.RotatingFileHandler(log_file, maxBytes=250*1024, backupCount=4)
    fh.setFormatter(fmt)
    rootlog.addHandler(fh)

    sys.stderr = LoggerWriter(rootlog)

    try:
        os.chmod(log_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
    except OSError:
        pass



config = configparser.RawConfigParser()
config.read(os.path.join(__location__, 'cam_transport.cfg'))

image_path = config.get('SERVER', 'path_images')
variable_path = config.get('SERVER', 'path_variables')
db_host = config.get('SERVER', 'db_host')
db_user = config.get('SERVER', 'db_user')
db_pass = config.get('SERVER', 'db_pass')
if config.has_option('SERVER', 'gmail_user') and config.has_option('SERVER', 'gmail_pass') and config.has_option('SERVER', 'alarm_email'):
    gmail_user = config.get('SERVER', 'gmail_user')
    gmail_pass = config.get('SERVER', 'gmail_pass')
    alarm_email = config.get('SERVER', 'alarm_email')

cam_id = config.getint('CAMERA', 'cam_id')
upload_ip = config.get('CAMERA', 'upload_ip')
upload_port = config.getint('CAMERA', 'upload_port')
msg_port = config.getint('CAMERA', 'msg_port')
movement_image_path = config.get('CAMERA', 'movement_image_path')
movement_mask = config.get('CAMERA', 'movement_mask')
cam_type = config.get('CAMERA', 'cam_type')

lights_enabled = config.getint('LIGHTCONTROL', 'lights_enabled')
gpio_relay = config.getint('LIGHTCONTROL', 'gpio_relay')
gpio_detector = config.getint('LIGHTCONTROL', 'gpio_detector')
lights_on_time = config.getint('LIGHTCONTROL', 'lights_on_time')

loglevel = config.get('COMMON', 'loglevel')

setup_logging()

