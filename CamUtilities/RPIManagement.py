import os
import re
import time
import logging


rpimanagement_logger = logging.getLogger('MotionAlarm')


def rpi_temp():
    temps = []
    for _ in range(4):
        res = os.popen('vcgencmd measure_temp').readline()
        p = re.compile('temp=([0-9.]*)')
        m = p.match(res)
        if m is not None:
            temps.append(float(m.group(1)))
            time.sleep(0.5)
        else:
            rpimanagement_logger.warn('unable to read rpi temp')
            return None
    return sum(temps) / len(temps)
