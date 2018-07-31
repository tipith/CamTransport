import logging
import MySQLdb
import MySQLdb.cursors
from pathlib import Path


import config

db_logger = logging.getLogger('database')


class DBConnection:
    def __init__(self):
        self.db = None

    def __enter__(self):
        self.db = MySQLdb.connect(host='koivu',  #config.db_host,
                                  user=config.db_user,
                                  passwd=config.db_pass,
                                  db="ToriScraper",
                                  cursorclass=MySQLdb.cursors.DictCursor)
        return self.db.cursor()

    def __exit__(self, type, value, traceback):
        self.db.commit()
        self.db.close()


def get_pics(p):
    with DBConnection() as cursor:
        cursor.execute("SELECT * FROM Alho.Picture WHERE HOUR(Timestamp) = %s and MINUTE(Timestamp) = %s and idCamera = %s;",
                       [p['hour'], p['min'], p['cam']])
        rows = cursor.fetchall()
    return rows


def copy_pics(p, pics):
    from shutil import copy2

    target_p = Path('cam{cam}_{hour}'.format(**p))
    if not target_p.exists():
        target_p.mkdir()
    already_contains = [f.name for f in target_p.glob('*')]
    for p in pics:
        src_p = Path(p)
        if src_p.exists() and src_p.name not in already_contains:
                copy2(src_p, target_p)
                print('{} copied'.format(src_p))
    return target_p


def create_gif(p):
    import imageio
    with imageio.get_writer(p / 'movie.gif', mode='I') as writer:
        for f in p.glob('*'):
            image = imageio.imread(f)
            writer.append_data(image)


if __name__ == '__main__':
    params = {'cam': 1, 'hour': 15, 'min': 0}
    pics = get_pics(params)
    print('got {} pics'.format(len(pics)))
    picpath = copy_pics(params, [p['FileLocation'] for p in pics])
    create_gif(picpath)
