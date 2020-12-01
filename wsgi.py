from bottle import request, response, abort, redirect, static_file, view
from bottle import Bottle, SimpleTemplate, BaseTemplate
import requests
import html
import os
from datetime import datetime, timedelta
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import youtube_dl
from urllib.parse import urlparse, parse_qs
import timeago


app = Bottle()
ROOT = os.path.dirname(os.path.realpath(__file__))

app.config.load_config(f"{ROOT}/app.ini")

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

DEFAULT_OPTION = "new"
SUBREDDIT_OPTIONS = ["new", "hot", "top", "rising", "controversial", "gilded"]
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
NOTHING = "<p>there doesn't seem to be anything here</p>"

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:81.0) Gecko/20100101 Firefox/81.0"
}

ydl_opts = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
    'merge-output-format': 'mp4',
    'outtmpl': FILE_PATH + '%(id)s.%(ext)s'
}


ydl = youtube_dl.YoutubeDL(ydl_opts)

header_template = SimpleTemplate(open(f"{ROOT}/templates/header.tpl").read())
post_template = SimpleTemplate(open(f"{ROOT}/templates/post.tpl").read())
video_template = SimpleTemplate(open(f"{ROOT}/templates/video.tpl").read())
image_template = SimpleTemplate(open(f"{ROOT}/templates/image.tpl").read())
comment_template = SimpleTemplate(open(f"{ROOT}/templates/comment.tpl").read())
reply_template = SimpleTemplate(open(f"{ROOT}/templates/reply.tpl").read())
gallery_template = SimpleTemplate(open(f"{ROOT}/templates/gallery.tpl").read())

BaseTemplate.defaults["unescape"] = html.unescape


def tpl(func):
    BaseTemplate.defaults[func.__name__] = func
    return func


@tpl
def xhtml():
    response.content_type = "application/xhtml+xml"


@tpl
def get_time(data):
    date = datetime.fromtimestamp(
        data["created"]) - timedelta(hours=TIMESHIFT)
    now = datetime.now()
    return timeago.format(date, now)


@tpl
def generate_subreddit_link(subreddit):
    return f'<a href="/r/{subreddit}">r/{subreddit}</a>'


def xparse(text):
    soup = BeautifulSoup(html.unescape(text), "html.parser")
    return soup.prettify()


@tpl
def generate_awards(post):
    awards = []
    if "all_awardings" in post:
        for award in post["all_awardings"]:
            awards.append(
                f'<a href="/{post["subreddit_name_prefixed"]}/gilded" class="awarding-icon" title="{html.escape(award["name"])}"><img src="/proxy/{award["icon_url"]}"/> {award["count"]} </a>')
    return "".join(awards)


def generate_subreddit_menu(o, option, subreddit):
    focus = 'class="focus" ' if option == o else ""
    sub = f"/r/{subreddit}" if subreddit else ""
    if not option and o == DEFAULT_OPTION:
        return f'<a class="focus" href="{sub}/">{o}</a>'
    else:
        return f'<a {focus}href="{sub}/{o}">{o}</a>'


def generate_user_menu(o, option, user):
    focus = 'class="focus" ' if option == o else ""
    return f'<a {focus} href="/u/{user}/{o}">{o}</a>'


def generate_before_link(data, subreddit, option, t=None):
    sub = f"/{subreddit}" if subreddit else ""
    time = f"t={t}&amp;" if t else ""
    return f'<a href="{sub}/{option}?{time}count=25&amp;before={data["data"]["before"]}">&lt;prev</a>'


def generate_after_link(data, subreddit, option, t=None):
    sub = f"/{subreddit}" if subreddit else ""
    time = f"t={t}&amp;" if t else ""
    return f'<a href="{sub}/{option}?{time}count=25&amp;after={data["data"]["after"]}">next&gt;</a>'


