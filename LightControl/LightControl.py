import time
import datetime
import calendar
import threading
import logging
import ephem

try:
    import RPi.GPIO as GPIO
except ImportError:
    pass

import cam_config

light_logger = logging.getLogger('LightControl')
relay_logger = logging.getLogger('Relay')
detector_logger = logging.getLogger('Detector')
alarmtimer_logger = logging.getLogger('AlarmTimer')
test_logger = logging.getLogger('test')


class AlarmTimer:

    def __init__(self):
        self.salo = ephem.Observer()
        self.salo.lon = str(23.13333)
        self.salo.lat = str(60.38333)
        self.salo.elev = 20
        self.salo.pressure = 0
        self.salo.horizon = '-6'  # -6 = civil twilight, -12 = nautical, -18 = astronomical
        self.update_date()

    def update_date(self):
        # PyEphem takes and returns only UTC times
        self.salo.date = ephem.Date(datetime.datetime.utcnow())
        return ephem.localtime(self.salo.date)

    def sunrise(self):
        self.salo.horizon = '-0:34'
        return ephem.localtime(self.salo.previous_rising(ephem.Sun()))

    def sunset(self):
        self.salo.horizon = '-0:34'
        return ephem.localtime(self.salo.next_setting(ephem.Sun()))

    def twilight_start_prev(self):
        self.salo.horizon = '-6'
        return ephem.localtime(self.salo.previous_setting(ephem.Sun(), use_center=True))

    def twilight_start_next(self):
        self.salo.horizon = '-6'
        return ephem.localtime(self.salo.next_setting(ephem.Sun(), use_center=True))

    def twilight_end_prev(self):
        self.salo.horizon = '-6'
        return ephem.localtime(self.salo.previous_rising(ephem.Sun(), use_center=True))

    def twilight_end_next(self):
        self.salo.horizon = '-6'
        return ephem.localtime(self.salo.next_rising(ephem.Sun(), use_center=True))

    def twilight_ongoing(self):
        now = self.update_date()
        if self.twilight_start_prev() < self.twilight_end_prev() < now:
            return False  # day, twilight has ended
        elif self.twilight_end_prev() < self.twilight_start_prev() < now:
            return True  # noon, twilight has started


class Relay:

    def __init__(self, pin):
        self.pin = pin
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.pin, GPIO.OUT, initial=GPIO.LOW)
        GPIO.output(self.pin, GPIO.LOW)
        self.enabled = False

    def activate(self):
        if not self.enabled:
            relay_logger.info("activate")
            GPIO.output(self.pin, GPIO.HIGH)
            self.enabled = True

    def deactivate(self):
        if self.enabled:
            relay_logger.info("deactivate")
            GPIO.output(self.pin, GPIO.LOW)
            self.enabled = False


class Detector:

    def __init__(self, pin):
        self.pin = pin
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def state(self):
        return GPIO.input(self.pin) == 1

    def wait(self):
        GPIO.wait_for_edge(self.pin, GPIO.RISING)

    def arm(self, cb):
        detector_logger.info("adding callback")
        GPIO.add_event_detect(self.pin, GPIO.RISING, callback=cb, bouncetime=300)


class LightControl(threading.Thread):

    def __init__(self, movement_callback):
        threading.Thread.__init__(self)
        self.detector = Detector(cam_config.gpio_detector)
        self.relay = Relay(cam_config.gpio_relay)
        self.light_on_time = cam_config.lights_on_time
        self.last_detected = 0
        self.is_running = True
        self.cb = movement_callback
        self.is_detected = False
        self.timer = AlarmTimer()

    def run(self):
        light_logger.info("started")

        self.detector.arm(self._detected)
        while self.is_running:
            if self._timeout():
                if self.is_detected:
                    self.is_detected = False
                    self.cb('off')
                self.turn_off()
            time.sleep(1.0)

        GPIO.cleanup()
        light_logger.info("stopped")

    def turn_on(self):
        self.last_detected = calendar.timegm(time.gmtime())
        self.relay.activate()

    def turn_off(self):
        self.last_detected = 0
        self.relay.deactivate()

    def stop(self):
        self.is_running = False

    def _timeout(self):
        return calendar.timegm(time.gmtime()) > (self.last_detected + self.light_on_time)

    def _detected(self, channel):
        if not self.is_detected:
            self.is_detected = True
            self.cb('on')
        # only enable light if it is dark
        if self.timer.twilight_ongoing():
            light_logger.info("night time, turning on lights")
            self.turn_on()
        else:
            light_logger.info("day time, not turning on lights")


if __name__ == "__main__":
    timer = AlarmTimer()


    test_logger.info('current               %s' % timer.update_date())
    test_logger.info('start twilight prev   %s' % timer.twilight_start_prev())
    test_logger.info('start twilight next   %s' % timer.twilight_start_next())
    test_logger.info('end twilight prev     %s' % timer.twilight_end_prev())
    test_logger.info('end twilight next     %s' % timer.twilight_end_next())
    test_logger.info('twilight ongoing      %s' % timer.twilight_ongoing())
