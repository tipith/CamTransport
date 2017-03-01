import uuid
import calendar
import time
import logging

import config

motionalarm_logger = logging.getLogger('MotionAlarm')


class MotionAlarm:

    def __init__(self, source, off_timeout, callback):
        self.src = source
        self.cb = callback
        self.detected = False

        # this is used to identify messages belonging to a single movement
        # entity which consists of start and end
        self.uuid = None

        self.last_detection = 0
        self.off_timeout = off_timeout
        self.grace_end = 0

    def update(self, state):
        if state:
            if self.grace_end < calendar.timegm(time.gmtime()):
                self.last_detection = calendar.timegm(time.gmtime())
                if self.uuid is None:
                    self.uuid = str(uuid.uuid1())
                    self.cb(self.src, 'on', self.uuid)
            else:
                motionalarm_logger.info('skip alarm while grace period active, %u s left' % (self.grace_end - calendar.timegm(time.gmtime())))
        else:
            if self.uuid is not None and self._timeout_passed():
                self.cb(self.src, 'off', self.uuid)
                self.uuid = None
                self.last_detection = 0
        return self.uuid

    def latest(self):
        return self.last_detection

    def grace_period(self, duration):
        self.grace_end = calendar.timegm(time.gmtime()) + duration

    def _timeout_passed(self):
        return calendar.timegm(time.gmtime()) > (self.last_detection + self.off_timeout)


def motion_cb(src, state, uuid):
    motionalarm_logger.info('src %s state %s uuid %s' % (src, state, uuid))


if __name__ == "__main__":
    m = MotionAlarm('test', 2, motion_cb)

    m.update(False)
    time.sleep(1)

    motionalarm_logger.info('test: should activate')
    m.update(True)
    time.sleep(1)
    m.update(False)
    time.sleep(1)
    m.update(False)
    time.sleep(1)
    motionalarm_logger.info('test: should deactivate')
    m.update(False)
    time.sleep(1)

    motionalarm_logger.info('test: grace period 5 seconds')
    m.grace_period(5)
    m.update(True)
    time.sleep(1)
    m.update(True)
    time.sleep(1)
    m.update(True)
    time.sleep(1)
    m.update(True)
    time.sleep(1)
    m.update(True)
    time.sleep(1)
    m.update(True)
    time.sleep(1)

    motionalarm_logger.info('test: should activate')
    m.update(True)
    time.sleep(1)
    m.update(False)
    time.sleep(1)
    m.update(False)
    time.sleep(1)
    motionalarm_logger.info('test: should deactivate')
    m.update(False)
    time.sleep(1)
