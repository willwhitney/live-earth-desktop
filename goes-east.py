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

# python himawari.py
# stolen from https://gist.github.com/celoyd/39c53f824daef7d363db

# Fetch Himawari-8 full disks at a given zoom level and set as desktop.
# Valid zoom levels seem to be powers of 2, 1..16, and 20.
#
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

    # the image links appear on the page in order of increasing resolution,
    # so we can just take the last one
    for l in links:
        link_target = l.get_attribute_list('href')[0]
        # the GEOCOLOR image is what we want
        if 'GEOCOLOR' in link_target:
            image_link = link_target
    return image_link

# taken from "https://stackoverflow.com/questions/16694907/"
# "how-to-download-large-file-in-python-with-requests-py"

def download_file(url, path):
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
    download_file(get_image_link(), tmp)

    # clear out the old images in this folder so the OS picks the right one
    os.system("rm /Users/willw/code/live-earth-desktop/images/*")

    # now move in the new image. doing it like this because writing the image
    # takes a while, so it's better to make it a (semi-) atomic swap
    os.system("mv {} {}".format(tmp, out))

try:
    fetch_and_set()
except:
    logging.exception('')

    # a very dirty try-at-most-twice
    try:
        fetch_and_set()
    except:
        logging.exception('')
