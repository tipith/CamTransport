
import time
import Messaging
import sys
from datetime import timedelta


def strfdelta(tdelta, fmt):
    d = {"days": tdelta.days}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    return fmt.format(**d)


def get_uptime():
    uptime_string = 'none'
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            uptime_string = strfdelta(timedelta(seconds = uptime_seconds), "{days} paivaa {hours}:{minutes}:{seconds}")
    except IOError:
        pass
    return uptime_string


def publish_image(image):
    start = time.clock()
    pub = Messaging.MessagePublisher()
    pub.publish(Messaging.image_message(image))
    #pub.publish(Messaging.variable_message('upload time', time.clock() - start))
    pub.publish(Messaging.variable_message('uptime', get_uptime()))
    pub.close()


if __name__ == "__main__":
    publish_image(sys.argv[1])
