import time
import calendar
import threading
import logging
import Timekeeper

try:
    import RPi.GPIO as GPIO
except ImportError:
    pass

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
        self.time_activated = 0
        self.time_deactivated = 0

    def activate(self):
        if not self.enabled:
            relay_logger.info("activate")
            GPIO.output(self.pin, GPIO.HIGH)
            self.enabled = True
            self.time_activated = calendar.timegm(time.gmtime())

    def deactivate(self):
        if self.enabled:
            relay_logger.info("deactivate")
            GPIO.output(self.pin, GPIO.LOW)
            self.enabled = False
            self.time_deactivated = calendar.timegm(time.gmtime())

    def change_time(self):
        return max(self.time_activated, self.time_deactivated)

    def activated_time(self):
        return self.time_activated

    def deactivated_time(self):
        return self.time_deactivated


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

    def __init__(self, movement_callback, timer):
        threading.Thread.__init__(self)
        self.detector = Detector(cam_config.gpio_detector)
        self.relay = Relay(cam_config.gpio_relay)
        self.duration_lights = cam_config.lights_on_time
        self.duration_movement = 30
        self.time_movement = 0
        self.time_control = 0
        self.cb = movement_callback
        self.is_running = True
        self.is_detected = False
        self.timer = timer

    def run(self):
        light_logger.info("started")
        self.detector.arm(self._detected)
        while self.is_running:
            if self.detector.state():
                self._detected(0)
            if self._lights_on_timeout():
                self.relay.deactivate()
            if self._movement_timeout():
                self._detection_off()
            time.sleep(2.0)
        GPIO.cleanup()
        light_logger.info("stopped")

    def turn_on(self):
        light_logger.info("previous control was %u s ago" % (calendar.timegm(time.gmtime()) - self.time_control))
        self.time_control = calendar.timegm(time.gmtime())
        self.relay.activate()

    def turn_off(self):
        self.relay.deactivate()

    def stop(self):
        self.is_running = False

    def _detection_on(self):
        self.time_movement = calendar.timegm(time.gmtime())
        if not self.is_detected:
            self.is_detected = True
            self.cb('on')

    def _detection_off(self):
        if self.is_detected:
            self.is_detected = False
            self.cb('off')

    def _lights_grace_period(self):
        return calendar.timegm(time.gmtime()) > (self.relay.change_time() + 2.0)

    def _lights_on_timeout(self):
        control_or_movement_time = max(self.relay.activated_time(), self.time_movement, self.time_control)
        return calendar.timegm(time.gmtime()) > (control_or_movement_time + self.duration_lights)

    def _movement_timeout(self):
        return calendar.timegm(time.gmtime()) > (self.time_movement + self.duration_movement)

    def _detected(self, channel):
        # movement detector gives false alarms when lights are turned on/off
        if self._lights_grace_period():
            self._detection_on()
            if self.timer.twilight_ongoing():
                self.relay.activate()
        else:
            light_logger.info("movement ignored during grace period")

