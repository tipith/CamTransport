import time
import Messaging
import sys


def publish_image(image):
    start = time.clock()
    pub = Messaging.MessagePublisher()
    time.sleep(0.1)
    pub.publish(Messaging.image_message(image))
    pub.publish(Messaging.variable_message('upload time', time.clock() - start))
    pub.close()


if __name__ == "__main__":
    publish_image(sys.argv[1])
