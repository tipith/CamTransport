import datetime
import logging
import MySQLdb
import re

import cam_config


db_logger = logging.getLogger('DataBase')


def open_db():
    return MySQLdb.connect(host=cam_config.db_host, user=cam_config.db_user, passwd=cam_config.db_pass, db="Alho")


def close_db(db):
    db.commit()
    db.close()


def store_image_meta(timestamp, src, location, size):
    now = datetime.datetime.now()
    timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    upload_time = (now - timestamp).total_seconds()
    db = open_db()
    cur = db.cursor()

    cam_id = int(re.findall('cam(\d+)', src)[0])

    db_logger.info('add picture from %i at %s, size %u, upload time %u s' % (cam_id, timestamp_str, size, upload_time))

    try:
        cur.execute("INSERT INTO Picture (Timestamp, idCamera, FileLocation, FileSize, UploadTime) \
                    VALUES (%s, %s, %s, %s, %s)",
                   (timestamp_str, cam_id, location, size, upload_time))
    except MySQLdb.IntegrityError:
        db_logger.warn('unable to add entry')
    close_db(db)
