import os

ROOT = os.environ.get('KDDIT_ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TIMESHIFT = int(os.environ.get('KDDIT_TIMESHIFT', '3'))

PROXY_ALLOW = {
    'image': [
        'preview.redd.it',
        'i.redd.it',
        'v.redd.it',
        'b.thumbs.redditmedia.com',
        'society.kalli.st',
        'i.kalli.st',
        'preview.redd.it',
        'emoji.redditmedia.com',
        'www.redditstatic.com',
        'external-preview.redd.it',
    ],
    'video': [
        'v.redd.it',
    ],
}

DEFAULT_OPTION = 'hot'
SUBREDDIT_OPTIONS = ['hot', 'new', 'top', 'rising', 'controversial']
USER_OPTIONS = ['overview', 'comments', 'submitted']
USER_SORT = ['hot', 'new', 'top', 'controversial']
SEARCH_SORT = ['relevance', 'top', 'new', 'comments']
USER_COMMENT_SORT = ['best', 'top', 'new', 'controversial', 'old']
EXPANDED_OPTIONS = ['top', 'controversial']
TIME_OPTIONS = {
    'hour': 'now',
    'day': 'today',
    'week': 'this week',
    'month': 'this month',
    'year': 'this year',
    'all': 'all time',
}

SAFE_SUBS = ['all', 'random']

FILE_PATH = f'{ROOT}/videos/'

CLIENT_ID = os.environ.get('KDDIT_CLIENT_ID')
CLIENT_SECRET = os.environ.get('KDDIT_CLIENT_SECRET')

UA = (
    os.environ.get('KDDIT_USER_AGENT')
    or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'
)

HEADERS = {'User-Agent': UA}

YDL_OPTS = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
    'merge-output-format': 'mp4',
    'outtmpl': FILE_PATH + '%(id)s.%(ext)s',
    'external_downloader': 'aria2c',
    'external_downloader_args': {
        'aria2c': [
            '--min-split-size=1M',
            '--max-connection-per-server=16',
            '--max-concurrent-downloads=16',
            '--split=16',
        ]
    },
}

if CLIENT_SECRET and CLIENT_ID:
    URL = 'https://oauth.reddit.com'
else:
    URL = 'https://old.reddit.com'
