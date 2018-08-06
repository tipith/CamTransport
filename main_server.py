#!/usr/bin/python

import Messaging
import Datastore
import config
import gmail

import json
import time
import calendar
import datetime
import logging

main_logger = logging.getLogger('Main')
email_alert = {'last': 0}
server_messaging = Messaging.WanServer()
local_messaging = Messaging.LocalServer()


def on_image(msg):
    if msg['type'] == Messaging.ImageMessage.TYPE_PERIODICAL:
        filename = Datastore.add_image(msg['src'], msg['time'], msg['data'])
        Datastore.db_store_image(msg['src'], msg['time'], filename, len(msg['data']))
    elif msg['type'] == Messaging.ImageMessage.TYPE_MOVEMENT:
        filename = Datastore.add_image_movement(msg['src'], msg['time'], msg['uuid'], msg['data'])
        Datastore.db_store_image_movement(msg['src'], msg['time'], filename, msg['uuid'], len(msg['data']))
        # send only the first picture belonging to a group of pictures from a source. uuid is the group identifier
        if msg['src'] not in email_alert or email_alert[msg['src']] != msg['uuid']:
            email_alert[msg['src']] = msg['uuid']

            if not (datetime.time(8, 0) < datetime.datetime.now().time() < datetime.time(15, 0)):
                if calendar.timegm(time.gmtime()) > email_alert['last'] + 3600:
                    email_alert['last'] = calendar.timegm(time.gmtime())
                    gmail.send('Activity from cam %i' % msg['src'], 'See attachment.', filename)
                else:
                    main_logger.info('skip email alert due to grace period, last alert %u s ago' %
                                     (calendar.timegm(time.gmtime()) - email_alert['last']))
            else:
                main_logger.info('skip email alert during day')
    elif msg['type'] == Messaging.ImageMessage.TYPE_TEST:
        filename = Datastore.add_test_image(msg['src'], msg['time'], msg['data'])
        main_logger.info('wrote {}'.format(filename))


def on_variable(msg):
    if msg['name'] == 'temperature':
        Datastore.db_store_temperature(msg['src'], msg['time'], msg['value'])
    else:
        Datastore.set_variable(msg['src'], msg['name'], msg['value'])


def on_movement(msg):
    Datastore.db_store_movement(msg['src'], msg['time'], msg['detector'], msg['state'], msg['uuid'])


def on_text(msg):
    try:
        u = json.loads(msg['text'])
        if 'dbm' in u:
            Datastore.db_store_uplink(msg['time'], u['dbm'], u['ip'], u['up'], u['rat'], u['sig'], u['net'])
    except json.JSONDecodeError:
        pass


def on_light_control(msg):
    Datastore.db_store_light_control(msg['src'], msg['time'], msg['state'], msg['uuid'])


def cam_on_any(msg):
    Datastore.set_variable(msg['src'], 'uptime', msg['uptime'])
    main_logger.info('cameras -> local %s' % Messaging.Message.msg_info(msg))
    local_messaging.send(msg, serialize=False)


def local_on_any(msg):
    main_logger.info('local -> cameras %s' % Messaging.Message.msg_info(msg))
    server_messaging.send(msg, serialize=False)


def local_on_command(msg):
    if msg['command'] == 'ping':
        local_messaging.send(Messaging.CommandMessage('pong', msg['parameter']))


if __name__ == "__main__":
    server_messaging.start()
    server_messaging.install(Messaging.Message.Image, on_image)
    server_messaging.install(Messaging.Message.Variable, on_variable)
    server_messaging.install(Messaging.Message.MovementEvent, on_movement)
    server_messaging.install(Messaging.Message.Text, on_text)
    server_messaging.install(Messaging.Message.LightControlEvent, on_light_control)
    server_messaging.install('*', cam_on_any)

    local_messaging.start()
    local_messaging.install('*', local_on_any)
    local_messaging.install(Messaging.Message.Command, local_on_command)

    try:
        while True:
            time.sleep(1.0)
    finally:
        server_messaging.stop()
        local_messaging.stop()