def generate_post(post, full=False):
    if "crosspost_parent_list" in post:
        content = generate_post(post['crosspost_parent_list'][0], True)
    elif text := post["selftext_html"]:
        content = f'<div class="text">{xparse(text)}</div>'
        if "poll_data" in post:
            content += generate_poll(post)
    elif post["is_reddit_media_domain"] and post["thumbnail"]:
        if post["is_video"]:
            content = video_template.render(post=post)
        else:
            content = image_template.render(post=post, full=full)
    elif "is_gallery" in post and post["media_metadata"]:
        content = generate_gallery(post, full=full)
    elif post["is_self"]:
        content = ""
    else:
        content = generate_content(post, full=full)
    return post_template.render(
        post=post,
        content=content,
        full=full)


def generate_poll(post):
    options = []
    tvotes = post["poll_data"]["total_vote_count"]
    for opt in post["poll_data"]["options"]:
        if "vowwte_count" in opt:
            votes = opt["vote_count"]
            options.append(
                f'<p>{opt["text"]} : {votes} votes</p><progress value="{votes}" max="{tvotes}"></progress>')
        else:
            options.append(
                f'<p><input style="display:inline;" disabled="" type="radio"/>{opt["text"]}</p>')
    return f'<div class="pool">{"".join(options)}</div>'


def generate_gallery(post, full=False):
    media = []
    for m in post["media_metadata"]:
        if "s" in post["media_metadata"][m]:
            me = post["media_metadata"][m]["s"]
            if "u" in me:
                media.append(me["u"])
            elif "gif" in me:
                media.append(me["gif"])
    return gallery_template.render(post=post, media=media, full=full)


def generate_content(post, full=False):
    url = post["url"]
    content = f'<a href="{url}">{url}</a><br/>'
    uri = urlparse(url)
    if (netloc := uri.netloc) in PROXY_ALLOW["youtube"]:
        if netloc in PROXY_ALLOW["video"]:
            content += video_template.render(url=url, thumbnail=url)
        elif "v" in (query := parse_qs(uri.query)):
            if v := query["v"]:
                u = f"https://youtu.be/{v[0]}"
                content += video_template.render(url=u, thumbnail=u)
    elif netloc in PROXY_ALLOW["video"]:
        content += video_template.render(url=url)
    elif netloc in PROXY_ALLOW["imgur"]:
        if url.endswith(".gifv"):
            content += video_template.render(url=url)
        else:
            content += image_template.render(post=post, url=url, full=full)
    return content


def get_thumbnail(url):
    try:
        with ydl:
            info = ydl.extract_info(url, download=False)
            return info["thumbnail"]
    except BaseException:
        return ""


def generate_posts(data, full=False):
    posts = []
    for children in data["data"]["children"]:
        post = children["data"]
        posts.append(generate_post(post, full))
    return "".join(posts)


def generate_mixed_content(data_list):
    content = []
    for data in data_list:
        if data["kind"] == "t1":
            content.append(generate_comment(data, True))
        elif data["kind"] == "t3":
            content.append(generate_post(data["data"], True))
    return "".join(content)


def generate_comment(data, full=False):
    text = html.unescape(data["data"]["body_html"])
    if full:
        return post_template.render(
            post=data["data"], content=text, full=full)
    else:
        replies = generate_replies(data)
        return comment_template.render(
            comment=data["data"],
            text=text,
            replies=replies)


def generate_comments(data_list):
    comments = []
    for data in data_list:
        if data['kind'] == "more":
            comments.append("<p>...</p>")
        else:
            comments.append(generate_comment(data))
    return f'<div class="comments">{"".join(comments)}</div>'


def generate_replies(data):
    replies = []
    if data['kind'] == "more":
        replies.append("<p>...</p>")
    elif data['data']['replies']:
        for children in data['data']['replies']['data']['children']:
            if children['kind'] == "more":
                replies.append("<p>...</p>")
            else:
                text = html.unescape(children["data"]["body_html"])
                replies.append(
                    reply_template.render(
                        comment=children["data"],
                        text=text,
                        replies=generate_replies(children)))
    return f'<ul>{"".join(replies)}</ul>' if replies else ""


