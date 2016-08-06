try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import os, sys, inspect

# realpath() will make your script run, even if you symlink it :)
cmd_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

# use this if you want to include modules from a subfolder
cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile(inspect.currentframe()))[0], "subfolder")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)

config = configparser.RawConfigParser()
config.read('cam_transport.cfg')

image_path = config.get('SUBSCRIBER', 'path_images')
variable_path = config.get('SUBSCRIBER', 'path_variables')

cam_name = config.get('PUBLISHER', 'cam_name')
upload_ip = config.get('PUBLISHER', 'upload_ip')
upload_port = config.getint('PUBLISHER', 'upload_port')

print("configuration loaded")