import requests
import sys
from datetime import datetime, timedelta
import pytz
from PIL import Image
import os
import logging
import uuid

try:
    from StringIO import StringIO
except ImportError:
    from io import BytesIO
# python himawari.py
# stolen from https://gist.github.com/celoyd/39c53f824daef7d363db

# Fetch Himawari-8 full disks at a given zoom level and set as desktop.
# Valid zoom levels seem to be powers of 2, 1..16, and 20.
#
# To do:
# - Librarify.
# - Clean up this paths business
# - Install script


# Tile size for this dataset:
width = 550
height = 550

tz = pytz.timezone('UTC')

# they don't get uploaded immediately. 40 minutes is a conservative delay.
time = datetime.now(tz) - timedelta(minutes=40)
print("Fetching image for time: " + datetime.strftime(time, "%Y-%m-%d %H:%M:%S"))
scale = 8

# set these appropriately for yourself
# using a UUID just so the OS sees a new filename each time it goes to change
#   the desktop image. if it's always the same name, it won't change

base = '/Users/willw/code/live-earth-desktop/'
tmp = base + 'tile_tmp.png'
tile_tmp = base + 'tmp.png'
out = base + 'images/desktop-%s.png' % (str(uuid.uuid4()))


base = 'http://himawari8.nict.go.jp/img/D531106/%sd/550' % (scale)

tiles = [[None] * scale] * scale

def pathfor(t, x, y):
    return "%s/%s/%02d/%02d/%02d%02d00_%s_%s.png" \
    % (base, t.year, t.month, t.day, t.hour, (t.minute / 10) * 10, x, y)


sess = requests.Session() # so requests will reuse the connection
png = Image.new('RGB', (width*scale, height*scale))

def download_file(url, path):
    # print("Downloading image from {}".format(url))
    r = requests.get(url, stream=True)
    with open(path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                # f.flush() # commented by recommendation from J.F.Sebastian
    return path

def fetch_and_set():
    previous_tiledata = ""
    for x in range(scale):
        for y in range(scale):
            path = pathfor(time, x, y)
            response = sess.get(path, stream=True)
            response.raw.decode_content=True
            tiledata = response.raw

            # we're just getting the "No Image" image
            # no need to retry, there just isn't data for right now
            if tiledata == previous_tiledata:
                print("No image available, quitting.")
                sys.exit(0)

            tile = Image.open(tiledata)
            png.paste(tile, (width*x, height*y, width*(x+1), height*(y+1)))

    png.save(tmp, 'PNG')

    # clear out the old images in this folder so the OS picks the right one
    os.system("rm /Users/will/code/live-earth-desktop/images/*")

    # now move in the new image. doing it like this because writing the image
    # takes a while, so it's better to make it a (semi-) atomic swap
    os.system("mv %s %s" % (tmp, out))


try:
    fetch_and_set()
except:
    logging.exception('')

    # a very dirty try-at-most-twice
    try:
        fetch_and_set()
    except:
        logging.exception('')