def generate_nav(data, subreddit="", option=None, user="", t=None):
    buttons = []
    if data["data"]["before"]:
        buttons.append(
            generate_before_link(
                data,
                f"r/{subreddit}" if subreddit else f"u/{user}" if user else "",
                option or "", t))
    if data["data"]["after"]:
        buttons.append(
            generate_after_link(
                data,
                f"r/{subreddit}" if subreddit else f"u/{user}" if user else "",
                option or "", t))
    return f'<div class="nav">{" ".join(buttons)}</div>' if buttons else ""


def generate_menu(items):
    return f'<div class="menu">{" ".join(items)}</div>'


def generate_header(subreddit="", user=""):
    link = ""
    if subreddit:
        link += f'<a href="/r/{subreddit}"><span class="title link">r/{subreddit}</span></a>'
    elif (not subreddit and not user):
        link = ""
    elif user:
        link = f'<a href="/u/{user}"><span class="link">u/{user}</span></a>'
    return header_template.render(link=link)


def generate_expanded_menu(subreddit, option, t=None):
    items = [
        f'<a href="{"/r/" + subreddit if subreddit else ""}/{option}?t={i}">{v}</a>' for i,
        v in TIME_OPTIONS.items()]
    return f'<details><summary>{TIME_OPTIONS[t or "day"]}</summary>{"<br/>".join(items)}</details>'


@app.route("/", "GET")
@app.route("/<option>", "GET")
@app.route("/<option>/", "GET")
@view("index")
def index(option=""):
    if option and option not in SUBREDDIT_OPTIONS:
        return abort(404)
    query = dict(request.query)
    t = query["t"] if "t" in query else None
    r = requests.get(
        f"https://old.reddit.com/{option or DEFAULT_OPTION}.json",
        params=query,
        headers=headers)
    if r.status_code == 200:
        data = r.json()
        fmt = {}
        fmt["header"] = generate_header()
        fmt["title"] = "kddit"
        fmt["content"] = generate_menu([generate_subreddit_menu(o, option, None)
                                        for o in SUBREDDIT_OPTIONS])
        if option in EXPANDED_OPTIONS:
            fmt["content"] += generate_expanded_menu("",
                                                     option or DEFAULT_OPTION, t)
        if option == "gilded":
            fmt["content"] += generate_mixed_content(
                data["data"]["children"]) or NOTHING
        else:
            fmt["content"] += generate_posts(data, True) or NOTHING
        if nav := generate_nav(data, option=option, t=t):
            fmt["content"] += nav
        return fmt
    else:
        return abort(r.status_code)


@app.route("/r/<subreddit>", "GET")
@app.route("/r/<subreddit>/", "GET")
@app.route("/r/<subreddit>/<option>", "GET")
@app.route("/r/<subreddit>/<option>/", "GET")
@view("index")
def subreddit_page(subreddit, option=""):
    if option and option not in SUBREDDIT_OPTIONS:
        return abort(404)
    query = dict(request.query)
    t = query["t"] if "t" in query else None
    r = requests.get(
        f"https://old.reddit.com/r/{subreddit}/{option}/.json",
        params=query,
        headers=headers)
    if r.status_code == 200:
        data = r.json()
        sub = f"r/{subreddit}"
        fmt = {}
        fmt["title"] = sub
        fmt["header"] = generate_header(
            subreddit=subreddit)
        fmt["content"] = generate_menu([generate_subreddit_menu(
            o, option, subreddit) for o in SUBREDDIT_OPTIONS])
        if option in EXPANDED_OPTIONS:
            fmt["content"] += generate_expanded_menu(
                subreddit, option or DEFAULT_OPTION, t)
        if option == "gilded":
            fmt["content"] += generate_mixed_content(
                data["data"]["children"]) or NOTHING
        else:
            fmt["content"] += generate_posts(data) or NOTHING
        if nav := generate_nav(data, subreddit=subreddit, option=option, t=t):
            fmt["content"] += nav
        return fmt
    else:
        return abort(r.status_code)


