from fractions import Fraction
import io
import time
import datetime
import logging
import threading

import numpy
import cv2

from CamUtilities import TimeoutManager, MotionAlarm, remove_oldest_files
import Messaging
import config

try:
    import picamera
except ImportError:
    pass

# testing related imports
import glob
import os
from itertools import chain
try:
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
except ImportError:
    pass


camera_logger = logging.getLogger('Camera')


class ImageTools:

    @staticmethod
    def im_reader(filename):
        camera_logger.info('reading file: ' + filename)
        try:
            with open(filename, 'rb') as readf:
                pic_buf = readf.read()
                img_mat = numpy.fromstring(pic_buf, dtype='uint8')
                img = cv2.imdecode(img_mat, cv2.IMREAD_UNCHANGED)
                if img is not None:
                    return img
                else:
                    camera_logger.warn('unable to decode')
                    return None
        except IOError:
            camera_logger.warn('unable to open file: ' + filename)
            return None

    @staticmethod
    def create_mask(img_filename):
        mask_img = ImageTools.im_reader(img_filename)
        if mask_img is not None:
            img2gray = cv2.cvtColor(mask_img, cv2.COLOR_BGR2GRAY)
            ret, mask = cv2.threshold(img2gray, 10, 255, cv2.THRESH_BINARY)
            return mask
        return None

    @staticmethod
    def calculate_average(img):
        avg_channels = cv2.mean(img)
        return sum(avg_channels) / 3

    @staticmethod
    def apply_mask(img, mask):
        if mask is not None and img.shape == mask.shape:
            return cv2.bitwise_and(img, img, mask=mask)
        return img

    @staticmethod
    def calculate_histograms(img, mask):
        # Calculate histogram with mask and without mask, check third argument for mask
        hist_full = cv2.calcHist([img], [0], None, [256], [0, 256])
        hist_mask = cv2.calcHist([img], [0], mask, [256], [0, 256])
        return [hist_full, hist_mask]

    @staticmethod
    def generate_jpeg(img):
        return cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 100])

    @staticmethod
    def generate_jpeg_thumbnail(img):
        thumbnail = cv2.resize(img, (0, 0), fx=0.3, fy=0.3)
        return cv2.imencode('.jpg', thumbnail, [cv2.IMWRITE_JPEG_QUALITY, 75])

    @staticmethod
    def store_movement(jpeg_buf):
        if not os.path.exists(config.movement_image_path):
            camera_logger.info("store_thumbnail: creating path %s" % config.movement_image_path)
            os.makedirs(config.movement_image_path)

        filename = datetime.datetime.now().strftime('th_%Y-%m-%d_%H%M%S') + '.jpg'
        camera_logger.debug('writing thumbnail ' + os.path.join(config.movement_image_path, filename))

        with open(os.path.join(config.movement_image_path, filename), 'wb') as write_f:
            write_f.write(jpeg_buf)

    @staticmethod
    def annotate_image(img, text):
        height, width, channels = img.shape
        overlay = img.copy()

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.4
        thickness = 2
        size = cv2.getTextSize(text, font, font_scale, thickness)

        offset_y = 30
        margin = 7
        upper_left = (width // 2 - size[0][0] // 2 - margin, offset_y - margin)
        lower_right = (width // 2 + size[0][0] // 2 + margin, size[0][1] + offset_y + margin)
        color = (0, 0, 0)
        cv2.rectangle(overlay, upper_left, lower_right, color, thickness=-1)

        alpha = 0.5
        cv2.addWeighted(src1=overlay, alpha=alpha, src2=img, beta=1 - alpha, gamma=0, dst=img)

        color = (255, 255, 255)
        pos = (width // 2 - size[0][0] // 2, size[0][1] + offset_y)
        cv2.putText(img, text, pos, font, font_scale, color, thickness)


class Motion:

    def __init__(self):
        self.avg = None

    def feed(self, pic, mask):
        retval = False

        # grab the raw NumPy array representing the image and initialize the timestamp and occupied/unoccupied text
        frame = pic.copy()

        # apply motion mask
        frame = ImageTools.apply_mask(frame, mask)

        # convert it to grayscale and blur
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        # if the average frame is None, initialize it
        if self.avg is None:
            self.avg = gray.copy().astype("float")
            return False, None

        # accumulate the running average
        cv2.accumulateWeighted(gray, self.avg, 0.3)

        # compare new frame to running average
        frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(self.avg))

        # threshold the delta image, dilate the thresholded image to fill
        # in holes, then find contours on thresholded image
        thresh = cv2.threshold(frameDelta, 40, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=3)
        image, contours, hierarchy = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        width, height, chs = frame.shape
        min_size = width*height // 400
        max_size = width*height // 3

        # loop over the contours
        for c in contours:
            # if the contour is too small or big, ignore it
            if min_size < cv2.contourArea(c) < max_size:
                # compute the bounding box for the contour, draw it on the frame, and update the text
                (x, y, w, h) = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                retval = True

        return retval, frame


class DummyCam:

    def __init__(self):
        self._exposure_mode = 'auto'

    def autotune_gains(self, is_night):
        camera_logger.info('autotuned, is_night={}'.format(is_night))

    @property
    def exposure_mode(self):
        return self._exposure_mode

    @exposure_mode.setter
    def exposure_mode(self, val):
        camera_logger.info('exposure set to {}'.format(val))
        self._exposure_mode = val

    @property
    def picture(self):
        with open(os.path.join('..', 'data', 'images', 'cam1', '2017', '6', '2', '2017-06-02_0010.jpg'), 'rb') as f:
            return f.read()

    @property
    def night(self):
        return True

    @night.setter
    def night(self, val):
        camera_logger.info('night set to {}'.format(val))

    def tune_shutter(self, img):
        pass


class USBCam:

    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, 1920)
        self.cap.set(4, 1080)
        self._exposure_mode = 'auto'

    def autotune_gains(self, is_night):
        camera_logger.info('autotuned, is_night={}'.format(is_night))

    @property
    def exposure_mode(self):
        return self._exposure_mode

    @exposure_mode.setter
    def exposure_mode(self, val):
        camera_logger.info('exposure set to {}'.format(val))
        self._exposure_mode = val

    @property
    def picture(self):
        ret_val, img = self.cap.read()
        return img

    @property
    def night(self):
        return True

    @night.setter
    def night(self, val):
        camera_logger.info('night set to {}'.format(val))

    def tune_shutter(self, img):
        pass


class PiCam:

    def __init__(self):
        self.cam = picamera.PiCamera(resolution=(1640, 1232), framerate=Fraction(1, 6))
        picamera.PiCamera.CAPTURE_TIMEOUT = 90000

    def autotune_gains(self, is_night):
        self.night = is_night
        self.exposure_mode = 'auto'
        if is_night:
            time.sleep(30)  # Give the camera a good long time to set gains and measure AWB
        self.night = is_night

    @property
    def exposure_mode(self):
        return self.cam.exposure_mode

    @exposure_mode.setter
    def exposure_mode(self, val):
        self.cam.exposure_mode = val

    @property
    def picture(self):
        stream = io.BytesIO()
        self.cam.capture(stream, 'jpeg', quality=20)
        stream.seek(0)
        img_mat = numpy.fromstring(stream.read(), dtype='uint8')
        return cv2.imdecode(img_mat, cv2.IMREAD_UNCHANGED)

    @property
    def night(self):
        return self.exposure_mode == 'off'

    @night.setter
    def night(self, val):
        if val:
            camera_logger.info('night parameters')
            self.exposure_mode = 'off'
            self.cam.shutter_speed = 100000
            self.cam.iso = 800
        else:
            camera_logger.info('day parameters')
            self.exposure_mode = 'auto'
            self.cam.shutter_speed = 0
            self.cam.iso = 0

    def tune_shutter(self, img):
        if self.cam.exposure_mode != 'auto':
            # 10 ms steps, max value 12 sec
            large_step_factor = 20
            tune_value = 10000
            max_value = 12000000
            change = 0

            avg = ImageTools.calculate_average(img)
            current = self.cam.shutter_speed

            if avg < 20 and current < (max_value - large_step_factor * tune_value):
                change = large_step_factor * tune_value
            elif avg < 50 and current < (max_value - tune_value):
                change = tune_value
            elif avg > 130 and (current - large_step_factor * tune_value) > 0:
                change = -large_step_factor * tune_value
            elif avg > 80 and (current - tune_value) > 0:
                change = -tune_value

            camera_logger.debug(
                'pixel avg %u, current shutter %i ms, change %i ms' % (avg, current / 1000, change / 1000))
            self.cam.shutter_speed = current + change


class Camera(threading.Thread):

    def __init__(self, timer, movement_cb, cam, test_mode=False):
        threading.Thread.__init__(self)
        self.timer = timer
        self.cam = cam
        self.cam.autotune_gains(is_night=self.timer.twilight_ongoing())
        self.motion = Motion()
        self.is_running = True

        self.livestream_timeout = TimeoutManager(0)
        self.mask = ImageTools.create_mask(config.movement_mask)

        self.local_messaging = Messaging.LocalClient()
        self.send_pic = False

        self.timer.add_twilight_observer(self._twilight_event)
        self.timer.add_cron_job(Camera._movement_img_truncate_cron_job, [], minute='*/59')

        if test_mode:
            self.timer.add_cron_job(self._cron_job, [], second='*/30')
            self.motion_alarm = MotionAlarm('cam', 180.0, None)
            self.periodical_cls = Messaging.ImageMessageTest
        else:
            self.timer.add_cron_job(self._cron_job, [], minute='*/5')
            self.motion_alarm = MotionAlarm('cam', 180.0, movement_cb)
            self.periodical_cls = Messaging.ImageMessagePeriodical

    def run(self):
        camera_logger.info('started')
        while self.is_running:
            img = self.cam.picture

            if img is not None:
                if self.timer.twilight_ongoing():
                    self.cam.tune_shutter(img)

                # new image is returned and original is left untouched
                m_det, m_img = self.motion.feed(img, self.mask)
                m_uuid = self.motion_alarm.update(m_det)

                text = 'Alho{} {}'.format(config.cam_id, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

                if self.send_pic or not self.livestream_timeout.has_passed():
                    ImageTools.annotate_image(img, text)
                if m_det:
                    ImageTools.annotate_image(m_img, text)

                if m_det and m_uuid is not None:
                    success, m_img_tb = ImageTools.generate_jpeg_thumbnail(m_img)
                    if success:
                        ImageTools.store_movement(ImageTools.generate_jpeg(m_img)[1])
                        self.local_messaging.send(Messaging.ImageMessageMovement(m_img_tb, m_uuid))

                if self.send_pic:
                    success, buf = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 75])
                    if success:
                        self.local_messaging.send(self.periodical_cls(buf))
                    self.send_pic = False

                if not self.livestream_timeout.has_passed():
                    success, img_tb = ImageTools.generate_jpeg_thumbnail(img)
                    if success:
                        self.local_messaging.send(Messaging.ImageMessageLive(img_tb))
            else:
                camera_logger.info('unable to decode')
        camera_logger.info('stopped')

    def stop(self):
        self.is_running = False

    def light_control(self, state):
        camera_logger.info('light control event: ' + state)
        if self.timer.twilight_ongoing():
            self.cam.night = (state != 'on')
        else:
            camera_logger.info('day time. ignoring light events')

    def livestream(self, duration):
        self.livestream_timeout.restart(duration)

    def _twilight_event(self, event):
        camera_logger.info('twilight event: ' + event)
        self.motion_alarm.grace_period(20.0)
        self.cam.night = (event == 'start')

    def _cron_job(self):
        camera_logger.info('pic send requested')
        self.send_pic = True

    @staticmethod
    def _movement_img_truncate_cron_job():
        remove_oldest_files(config.movement_image_path, 5*1024*1024*1024, 4*1024*1024*1024)


