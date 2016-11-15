from fractions import Fraction
import io
import os
import time
import datetime
import logging
import threading

import numpy
import cv2

import Messaging

try:
    import picamera
except ImportError:
    pass

import cam_config

camera_logger = logging.getLogger('Camera')


class Motion:

    def __init__(self):
        self.avg = None

    def feed(self, pic):
        retval = False

        # grab the raw NumPy array representing the image and initialize the timestamp and occupied/unoccupied text
        frame = pic

        # resize the frame, convert it to grayscale, and blur it
        #frame = imutils.resize(frame, width=500)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        # if the average frame is None, initialize it
        if self.avg is None:
            self.avg = gray.copy().astype("float")
            return (False, None)

        # accumulate the weighted average between the current frame and previous frames,
        # then compute the difference between the current frame and running average
        cv2.accumulateWeighted(gray, self.avg, 0.5)
        frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(self.avg))

        # threshold the delta image, dilate the thresholded image to fill
        # in holes, then find contours on thresholded image
        thresh = cv2.threshold(frameDelta, 17, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=3)
        image, contours, hierarchy = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        #cv2.imshow('delta', frameDelta)
        #cv2.imshow('threshold', thresh)
        #cv2.imshow('contour', image)

        # loop over the contours
        for c in contours:
            # if the contour is too small, ignore it
            if cv2.contourArea(c) < 5000:
                continue

            # compute the bounding box for the contour, draw it on the frame, and update the text
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            retval = True

        return (retval, frame)


class Camera(threading.Thread):

    def __init__(self, timer, movement_cb):
        threading.Thread.__init__(self)
        self.timer = timer
        self.cam = picamera.PiCamera(resolution=(1640, 1232), framerate=Fraction(1, 6))
        self.cam.annotate_background = picamera.Color('black')
        self.cam.annotate_text_size = 50
        self.movement_cb = movement_cb
        self.is_running = True
        self.motion = Motion()
        self.detected = False

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

        self.local_messaging = Messaging.LocalClientMessaging()
        self.send_pic = False

        self.timer.add_twilight_observer(self._twilight_event)
        self.timer.add_cron_job(self._cron_job, [], '*/5')

    def run(self):
        camera_logger.info('started')
        while self.is_running:
            buf = self.picture()
            img_mat = numpy.fromstring(buf, dtype='uint8')
            img = cv2.imdecode(img_mat, cv2.IMREAD_UNCHANGED)

            if img is not None:
                (m_det, m_img) = self.motion.feed(img)

                if self.detected != m_det:
                    self.detected = m_det
                    if self.detected:
                        self.movement_cb('cam', 'on')
                    else:
                        self.movement_cb('cam', 'off')

                if m_det:
                    camera_logger.info('motion detected')
                    store_thumbnail(m_img)

                if self.send_pic and m_img is not None:
                    success, buf = cv2.imencode('.jpg', m_img, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    if success:
                        self.local_messaging.send(Messaging.Message.msg_image(buf))
                    self.send_pic = False
            else:
                camera_logger.info('unable to decode')

            time.sleep(1.0)
        camera_logger.info('stopped')
        self.local_messaging.stop()

    def stop(self):
        self.is_running = False

    def picture(self):
        self.cam.annotate_text = 'Alho%d %s' % (cam_config.cam_id, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        stream = io.BytesIO()
        self.cam.capture(stream, 'jpeg', quality=20)
        stream.seek(0)
        return stream.read()

    def light_control(self, state):
        camera_logger.info('light control event: ' + state)
        if self.timer.twilight_ongoing():
            if state == 'on':
                self._day()
            else:
                self._night()
        else:
            camera_logger.info('day time. ignoring light events')

    def _twilight_event(self, event):
        camera_logger.info('twilight event: ' + event)
        if event == 'start':
            self._night()
        else:
            self._day()

    def _cron_job(self):
        self.send_pic = True
        #local_messaging = Messaging.LocalClientMessaging()
        #local_messaging.send(Messaging.Message.msg_image(self.picture()))
        #local_messaging.stop()

    def _night(self):
        camera_logger.info('night parameters')
        self.cam.exposure_mode = 'off'
        self.cam.shutter_speed = 6000000
        self.cam.iso = 800

    def _day(self):
        camera_logger.info('day parameters')
        self.cam.exposure_mode = 'auto'
        self.cam.shutter_speed = 0
        self.cam.iso = 0


def store_thumbnail(img):
    small = cv2.resize(img, (0, 0), fx=0.3, fy=0.3)
    success, buf = cv2.imencode('.jpg', small, [cv2.IMWRITE_JPEG_QUALITY, 70])

    if success:
        if not os.path.exists(cam_config.movement_image_path):
            camera_logger.info("store_thumbnail: creating path %s" % cam_config.movement_image_path)
            os.makedirs(cam_config.movement_image_path)

        filename = datetime.datetime.now().strftime('th_%Y-%m-%d_%H%M') + '.jpg'
        camera_logger.info('writing thumbnail ' + os.path.join(cam_config.movement_image_path, filename))

        with open(os.path.join(cam_config.movement_image_path, filename), 'wb') as write_f:
            write_f.write(buf)


def test():
    import glob
    import os

    motion = Motion()

    pics = glob.glob(os.path.join('..', 'testing', 'test_data2', '*.jpg'))

    for idx, pic in enumerate(pics):
        camera_logger.info('processing ' + pic)
        with open(pic, 'rb') as readf:
            pic_buf = readf.read()
            img_mat = numpy.fromstring(pic_buf, dtype='uint8')
            img = cv2.imdecode(img_mat, cv2.IMREAD_UNCHANGED)
            if img is not None:
                (m_det, m_img) = motion.feed(img)
                if m_det:
                    camera_logger.info('motion detected')
                    store_thumbnail(m_img)
            else:
                camera_logger.info('unable to decode')


if __name__ == "__main__":
    test()
