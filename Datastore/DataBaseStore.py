import datetime, logging, re, traceback

import MySQLdb

import config


db_logger = logging.getLogger('DataBase')


class DBConnection:
    def __init__(self):
        self.db = None

    def __enter__(self):
        self.db = MySQLdb.connect(host=config.db_host, user=config.db_user, passwd=config.db_pass, db='Alho')
        return self.db.cursor()

    def __exit__(self, type, value, traceback):
        self.db.commit()
        self.db.close()


def _dt2str(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def _dtdiff2now(dt):
    return (datetime.datetime.now() - dt).total_seconds()


def _insert_vals(sql, vals):
    with DBConnection() as cur:
        try:
            cur.execute(sql, vals)
        except MySQLdb.IntegrityError:
            db_logger.error(traceback.format_exc())


def db_store_image(cam_id, timestamp, location, size):
    sql = "INSERT INTO Picture (Timestamp, idCamera, FileLocation, FileSize, UploadTime) VALUES (%s, %s, %s, %s, %s)"
    vals = (_dt2str(timestamp), cam_id, location, size, _dtdiff2now(timestamp))
    _insert_vals(sql, vals)


def db_store_movement(cam_id, timestamp, detector, event, uuid):
    if event == 'on':
        sql = "INSERT INTO Movement (idCamera, StartTimestamp, Detector, UUID) VALUES (%s, %s, %s, %s)"
        vals = (cam_id, _dt2str(timestamp), detector, uuid)
    else:
        sql = "UPDATE Movement SET EndTimestamp = '%s' WHERE UUID = '%s'"
        vals = (_dt2str(timestamp), uuid)
    _insert_vals(sql, vals)


def db_store_light_control(cam_id, timestamp, event, uuid):
    if event == 'on':
        sql = "INSERT INTO LightControl (idCamera, StartTimestamp, UUID) VALUES (%s, %s, %s)"
        vals = (cam_id, _dt2str(timestamp), uuid)
    else:
        sql = "UPDATE LightControl SET EndTimestamp = '%s' WHERE UUID = '%s'"
        vals = (_dt2str(timestamp), uuid)
    _insert_vals(sql, vals)


def db_store_image_movement(cam_id, timestamp, location, uuid, size):
    sql = "INSERT INTO PictureMovement (Timestamp, idCamera, FileLocation, FileSize, UUID, UploadTime) " \
          "VALUES (%s, %s, %s, %s, %s, %s)"
    vals = (_dt2str(timestamp), cam_id, location, size, uuid, _dtdiff2now(timestamp))
    _insert_vals(sql, vals)


def db_store_temperature(cam_id, timestamp, temperature):
    sql = "INSERT INTO RpiTemperature (Timestamp, idCamera, Temperature) VALUES (%s, %s, %s)"
    vals = (_dt2str(timestamp), cam_id, temperature)
    _insert_vals(sql, vals)


def db_store_uplink(timestamp, dbm, ip, up, rat, sig, net):
    regex = re.compile(r'(?P<h>\d+):(?P<m>\d+):(?P<s>\d+)')
    m = regex.match(up)
    if m:
        up_secs = int(m['h'])*3600 + int(m['m'])*60 + int(m['s'])
    else:
        up_secs = 0
    sql = "INSERT INTO RpiTemperature " \
          "(Timestamp, UptimeSeconds, RadioAccessTechnology, IPAddress, NetworkName, SignalStrength, SignalQualityPercent) " \
          "VALUES (%s, %s, %s %s, %s %s)"
    vals = (_dt2str(timestamp), up_secs, rat, ip, net, dbm, sig)
    _insert_vals(sql, vals)


def test():
    global _insert_vals
    _insert_vals = lambda sql, vals: print('{}\n -> {}'.format(sql, vals))

    timestamp = datetime.datetime.now()
    db_store_uplink(timestamp, dbm='28', ip='12.23.2.12', up='1:1:1', rat='3G', sig='90%', net='DNA')
    db_store_image(cam_id=1, timestamp=timestamp, location='/data', size=123312)


if __name__ == '__main__':
    test()
