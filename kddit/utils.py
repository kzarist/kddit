from datetime import datetime, timedelta
from kddit.settings import HEADERS, TIMESHIFT, YDL_OPTS
import timeago
import re
import requests
import youtube_dl

ydl = youtube_dl.YoutubeDL(YDL_OPTS)

def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])

def get_time(timestamp):
    date = datetime.fromtimestamp(
        timestamp) - timedelta(hours=TIMESHIFT)
    now = datetime.now()
    return timeago.format(date, now)

def get_thumbnail(url):
    try:
        with ydl:
            info = ydl.extract_info(url, download=False)
            return info["thumbnail"]
    except:
        return ""

preview_re = re.compile("https://preview.redd.it/")

def req(url, params=None):
    return requests.get(url, params=params, headers=HEADERS)

def success(r):
    return r.status_code == 200

def builder(*args):
    obj = ()
    args = list(args)
    last = args.pop()
    args.reverse()
    for arg in args:
        if obj:
            obj = (arg(obj),)
        else:
            obj = (arg(last),)
    return obj

#def tuplefy(*args):
#    return (*args,)

def tuplefy(func):
    def inner(*args, **kwargs):
        result = func(*args, **kwargs)
        return (result,)
    return inner
