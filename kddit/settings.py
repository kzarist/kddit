from kddit import app

ROOT = app.config["kddit.root"]
TIMESHIFT = int(app.config["kddit.timeshift"])

PROXY_ALLOW = {
    "image": [
        "preview.redd.it",
        "i.redd.it",
        "v.redd.it",
        "b.thumbs.redditmedia.com",
        "society.kalli.st",
        "i.kalli.st",
        "preview.redd.it",
        "emoji.redditmedia.com",
        "i.ytimg.com",
        "www.redditstatic.com",
        "i.imgur.com",
        "i.imgflip.com",
        "external-preview.redd.it",
        "thumbs.gfycat.com"
    ],
    "video": [
        "v.redd.it",
        "youtu.be",
        "gfycat.com",
        "redgifs.com",
        "www.redgifs.com"],
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
USER_SORT = ["hot", "new", "top", "controversial"]
SEARCH_SORT = ["relevance", "top", "new", "comments"]
EXPANDED_OPTIONS = ["top", "controversial"]
TIME_OPTIONS = {
    "hour": "now",
    "day": "today",
    "week": "this week",
    "month": "this month",
    "year": "this year",
    "all": "all time"
}

SAFE_SUBS = ["all", "random"]

FILE_PATH = f"{ROOT}/videos/"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"

HEADERS = {
    "User-Agent": UA
}

YDL_OPTS = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
    'merge-output-format': 'mp4',
    'outtmpl': FILE_PATH + '%(id)s.%(ext)s'
}