def test():
    motion = Motion()

    mask = ImageTools.create_mask(config.movement_mask)
    pics = glob.glob(os.path.join('..', 'testing', 'test_data2', '*.jpg'))

    for idx, pic in enumerate(pics):
        camera_logger.info('processing ' + pic)
        with open(pic, 'rb') as readf:
            pic_buf = readf.read()
            img_mat = numpy.fromstring(pic_buf, dtype='uint8')
            img = cv2.imdecode(img_mat, cv2.IMREAD_UNCHANGED)
            if img is not None:
                (m_det, m_img) = motion.feed(img, mask)
                if m_det:
                    camera_logger.info('motion detected')
                    #ImageTools.store_movement(m_img)
                    time.sleep(1.0)
            else:
                camera_logger.info('unable to decode')


class TestAnim:

    def __init__(self):
        self.pics = iter(glob.glob(os.path.join('..', 'testing', 'test_data2', '*.jpg')))
        self.fig = plt.figure()
        self.pic = plt.imshow(ImageTools.im_reader(self.pics), vmin=0, vmax=255)

    def anim(self):
        ani = animation.FuncAnimation(self.fig, self._update_img, interval=5, blit=True)
        plt.show()

    def _update_img(self, *args):
        self.pic.set_array(ImageTools.im_reader(self.pics))
        return [self.pic]


