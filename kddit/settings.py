from kddit import app

ROOT = app.config["kddit.root"]
TIMESHIFT = int(app.config["kddit.timeshift"])

PROXY_ALLOW = {
    "image": [
        "i.redd.it",
        "b.thumbs.redditmedia.com",
        "preview.redd.it",
        "i.ytimg.com",
        "www.redditstatic.com",
        "i.imgur.com"],
    "video": [
        "v.redd.it",
        "youtu.be",
        "gfycat.com"],
    "youtube": [
        "youtu.be",
        "www.youtube.com",
        "m.youtube.com"],
    "imgur": [
        "i.imgur.com"]
}

DEFAULT_OPTION = "hot"
SUBREDDIT_OPTIONS = ["hot", "new", "top", "rising", "controversial", "gilded"]
USER_OPTIONS = ["overview", "comments", "submitted", "gilded"]
EXPANDED_OPTIONS = ["top", "controversial"]
TIME_OPTIONS = {
    "hour": "now",
    "day": "today",
    "week": "this week",
    "month": "this month",
    "year": "this year",
    "all": "all time"
}

FILE_PATH = f"{ROOT}/videos/"

UA = "Mozilla/5.0 (X11; Linux x86_64; rv:81.0) Gecko/20100101 Firefox/81.0"

HEADERS = {
    "User-Agent": UA
}

YDL_OPTS = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
    'merge-output-format': 'mp4',
    'outtmpl': FILE_PATH + '%(id)s.%(ext)s'
}

