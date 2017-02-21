#!/usr/bin/python
import MySQLdb
import time

import config

db = MySQLdb.connect(host=config.db_host, user=config.db_user, passwd=config.db_pass, db="Alho")

cur = db.cursor()

now = time.strftime('%Y-%m-%d %H:%M:%S')

try:
    cur.execute("INSERT INTO Picture (Timestamp, idCamera) VALUES (%s, %s)", (now, 1))
except MySQLdb.IntegrityError:
    print('unable to add entry')

cur.execute("SELECT * FROM Picture")

for row in cur.fetchall():
    print row[0]

db.commit()
db.close()