class TestAnim2:

    def __init__(self):
        self.pics = iter(glob.glob(os.path.join('..', 'testing', 'test_data2', '*.jpg')))

        self.mask = ImageTools.create_mask(config.movement_mask)

        self.avg = []

        self.fig, ax = plt.subplots(2, 3)

        pic = ImageTools.im_reader(self.pics.next())
        masked = ImageTools.apply_mask(pic, self.mask)
        hist = ImageTools.calculate_histograms(pic, self.mask)
        self.avg.append(ImageTools.calculate_average(pic))

        self.im = []
        self.im.append(ax[0, 0].imshow(pic))
        self.im.append(ax[1, 0].imshow(masked))

        self.im.append(ax[1, 1].plot(hist[0])[0])
        self.im.append(ax[1, 1].plot(hist[1])[0])
        self.im.append(ax[0, 2].plot(self.avg)[0])

        for plot in chain.from_iterable(zip(*ax)):
            plot.tick_params(axis='both', which='both', bottom='off', top='off', labelbottom='off', labelleft='on')
            plot.set_autoscale_on(True)

    def _update_img(self, *args):
        pic = ImageTools.im_reader(self.pics.next())
        masked = ImageTools.apply_mask(pic, self.mask)
        hist = ImageTools.calculate_histograms(pic, self.mask)
        self.avg.append(ImageTools.calculate_average(pic))

        self.im[0].set_array(pic)
        self.im[1].set_array(masked)
        self.im[2].set_ydata(hist[0])
        self.im[3].set_ydata(hist[1])
        self.im[4].set_data(range(len(self.avg)), self.avg)

        axes = self.fig.get_axes()
        axes[1].relim()
        axes[1].autoscale()
        axes[2].relim()
        axes[2].autoscale()
        axes[4].relim()
        axes[4].autoscale()
        axes[5].relim()
        axes[5].autoscale()

        return self.im

    def anim(self):
        ani = animation.FuncAnimation(self.fig, self._update_img, interval=1, blit=False)
        plt.show()


def test_dummycam():
    def on_movement(detector, state, uuid):
        print(detector, state, uuid)

    import CamUtilities
    cam = DummyCam()
    timer = CamUtilities.Timekeeper()
    c = Camera(timer, on_movement, cam, test_mode=True)
    c.start()
    time.sleep(10)
    c.stop()


if __name__ == "__main__":
    #test = TestAnim2()
    #test.anim()
    #test()
    test_dummycam()
