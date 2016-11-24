import datetime
import logging
import MySQLdb

import cam_config


db_logger = logging.getLogger('DataBase')


def open_db():
    return MySQLdb.connect(host=cam_config.db_host, user=cam_config.db_user, passwd=cam_config.db_pass, db="Alho")


def close_db(db):
    db.commit()
    db.close()


def db_store_image(cam_id, timestamp, location, size):
    timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    upload_time = (datetime.datetime.now() - timestamp).total_seconds()
    db = open_db()
    cur = db.cursor()
    try:
        cur.execute("INSERT INTO Picture (Timestamp, idCamera, FileLocation, FileSize, UploadTime) \
                     VALUES (%s, %s, %s, %s, %s)", (timestamp_str, cam_id, location, size, upload_time))
    except MySQLdb.IntegrityError:
        db_logger.warn('unable to add entry')
    close_db(db)


def db_store_movement(cam_id, timestamp, detector, event, uuid):
    timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    db = open_db()
    cur = db.cursor()
    try:
        if event == 'on':
                cur.execute("INSERT INTO Movement (idCamera, StartTimestamp, Detector, Event, UUID) \
                             VALUES (%s, %s, %s, %s, %s)", (cam_id, timestamp_str, detector, event, uuid))
        elif event == 'off':
            cur.execute("UPDATE Movement SET EndTimestamp = '%s' WHERE UUID = '%s'" % (timestamp_str, uuid))
    except MySQLdb.IntegrityError:
        db_logger.warn('unable to add entry')
    close_db(db)


def db_store_light_control(cam_id, timestamp, event):
    timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    db = open_db()
    cur = db.cursor()
    try:
        cur.execute("INSERT INTO LightControl (idCamera, Timestamp, Event) \
                     VALUES (%s, %s, %s)", (cam_id, timestamp_str, event))
    except MySQLdb.IntegrityError:
        db_logger.warn('unable to add entry')
    close_db(db)


def db_store_image_movement(cam_id, timestamp, location, uuid, size):
    timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    upload_time = (datetime.datetime.now() - timestamp).total_seconds()
    db = open_db()
    cur = db.cursor()
    try:
        cur.execute("INSERT INTO PictureMovement (Timestamp, idCamera, FileLocation, FileSize, UUID, UploadTime) \
                     VALUES (%s, %s, %s, %s, %s, %s)", (timestamp_str, cam_id, location, size, uuid, upload_time))
    except MySQLdb.IntegrityError:
        db_logger.warn('unable to add entry')
    close_db(db)
