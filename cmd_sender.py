#!/usr/bin/env python

import Messaging
import sys
import logging

cmd_logger = logging.getLogger('CmdSender')


if __name__ == "__main__":
    cmd_logger.info('start sending command %s: %s' % (sys.argv[1], sys.argv[2]))
    local_messaging = Messaging.LocalClientMessaging()
    local_messaging.send(Messaging.Message.msg_command(sys.argv[1], sys.argv[2]))
    local_messaging.stop()
    cmd_logger.info('stop')