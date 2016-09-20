import RPi.GPIO as GPIO
import time
import calendar
import threading
import logging

import cam_config

light_logger = logging.getLogger('LightControl')
relay_logger = logging.getLogger('Relay')
detector_logger = logging.getLogger('Detector')


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

    def __init__(self):
        threading.Thread.__init__(self)
        self.detector = Detector(cam_config.gpio_detector)
        self.relay = Relay(cam_config.gpio_relay)
        self.light_on_time = cam_config.lights_on_time
        self.last_detected = 0
        self.is_running = True

    def run(self):
        light_logger.info("started")

        self.detector.arm(self._detected)
        while self.is_running:
            if self._timeout():
                self.relay.deactivate()
            time.sleep(1.0)

        GPIO.cleanup()
        light_logger.info("stopped")

    def turn_on(self):
        light_logger.info('lights on')
        self.last_detected = calendar.timegm(time.gmtime())
        self.relay.activate()

    def turn_off(self):
        light_logger.info('lights off')
        self.last_detected = 0
        self.relay.deactivate()

    def stop(self):
        self.is_running = False

    def _timeout(self):
        return calendar.timegm(time.gmtime()) > (self.last_detected + self.light_on_time)

    def _detected(self, channel):
        self.last_detected = calendar.timegm(time.gmtime())
        self.relay.activate()

