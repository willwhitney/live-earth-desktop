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
import os.path
import traceback

from datetime import datetime, timedelta
# python himawari.py
# stolen from https://gist.github.com/celoyd/39c53f824daef7d363db

# To do:
# - Librarify.
# - Clean up this paths business
# - Install script

def link_from_time(t):
    year = t.year
    day_of_year = t.timetuple().tm_yday
    utc_24h = t.hour * 100 + (t.minute // 15) * 15
    link = ("https://cdn.star.nesdis.noaa.gov/GOES16/ABI/FD/GEOCOLOR/"
            "{:04d}{:03d}{:04d}_GOES16-ABI-FD-GEOCOLOR-5424x5424.jpg").format(
            year, day_of_year, utc_24h)
    return link


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

def filename_from_url(link):
    return link.rsplit('/', 1)[-1]

# taken from "https://stackoverflow.com/questions/16694907/"
# "how-to-download-large-file-in-python-with-requests-py"

def download_file(url, path):
    r = requests.get(url, stream=True)
    size = 0
    with open(path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                size += len(chunk)
                f.write(chunk)
    if size < 10000000:
        os.system("rm {}".format(path))
    return path

def print_image_time(link):
    geocolor_index = link.find('GEOCOLOR/')
    img_time = link[geocolor_index + 16: geocolor_index + 20]
    utcmoment_naive = datetime.utcnow()
    utcmoment = utcmoment_naive.replace(tzinfo=pytz.utc)

    utcmoment = utcmoment.replace(hour=int(img_time[:2]))
    utcmoment = utcmoment.replace(minute=int(img_time[2:]))

    local_time = utcmoment.astimezone(tzlocal.get_localzone())
    print(":earth_americas: {:%I:%M}".format(local_time))

base_dir = '/Users/willw/code/live-earth-desktop/'
tmp = base_dir + 'tmp.jpg'
out_dir = base_dir + 'images/'
archive_dir = base_dir + 'old_images/'

def exists(img_name):
    for f in os.listdir(out_dir):
        if f.startswith(img_name[:11]):
            return True
    return False


def fetch_and_set():
    link = get_image_link()
    img_name = filename_from_url(link)
    save_path = out_dir + img_name

    if not exists(img_name):
        download_file(link, tmp)

        # clear out the old images in this folder so the OS picks the right one
        # os.system("mv {} {}".format(out_dir + '*', archive_dir))
        os.system("rm {}".format(out_dir + '*'))

        # now move in the new image. doing it like this because writing the image
        # takes a while, so it's better to make it a (semi-) atomic swap
        os.system("mv {} {}".format(tmp, out_dir + img_name))

t = datetime.utcnow()
for i in range(1000):
    link = link_from_time(t)
    print(link)
    try:
        download_file(link, 'video_images/{}.jpg'.format(1000 - i))
    except KeyboardInterrupt:
        raise
    except:
        traceback.print_exc()
        print("Skipping time {:%Y-%m-%d %H:%M}".format(t))
    t -= timedelta(minutes=15)

# os.system("cd video_images")
# os.system("for f in (ls); echo \"file '$f'\" >> files.txt; end")
# os.system("ffmpeg  -f concat -i files.txt -vf scale=2000:-1 -r 10 output.mp4")
# os.system("cd ..")
