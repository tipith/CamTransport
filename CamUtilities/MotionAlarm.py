import uuid
import calendar
import time


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

    def update(self, state):
        if state:
            self.last_detection = calendar.timegm(time.gmtime())
            if self.uuid is None:
                self.uuid = str(uuid.uuid1())
                self.cb(self.src, 'on', self.uuid)
        else:
            if self.uuid is not None and self._timeout_passed():
                self.cb(self.src, 'off', self.uuid)
                self.uuid = None
                self.last_detection = 0
        return self.uuid

    def latest(self):
        return self.last_detection

    def _timeout_passed(self):
        return calendar.timegm(time.gmtime()) > (self.last_detection + self.off_timeout)