@app.route("/r/<subreddit>/comments/<post_id>/<path>", "GET")
@app.route("/r/<subreddit>/comments/<post_id>/<path>/", "GET")
@app.route("/r/<subreddit>/comments/<post_id>/<path>/<comment_id>", "GET")
@app.route("/r/<subreddit>/comments/<post_id>/<path>/<comment_id>/", "GET")
@view("index")
def subreddit(subreddit, post_id, path, comment_id=""):
    r = requests.get(
        f"https://old.reddit.com/r/{subreddit}/comments/{post_id}/{path}/{comment_id}.json",
        params=dict(
            request.query),
        headers=headers)
    if r.status_code == 200:
        data = r.json()
        post = data[0]["data"]["children"][0]["data"]
        comments = data[1]["data"]["children"]
        fmt = {}
        fmt["title"] = post["title"]
        fmt["content"] = generate_post(post) + generate_comments(comments)
        fmt["header"] = generate_header(subreddit=subreddit)
        return fmt
    else:
        return abort(r.status_code)


@app.route("/u/<user>/", "GET")
@app.route("/user/<user>/", "GET")
@app.route("/u/<user>", "GET")
@app.route("/user/<user>", "GET")
@app.route("/u/<user>/<option>", "GET")
@app.route("/user/<user>/<option>", "GET")
@app.route("/u/<user>/<option>/", "GET")
@app.route("/user/<user>/<option>/", "GET")
@view("index")
def user_page(user, option="overview"):
    if option and option not in USER_OPTIONS:
        return abort(404)
    query = dict(request.query)
    t = query["t"] if "t" in query else None
    r = requests.get(
        f"https://old.reddit.com/user/{user}/{option}/.json",
        query),
        headers=headers)
    if r.status_code == 200:
        data = r.json()
        fmt = {}
        fmt["title"] = f"{option} by {user}"
        fmt["content"] = generate_menu([generate_user_menu(o, option, user)
                                        for o in USER_OPTIONS])
        fmt["content"] += generate_mixed_content(data["data"]["children"])
        fmt["header"] = generate_header(user=user)
        if nav := generate_nav(data, user=user, option=option, t=t):
            fmt["content"] += nav
        return fmt
    else:
        return abort(r.status_code)


@app.route("/static/<file>")
@app.route("/static/<file>/")
def static(file):
    return static_file(file, root=f"{ROOT}/static")


@app.route("/video/<url:path>")
def video_proxy(url):
    uri = urlparse(url)
    if (netloc := uri.netloc) in PROXY_ALLOW["video"]:
        with ydl:
            result = ydl.extract_info(url, download=True)
            return static_file(
                f'{result["id"]}.{result["ext"]}',
                root=FILE_PATH)
    elif netloc in PROXY_ALLOW["imgur"]:
        iurl = url.replace(".gifv", ".mp4")
        r = requests.get(iurl, headers=headers)
        if r.status_code == 200:
            response.set_header("content-type", r.headers["content-type"])
            return r.content
        else:
            return abort(r.status_code)
    else:
        return abort(403)


@app.route("/proxy/<url:path>")
def proxy(url):
    uri = urlparse(url)
    if (netloc :=
            uri.netloc) not in PROXY_ALLOW["image"] + PROXY_ALLOW["video"]:
        return abort(403)
    if netloc in PROXY_ALLOW["video"]:
        u = get_thumbnail(url)
    else:
        u = url
    r = requests.get(f"{u}", params=dict(request.query), headers=headers)
    if r.status_code == 200:
        response.set_header("content-type", r.headers["content-type"])
        return r.content
    else:
        return abort(r.status_code)


@app.error(401)
@app.error(403)
@app.error(404)
@app.error(405)
@app.error(406)
@app.error(451)
@app.error(500)
@app.error(503)
@view("index")
def error_redirect(error):
    fmt = {}
    fmt["title"] = f"{error.status}!"
    fmt["content"] = f"<br/><br/><br/><br/><br/><br/><h1>{error.status}!\n</h1>"
    fmt["header"] = header_template.render()
    return fmt


application = app
