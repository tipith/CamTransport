from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from datetime import datetime, timedelta
import os
import glob

from main_client import publish_image

if __name__ == '__main__':

    path = 'perf_testing'
    fontname = "arial.ttf"
    fontsize = 30
    time_string = "example@gmail.com"
    time_curr = datetime(2015, 12, 24, 10, 00, 00)

    if not os.path.exists(path):
        print("add_image: creating path", path)
        os.makedirs(path)

    for i in range(1000):
        time_curr = time_curr + timedelta(minutes=5)
        file_string = time_curr.strftime('%Y%m%d_%H%M%S')
        image_string = time_curr.strftime('%Y-%m-%d %H:%M:%S')
        filename = 'im_%u_%s.jpg' % (i, file_string)

        img_file = os.path.join(path, filename)

        if not os.path.isfile(img_file):
            colorText = "black"
            colorOutline = "red"
            colorBackground = "white"

            font = ImageFont.truetype(fontname, fontsize)
            width, height = (400, 100)
            img = Image.new('RGB', (width+4, height+4), colorBackground)
            d = ImageDraw.Draw(img)
            d.text((20, height/2 - 15), image_string, fill=colorText, font=font)
            d.rectangle((0, 0, width+3, height+3), outline=colorOutline)

            print("add_image: saving file", img_file)
            img.save(img_file)

    pics = glob.glob(path + '/*.jpg')

    for pic in pics:
        publish_image(pic)
