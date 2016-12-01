import time
import calendar
import threading
import logging
import uuid

import CamUtilities

try:
    import RPi.GPIO as GPIO
except ImportError:
    pass

import cam_config

light_logger = logging.getLogger('LightControl')
relay_logger = logging.getLogger('Relay')
detector_logger = logging.getLogger('Detector')


class Relay:

    def __init__(self, pin, relay_callback):
        self.pin = pin
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.pin, GPIO.OUT, initial=GPIO.LOW)
        GPIO.output(self.pin, GPIO.LOW)
        self.enabled = False
        self.time_activated = 0
        self.time_deactivated = 0
        self.relay_cb = relay_callback
        self.relay_uuid = None

    def activate(self):
        if not self.enabled:
            relay_logger.info('activate')
            GPIO.output(self.pin, GPIO.HIGH)
            self.enabled = True
            self.relay_uuid = str(uuid.uuid1())
            self.time_activated = calendar.timegm(time.gmtime())
            if self.relay_cb is not None:
                self.relay_cb('on', self.relay_uuid)

    def deactivate(self):
        if self.enabled:
            relay_logger.info('deactivate')
            GPIO.output(self.pin, GPIO.LOW)
            self.enabled = False
            self.time_deactivated = calendar.timegm(time.gmtime())
            if self.relay_cb is not None:
                self.relay_cb('off',  self.relay_uuid)
            self.relay_uuid = None

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
        GPIO.add_event_detect(self.pin, GPIO.RISING, callback=cb, bouncetime=300)


class LightControl(threading.Thread):

    def __init__(self, movement_callback, lights_callback, timer):
        threading.Thread.__init__(self)
        self.detector = Detector(cam_config.gpio_detector)
        self.relay = Relay(cam_config.gpio_relay, lights_callback)
        self.duration_lights = cam_config.lights_on_time
        self.time_control = 0
        self.is_running = True
        self.timer = timer
        self.motion_alarm = CamUtilities.MotionAlarm('pir', 180.0, movement_callback)

    def run(self):
        light_logger.info('started')
        self.detector.arm(self._cb_detected)
        while self.is_running:
            self._detection(self.detector.state())
            if self._lights_on_timeout():
                self.relay.deactivate()
            time.sleep(2.0)
        GPIO.cleanup()
        light_logger.info('stopped')

    def turn_on(self):
        light_logger.info('previous control was %u s ago' % (calendar.timegm(time.gmtime()) - self.time_control))
        self.time_control = calendar.timegm(time.gmtime())
        self.relay.activate()

    def turn_off(self):
        self.relay.deactivate()

    def stop(self):
        self.is_running = False

    def _lights_grace_period(self):
        return calendar.timegm(time.gmtime()) > (self.relay.change_time() + 2.0)

    def _lights_on_timeout(self):
        action_time = max(self.relay.activated_time(), self.motion_alarm.last_detection(), self.time_control)
        light_logger.info('relay %s, motionalarm %s, control %s' % (calendar.timegm(time.gmtime()), action_time, self.time_control))
        light_logger.info('current %s vs %s' % (calendar.timegm(time.gmtime()), action_time))
        return calendar.timegm(time.gmtime()) > (action_time + self.duration_lights)

    def _detection(self, state):
        if self._lights_grace_period():
            self.motion_alarm.update(state)
            if state and self.timer.twilight_ongoing():
                self.relay.activate()
        else:
            light_logger.info('movement ignored during grace period')

    def _cb_detected(self, channel):
        self._detection(True)
