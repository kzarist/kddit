from bottle import request, response, abort, redirect, static_file, view
from bottle import Bottle, SimpleTemplate, BaseTemplate
import requests
import html
import os
from datetime import datetime, timezone
from urllib.parse import urlparse
from bs4 import BeautifulSoup

app = Bottle()

PROXY_ALLOW = ["i.redd.it", "v.redd.it", "b.thumbs.redditmedia.com"]
DEFAULT_OPTION = "new"
SUBREDDIT_OPTIONS = ["hot", "new", "rising", "controversial", "top"]
USER_OPTIONS = ["overview", "comments", "submitted"]


root = os.path.dirname(os.path.realpath(__file__))
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:81.0) Gecko/20100101 Firefox/81.0"
}

header_template = SimpleTemplate(open(f"{root}/templates/header.tpl").read())
post_template = SimpleTemplate(open(f"{root}/templates/post.tpl").read())
video_template = SimpleTemplate(open(f"{root}/templates/video.tpl").read())
image_template = SimpleTemplate(open(f"{root}/templates/image.tpl").read())
comment_template = SimpleTemplate(open(f"{root}/templates/comment.tpl").read())
reply_template = SimpleTemplate(open(f"{root}/templates/reply.tpl").read())
single_comment_template = SimpleTemplate(
    open(f"{root}/templates/single_comment.tpl").read())


def tpl(func):
    BaseTemplate.defaults[func.__name__] = func
    return func


@tpl
def xhtml():
    response.content_type = "application/xhtml+xml"


@tpl
def get_created(data):
    return datetime.fromtimestamp(
        data["created"],
        timezone.utc).strftime("%d/%m/%y %H:%M")


@tpl
def generate_subreddit_link(subreddit):
    return f'<a href="/r/{subreddit}"><span class="title link">r/{subreddit}</span></a>'


def xparse(text):
    soup = BeautifulSoup(html.unescape(text), "html.parser")
    return soup.prettify()


def generate_subreddit_menu(o, option, subreddit):
    focus = " focus" if option == o else ""
    sub = f"/r/{subreddit}" if subreddit else ""
    return f'<a class="menu{focus}" href="{sub}/{o}">{o}</a>'


def generate_user_menu(o, option, user):
    focus = " focus" if option == o else ""
    return f'<a class="menu {focus}" href="/u/{user}/{o}">{o}</a>'


def generate_before_link(data, subreddit, option):
    sub = f"/{subreddit}" if subreddit else ""
    return f'<a href="{sub}/{option}?count=25&amp;before={data["data"]["before"]}">&lt;prev</a>'


def generate_after_link(data, subreddit, option):
    sub = f"/{subreddit}" if subreddit else ""
    return f'<a href="{sub}/{option}?count=25&amp;after={data["data"]["after"]}">next&gt;</a>'


def generate_post(post, full=False):
    if "crosspost_parent_list" in post:
        content = generate_post(post['crosspost_parent_list'][0], True)
    elif text := post["selftext_html"]:
        content = f'<div class="text">{xparse(text)}</div>'
    elif post["is_reddit_media_domain"]:
        if post["is_video"]:
            content = video_template.render(post=post)
        else:
            content = image_template.render(post=post, full=full)
    elif post["is_self"]:
        content = ""
    else:
        url = post["url"]
        content = f'<a href="{url}">{url}</a>'
    return post_template.render(
        post=post,
        content=content,
        full=full)


def generate_posts(data, full=False):
    posts = []
    for children in data["data"]["children"]:
        post = children["data"]
        posts.append(generate_post(post, full))
    return "".join(posts)


def generate_nav(data, subreddit="", option=None):
    nav = []
    if data["data"]["before"]:
        nav.append(generate_before_link(data, subreddit, option))
    if data["data"]["after"]:
        nav.append(generate_after_link(data, subreddit, option))
    return f'<div class="nav">view more: {" | ".join(nav)}</div>' if nav else ""


def generate_user_content(data_list):
    content = []
    for data in data_list:
        if data["kind"] == "t1":
            content.append(generate_comment(data, True))
        elif data["kind"] == "t3":
            content.append(generate_post(data["data"], True))
        else:
            print(data["kind"])
    return "".join(content)


