import ephem
import datetime
import logging
import time
import calendar
from apscheduler.schedulers.background  import BackgroundScheduler

import config

time_logger = logging.getLogger('CamUtilities')
test_logger = logging.getLogger('test')


class SchedulerLogFilter(logging.Filter):
    def filter(self, record):
        return False

logging.getLogger("apscheduler.scheduler").addFilter(SchedulerLogFilter())
logging.getLogger("apscheduler.executors.default").addFilter(SchedulerLogFilter())


class Timekeeper:

    TWILIGHT_CUSTOM = '-3'
    TWILIGHT_CIVIL = '-6'
    TWILIGHT_NAUTICAL = '-12'
    TWILIGHT_ASTRONOMICAL = '-18'

    def __init__(self):
        self.salo = ephem.Observer()
        self.salo.lon = str(23.13333)
        self.salo.lat = str(60.38333)
        self.salo.elev = 20
        self.salo.pressure = 0
        self.update_date()
        self.twilight_observers = []
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self._schedule_next_twilight_event()
        time_logger.info('started scheduler')
        time_logger.info('current               %s' % self.update_date())
        time_logger.info('start twilight prev   %s' % self.twilight_start_prev())
        time_logger.info('start twilight next   %s' % self.twilight_start_next())
        time_logger.info('end twilight prev     %s' % self.twilight_end_prev())
        time_logger.info('end twilight next     %s' % self.twilight_end_next())
        time_logger.info('twilight ongoing      %s' % self.twilight_ongoing())

    def update_date(self):
        # PyEphem takes and returns only UTC times
        self.salo.date = ephem.Date(datetime.datetime.utcnow())
        date = ephem.localtime(self.salo.date)
        return date.replace(microsecond=0)

    def sunrise(self):
        self.salo.horizon = '-0:34'
        return ephem.localtime(self.salo.previous_rising(ephem.Sun()))

    def sunset(self):
        self.salo.horizon = '-0:34'
        return ephem.localtime(self.salo.next_setting(ephem.Sun()))

    def twilight_start_prev(self):
        self.salo.horizon = Timekeeper.TWILIGHT_CUSTOM
        date = ephem.localtime(self.salo.previous_setting(ephem.Sun(), use_center=True))
        return date.replace(microsecond=0)

    def twilight_start_next(self):
        self.salo.horizon = Timekeeper.TWILIGHT_CUSTOM
        date = ephem.localtime(self.salo.next_setting(ephem.Sun(), use_center=True))
        return date.replace(microsecond=0)

    def twilight_end_prev(self):
        self.salo.horizon = Timekeeper.TWILIGHT_CUSTOM
        date = ephem.localtime(self.salo.previous_rising(ephem.Sun(), use_center=True))
        return date.replace(microsecond=0)

    def twilight_end_next(self):
        self.salo.horizon = Timekeeper.TWILIGHT_CUSTOM
        date = ephem.localtime(self.salo.next_rising(ephem.Sun(), use_center=True))
        return date.replace(microsecond=0)

    def twilight_ongoing(self):
        now = self.update_date()
        if self.twilight_start_prev() < self.twilight_end_prev() < now:
            return False  # day, twilight has ended
        elif self.twilight_end_prev() < self.twilight_start_prev() < now:
            return True  # noon, twilight has started

    def add_twilight_observer(self, cb):
        self.twilight_observers.append(cb)

    def add_cron_job(self, cb, args, minute=None, second=None):
        self.scheduler.add_job(cb, 'cron', args, minute=minute, second=second)

    def _twilight_event(self, event):
        for observer in self.twilight_observers:
            observer(event)
        self._schedule_next_twilight_event()

    def _schedule_next_twilight_event(self):
        if self.twilight_ongoing():
            self.scheduler.add_job(self._twilight_event, 'date', ['end'], next_run_time=self.twilight_end_next() + datetime.timedelta(seconds=30))
        else:
            self.scheduler.add_job(self._twilight_event, 'date', ['start'], next_run_time=self.twilight_start_next() + datetime.timedelta(seconds=30))


class TimeoutManager:

    def __init__(self, duration_seconds):
        self.event_start = calendar.timegm(time.gmtime())
        self.event_duration = duration_seconds

    def restart(self, duration_seconds):
        self.event_start = calendar.timegm(time.gmtime())
        self.event_duration = duration_seconds

    def has_passed(self):
        if calendar.timegm(time.gmtime()) >= (self.event_start + self.event_duration):
            return True
        else:
            return False


def twilight_observer_test(event):
    test_logger.info('twilight event: %s' % event)


def cron_job_test(text):
    test_logger.info('cronjob: %s' % text)


if __name__ == "__main__":
    timer = Timekeeper()

    timer.add_twilight_observer(twilight_observer_test)
    timer.add_cron_job(cron_job_test, ['test param'], '*/1')

    while True:
        time.sleep(100)
