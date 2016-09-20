#!/usr/bin/env python

import Messaging
import sys
import logging

img_logger = logging.getLogger('ImgSender')


if __name__ == "__main__":
    img_logger.info('image %s' % sys.argv[1])
    local_messaging = Messaging.LocalClientMessaging()
    local_messaging.send(Messaging.Message.msg_image(sys.argv[1]))
    local_messaging.stop()