def generate_comment(data, full=False):
    text = html.unescape(data["data"]["body_html"])
    created = get_created(data["data"])
    if full:
        return single_comment_template.render(
            created=created, comment=data["data"], text=text)
    else:
        replies = generate_replies(data)
        return comment_template.render(
            comment=data["data"],
            created=created,
            text=text,
            replies=replies)


def generate_comments(data_list):
    comments = []
    for data in data_list:
        if data['kind'] == "more":
            comments.append("...")
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
                created = get_created(children["data"])
                replies.append(
                    reply_template.render(
                        comment=children["data"],
                        created=created,
                        text=text,
                        replies=generate_replies(children)))
    return f'<ul>{"".join(replies)}</ul>' if replies else ""


def generate_subreddit_header(subreddit="", option=""):
    menu = ""
    link = ""
    if subreddit:
        link += generate_subreddit_link(subreddit)
    if option:
        menu += " | ".join(generate_subreddit_menu(o, option, subreddit)
                           for o in SUBREDDIT_OPTIONS)
    return header_template.render(link=link, menu=menu)


def generate_user_header(user, option=""):
    menu = ""
    link = f'<a href="/u/{user}"><span class="title link">u/{user}</span></a>'
    if option:
        menu += " | ".join(generate_user_menu(o, option, user)
                           for o in USER_OPTIONS)
    return header_template.render(link=link, menu=menu)


@app.route("/", "GET")
@app.route("/<option>", "GET")
@view("index")
def index(option=""):
    if option and option not in SUBREDDIT_OPTIONS:
        return abort(404)
    r = requests.get(
        f"https://old.reddit.com/{option}.json",
        params=dict(
            request.query),
        headers=headers)
    if r.status_code == 200:
        data = r.json()
        fmt = {}
        fmt["header"] = generate_subreddit_header(
            option=option or DEFAULT_OPTION)
        fmt["title"] = "kddit"
        fmt["content"] = generate_posts(data, True)
        if nav := generate_nav(data, option=option):
            fmt["nav"] = nav
        return fmt
    else:
        return abort(r.status_code)


@app.route("/r/<subreddit>", "GET")
@app.route("/r/<subreddit>/", "GET")
@app.route("/r/<subreddit>/<option>", "GET")
@app.route("/r/<subreddit>/<option>/", "GET")
@view("index")
def subreddit(subreddit, option=""):
    if option and option not in SUBREDDIT_OPTIONS:
        return abort(404)
    r = requests.get(
        f"https://old.reddit.com/r/{subreddit}/{option}/.json",
        params=dict(
            request.query),
        headers=headers)
    if r.status_code == 200:
        data = r.json()
        sub = f"r/{subreddit}"
        fmt = {}
        fmt["title"] = sub
        fmt["header"] = generate_subreddit_header(
            subreddit, option=option or DEFAULT_OPTION)
        fmt["content"] = generate_posts(
            data)
        if nav := generate_nav(data, sub, option):
            fmt["nav"] = nav
        return fmt
    else:
        return abort(r.status_code)


@app.route("/r/<subreddit>/comments/<post_id>/<path>/", "GET")
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
        fmt["header"] = generate_subreddit_header(subreddit)
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
    r = requests.get(
        f"https://old.reddit.com/user/{user}/{option}/.json",
        params=dict(
            request.query),
        headers=headers)
    if r.status_code == 200:
        data = r.json()
        fmt = {}
        fmt["title"] = f"{option} by {user}"
        fmt["content"] = generate_user_content(data["data"]["children"])
        fmt["header"] = generate_user_header(user, option)
        return fmt
    else:
        return abort(r.status_code)


@app.route("/static/<file>")
def static(file):
    return static_file(file, root=f"{root}/static")


@app.route("/proxy/<url:path>")
def proxy(url):
    uri = urlparse(url)
    if uri.netloc not in PROXY_ALLOW:
        return abort(403)
    r = requests.get(f"{url}", params=dict(request.query), headers=headers)
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
