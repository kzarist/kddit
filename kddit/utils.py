from datetime import datetime, timedelta
from kddit.settings import HEADERS, TIMESHIFT, YDL_OPTS
from kddit.settings import SUBREDDIT_OPTIONS, SAFE_SUBS, USER_OPTIONS
import timeago
import re
import requests
import youtube_dl
from glom import glom as g
from glom import Coalesce
from bs4 import BeautifulSoup
from html import unescape
from bottle import request, abort

ydl = youtube_dl.YoutubeDL(YDL_OPTS)

def get_query():
    return dict(request.query)

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

def replace_tag(bs_tag, html_tag):
    html_tag = html_tag[0] if isinstance(html_tag, tuple) else html_tag
    soup = BeautifulSoup(html_tag.render(), "html.parser")
    bs_tag.replace_with(soup)

def get_metadata(data, name):
    output = g(data, Coalesce(f"media_metadata.{name}.s.u", f"media_metadata.{name}.s.gif"), default=None)
    return unescape(output) if output else None


external_preview_re = re.compile("https://external-preview.redd.it/")
preview_re = re.compile("https://preview.redd.it/")
processing_re = re.compile("Processing img (.*)...")
video_re = re.compile("https://reddit.com/link/.*/video/(.*)/player")

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

def tuplefy(func):
    def inner(*args, **kwargs):
        result = func(*args, **kwargs)
        return (result,)
    return inner


def get_subreddit_url():
    sub = request.url_args.get("subreddit")
    return f"/r/{sub}" if sub else ""

def get_subreddit():
    sub = request.url_args.get("subreddit")
    return f"r/{sub}" if sub else ""

def get_option():
    option = request.url_args.get("option")
    return option

def verify_subreddit_option():
    option = get_option()
    if option and option not in SUBREDDIT_OPTIONS:
        return abort(404)

def verify_user_option():
    option = get_option()
    if option and option not in USER_OPTIONS:
        return abort(404)

def nsfw_mode(subreddit):
    return not subreddit or subreddit in SAFE_SUBS
