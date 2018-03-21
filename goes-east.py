import requests
import sys
from datetime import datetime, timedelta
import pytz
from PIL import Image
# from StringIO import StringIO
import os
import logging
import uuid
from bs4 import BeautifulSoup
import time
import tzlocal

# python himawari.py
# stolen from https://gist.github.com/celoyd/39c53f824daef7d363db

# To do:
# - Librarify.
# - Clean up this paths business
# - Install script


def get_image_link():
    page = requests.get('https://www.star.nesdis.noaa.gov/GOES/GOES16_FullDisk.php')
    raw_html = page.content
    html = BeautifulSoup(raw_html, "lxml")

    # all the image links have one of these classes
    links = html.select('a.FB,a.FBNZ')
    image_link = None

    for l in links:
        link_target = l.get_attribute_list('href')[0]
        # the GEOCOLOR image is what we want
        if 'GEOCOLOR' in link_target:
            # print(link_target)
            if (link_target.endswith('10848x10848.jpg') or
                link_target.endswith('5424x5424.jpg')):
                image_link = link_target
    return image_link

# taken from "https://stackoverflow.com/questions/16694907/"
# "how-to-download-large-file-in-python-with-requests-py"

def download_file(url, path):
    # print("Downloading image from {}".format(url))
    r = requests.get(url, stream=True)
    with open(path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                # f.flush() # commented by recommendation from J.F.Sebastian
    return path

tmp = '/Users/willw/code/live-earth-desktop/tmp.jpg'
out = '/Users/willw/code/live-earth-desktop/images/desktop-{}.jpg'.format(
    str(uuid.uuid4()))

def fetch_and_set():
    link = get_image_link()
    geocolor_index = link.find('GEOCOLOR/')
    img_time = link[geocolor_index + 16: geocolor_index + 20]
    utcmoment_naive = datetime.utcnow()
    utcmoment = utcmoment_naive.replace(tzinfo=pytz.utc)

    utcmoment = utcmoment.replace(hour=int(img_time[:2]))
    utcmoment = utcmoment.replace(minute=int(img_time[2:]))

    # local_time = utcmoment.astimezone(pytz.timezone(time.tzname[time.daylight]))
    local_time = utcmoment.astimezone(tzlocal.get_localzone())

    if link is not None:
        download_file(link, tmp)

        # clear out the old images in this folder so the OS picks the right one
        os.system("rm /Users/willw/code/live-earth-desktop/images/*")

        # now move in the new image. doing it like this because writing the image
        # takes a while, so it's better to make it a (semi-) atomic swap
        os.system("mv {} {}".format(tmp, out))
    print(":earth_americas: {:%I:%M}".format(local_time))
try:
    fetch_and_set()
except:
    logging.exception('')

    # a very dirty try-at-most-twice
    try:
        fetch_and_set()
    except:
        logging.exception('')
