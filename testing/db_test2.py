import Datastore
import datetime

now = datetime.datetime.now()

Datastore.store_image_meta(now, 1, '/data/image.jpg', 12312)