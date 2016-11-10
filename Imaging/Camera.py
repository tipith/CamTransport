from fractions import Fraction
import io
import time
import datetime
import logging

import Messaging

try:
    import picamera
except ImportError:
    pass

import cam_config

camera_logger = logging.getLogger('Camera')


class Camera:

    def __init__(self, timer):
        self.timer = timer
        self.cam = picamera.PiCamera(resolution=(1640, 1232), framerate=Fraction(1, 6))
        self.cam.annotate_background = picamera.Color('black')
        self.cam.annotate_text_size = 50

        if self.timer.twilight_ongoing():
            self._night()
        else:
            self._day()

        self.cam.exposure_mode = 'auto'

        # Give the camera a good long time to set gains and measure AWB (you may wish to use fixed AWB instead)
        time.sleep(30)

        if self.timer.twilight_ongoing():
            self._night()
        else:
            self._day()

        self.timer.add_twilight_observer(self._twilight_event)
        self.timer.add_cron_job(self._cron_job, [], '*/5')

    def picture(self):
        self.cam.annotate_text = 'Alho%d %s' % (cam_config.cam_id, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        stream = io.BytesIO()
        self.cam.capture(stream, 'jpeg', quality=20)
        stream.seek(0)
        return stream.read()

    def _twilight_event(self, event):
        camera_logger.info("twilight event: " + event)
        if event == 'start':
            self._night()
        else:
            self._day()

    def _cron_job(self):
        local_messaging = Messaging.LocalClientMessaging()
        local_messaging.send(Messaging.Message.msg_image(self.picture()))
        local_messaging.stop()

    def _night(self):
        self.cam.exposure_mode = 'off'
        self.cam.shutter_speed = 6000000
        self.cam.iso = 800

    def _day(self):
        self.cam.exposure_mode = 'auto'
        self.cam.shutter_speed = 0
        self.cam.iso = 0
