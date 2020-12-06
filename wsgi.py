from bottle import request, response, abort, redirect, static_file, view
from bottle import Bottle
import requests
from html import unescape, escape
import os
from datetime import datetime, timedelta
from urllib.parse import urlparse
import youtube_dl
from urllib.parse import urlparse, parse_qs
import timeago
import pyhtml as html


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

DEFAULT_OPTION = "hot"
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
NOTHING = html.p("there doesn't seem to be anything here")
UA = "Mozilla/5.0 (X11; Linux x86_64; rv:81.0) Gecko/20100101 Firefox/81.0"

headers = {
    "User-Agent": UA
}

ydl_opts = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
    'merge-output-format': 'mp4',
    'outtmpl': FILE_PATH + '%(id)s.%(ext)s'
}


ydl = youtube_dl.YoutubeDL(ydl_opts)


def generate_video(post=None, url=None, thumbnail=None):
    video = ()
    if post:
        url = post["media"]["reddit_video"]["dash_url"]
    if thumbnail:
        video += (html.video(Class="media",
                             poster=f"/proxy/{thumbnail}",
                             controls="",
                             preload="none",
                             src=f"/video/{url}"),
                  )
    else:
        video += (html.video(Class="media", controls="",
                             preload="metadata", src=f"/video/{url}"),)
    return video


def generate_image(post, full=False, url=None):
    url = url or post["url"]
    img = html.img(Class="media", src=f'/proxy/{url}')
    if post["over_18"] and full:
        image = (html.label(html.input_(Class="nsfw", type="checkbox"), img),)
    else:
        image = (img,)
    return image


def generate_gallery(post, full):
    media = ()
    for m in post["media_metadata"]:
        if "s" in post["media_metadata"][m]:
            me = post["media_metadata"][m]["s"]
            if "u" in me:
                l = me["u"]
            elif "gif" in me:
                l = me["gif"]
            media += generate_image(post, full, unescape(l))
    mask = html.div(Class="css-slider-mask")
    ul = html.ul(Class="css-slider with-responsive-images")
    slider = html.li(Class="slide", tabindex=1)
    outer = html.span(Class="slide-outer")
    inner = html.span(Class="slide-inner")
    gfx = html.span(Class="slide-gfx")(media)
    gallery = mask(
        ul(
            slider(
                outer(
                    inner(
                        gfx(me)
                    )
                )
            ) for me in media
        )
    )

    return gallery


def generate_page(title, header, content):
    page = html.html(
        html.head(
            html.title(title),
            html.link(
                rel="stylesheet",
                type="text/css",
                href="/static/style.css"),
            html.link(
                rel="stylesheet",
                type="text/css",
                href="/static/slider.css"),
            html.link(
                rel="icon",
                href="/static/favicon.svg"),
            html.meta(
                name="viewport",
                content="width=device-width, initial-scale=1.0")),
        html.body(
            html.div(
                Class="header")(header),
            html.div(
                Class="content")(content)))
    return page


class progress(html.Tag):
    self_closing = False


class details(html.Tag):
    self_closing = False


class summary(html.Tag):
    self_closing = False


def get_time(data):
    date = datetime.fromtimestamp(
        data["created"]) - timedelta(hours=TIMESHIFT)
    now = datetime.now()
    return timeago.format(date, now)


def generate_subreddit_link(subreddit):
    return html.a(href=f"/r/{subreddit}")(f"r/{subreddit}")


def xparse(text):
    return (html.Safe(unescape(text)),)


def generate_awards(post):
    awards = ()
    if "all_awardings" in post:
        for award in post["all_awardings"]:
            cin = (html.img(src=f'/proxy/{award["icon_url"]}'),)
            if (count := award["count"]) > 1:
                cin += (count,)
            link = f'{post["subreddit_name_prefixed"]}/gilded'
            awards += (html.a(href=link, Class="awarding-icon",
                              title=escape(award["name"]))(cin),)
    return awards


def generate_subreddit_menu(option, subreddit, domain):
    links = ()
    for o in SUBREDDIT_OPTIONS:
        focus = option == o or (not option and o == DEFAULT_OPTION)
        sub = f"/r/{subreddit}" if subreddit else f"/domain/{domain}" if domain else ""
        link = f"{sub}/{o}"
        if focus:
            a = html.a(href=link, Class="focus")(o)
        else:
            a = html.a(href=link)(o)
        links += (a,)
    return links


def generate_user_menu(option, user):
    links = ()
    for o in USER_OPTIONS:
        focus = option == o or (not option and o == default_option)
        link = f"/u/{user}/{o}"
        if focus:
            a = html.a(href=link, Class="focus")(o)
        else:
            a = html.a(href=link)(o)
        links += (a,)
    return links


def generate_before_link(data, subreddit, option, t=None):
    sub = f"/{subreddit}" if subreddit else ""
    time = f"t={t}&" if t else ""
    link = f'{sub}/{option}?{time}count=25&before={data["data"]["before"]}'
    a = html.a(href=link)("<prev")
    return a


def generate_after_link(data, target, option, t=None):
    sub = f"/{target}" if target else ""
    time = f"t={t}&" if t else ""
    link = f'{sub}/{option}?{time}count=25&after={data["data"]["after"]}'
    a = html.a(href=link)("next>")
    return a


def generate_post(post, full=False):
    if "crosspost_parent_list" in post:
        content = generate_post(post['crosspost_parent_list'][0], True)
    elif text := post["selftext_html"]:
        content = xparse(text)
        if "poll_data" in post:
            content = generate_poll(post)
    elif post["is_reddit_media_domain"] and post["thumbnail"]:
        content = (html.a(href=post["url"])(post["url"]), html.br())
        if post["is_video"]:
            content += (generate_video(post),)
        else:
            content += (generate_image(post, full=full),)
    elif "is_gallery" in post and post["media_metadata"]:
        content = (html.a(href=post["url"])(post["url"]), html.br())
        content += (generate_gallery(post, full=full),)
    elif post["is_self"]:
        content = ""
    else:
        content = generate_content(post, full=full)
    title = post["title"] if "title" in post else post["link_title"]
    flair = post["link_flair_text"] if "link_flair_text" in post else None
    header = ()
    if full:
        header += (generate_subreddit_link(post["subreddit"]),)
    header += (html.a(href=post["permalink"])(html.b(title)),)
    if flair:
        header += (html.span(Class="flair")(flair),)
    author = html.a(href=f'/u/{post["author"]}')(f'u/{post["author"]}')
    header += (html.br(), author, get_time(post),
               html.br(), generate_awards(post))
    return html.div(
        Class="post")(
        html.div(
            Class="sub-header")(header),
        html.hr(),
        html.div(
                Class="post-content")(content))


def generate_poll(post):
    options = ()
    tvotes = post["poll_data"]["total_vote_count"]
    for opt in post["poll_data"]["options"]:
        if "vote_count" in opt:
            votes = opt["vote_count"]
            cin = (
                html.p(f'{opt["text"]} : {votes}'),
                progress(
                    value=votes,
                    max=tvotes))
            options += cin
        else:
            cin = (html.p(html.input_(disabled="", type="radio"), opt["text"]))
            options += (cin,)
    div = html.div(Class="poll")(options)
    return div


def generate_content(post, full=False):
    url = post["url"]
    content = (html.a(href=url)(url), html.br())
    uri = urlparse(url)
    if (netloc := uri.netloc) in PROXY_ALLOW["youtube"]:
        if netloc in PROXY_ALLOW["video"]:
            content += (generate_video(url=url, thumbnail=url),)
        elif "v" in (query := parse_qs(uri.query)):
            if v := query["v"]:
                u = f"https://youtu.be/{v[0]}"
                content += (generate_video(url=u, thumbnail=u),)
    elif netloc in PROXY_ALLOW["video"]:
        content += (generate_video(url=url),)
    elif netloc in PROXY_ALLOW["imgur"]:
        if url.endswith(".gifv"):
            content += (generate_video(url=url),)
        else:
            content += generate_image(post=post, full=full)
    return content


def get_thumbnail(url):
    try:
        with ydl:
            info = ydl.extract_info(url, download=False)
            return info["thumbnail"]
    except BaseException:
        return ""


def generate_posts(data, full=False):
    posts = ()
    for children in data["data"]["children"]:
        post = children["data"]
        posts += (generate_post(post, full),)
    return posts


def generate_mixed_content(data_list):
    content = ()
    for data in data_list:
        if data["kind"] == "t1":
            content += (generate_comment(data, True),)
        elif data["kind"] == "t3":
            content += (generate_post(data["data"], True),)
    return (content,)


def generate_comment(data, full=False):
    comment = data["data"]
    text = unescape(comment["body_html"])
    if full:
        a = html.a(href=f'/u/{comment["author"]}')(f'/u/{comment["author"]}')
        cin = (
            a,
            get_time(comment),
            generate_awards(comment),
            html.br(),
            html.Safe(text))
        return html.div(Class="comment")(cin)
    else:
        replies = generate_replies(data)
        a = html.a(href=f'/u/{comment["author"]}')(f'/u/{comment["author"]}')
        cin = (
            a,
            get_time(comment),
            generate_awards(comment),
            html.br(),
            html.Safe(text),
            replies)
        return html.div(Class="comment")(cin)


def generate_comments(data_list):
    comments = ()
    for data in data_list:
        if data['kind'] == "more":
            comments += (html.p("..."),)
        else:
            comments += (generate_comment(data),)
    return html.div(Class="comments")(comments)


def generate_replies(data):
    replies = ()
    if data['kind'] == "more":
        replies += html.p("...")
    elif data['data']['replies']:
        for children in data['data']['replies']['data']['children']:
            if children['kind'] == "more":
                replies += (html.p("..."),)
            else:
                comment = children["data"]
                text = unescape(children["data"]["body_html"])
                a = html.a(
                    href=f'/u/{comment["author"]}')(f'/u/{comment["author"]}')
                cin = (
                    a,
                    get_time(comment),
                    generate_awards(comment),
                    html.br(),
                    html.Safe(text),
                    generate_replies(children))
                replies += (html.li(html.div(Class="reply")(cin)),)
    return html.ul(replies) if replies else ""


def generate_nav(
        data,
        subreddit=None,
        option=None,
        user=None,
        t=None,
        domain=None):
    buttons = ()
    target = f"r/{subreddit}" if subreddit else f"u/{user}" if user else f"domain/{domain}" if domain else ""
    if data["data"]["before"]:
        buttons += (
            generate_before_link(
                data, target, option or "", t),)
    if data["data"]["after"]:
        buttons += (
            generate_after_link(
                data, target, option or "", t),)
    return html.div(Class="nav")(buttons) if buttons else ()


def generate_menu(items):
    return (html.div(Class="menu")(items),)


def generate_header(subreddit=None, user=None, domain=None):
    header = (html.a(href="/")(html.span(Class="title")("kddit")),)
    if subreddit:
        header += (html.a(href=f"/r/{subreddit}")
                   (html.span(Class="title link")(f"r/{subreddit}")),)
    elif user:
        header += (html.a(href=f"/u/{user}")
                   (html.span(Class="title link")(f"u/{user}")),)
    elif domain:
        header += (html.a(href=f"/domain/{domain}")
                   (html.span(Class="title link")(domain)),)
    return header


def generate_expanded_menu(subreddit, option, t=None):
    p = f"/r/{subreddit}" if subreddit else ""
    items = tuple(
        (html.a(
            href=f'{p}/{option}?t={i}')(v),
            html.br()) for i,
        v in TIME_OPTIONS.items())
    return details(summary(TIME_OPTIONS[t or "day"]), items)


@app.route("/", "GET")
@app.route("/<option>", "GET")
@app.route("/<option>/", "GET")
@app.route("/r/<subreddit>", "GET")
@app.route("/r/<subreddit>/", "GET")
@app.route("/r/<subreddit>/<option>", "GET")
@app.route("/r/<subreddit>/<option>/", "GET")
@app.route("/domain/<domain>", "GET")
@app.route("/domain/<domain>/", "GET")
@app.route("/domain/<domain>/<option>", "GET")
@app.route("/domain/<domain>/<option>/", "GET")
def subreddit_page(subreddit=None, option=None, domain=None):
    if option and option not in SUBREDDIT_OPTIONS:
        return abort(404)
    query = dict(request.query)
    t = query["t"] if "t" in query else None
    p = f"/r/{subreddit}" if subreddit else f"/domain/{domain}" if domain else ""
    r = requests.get(
        f'https://old.reddit.com{p}/{option or DEFAULT_OPTION}.json',
        params=query,
        headers=headers)
    if r.status_code == 200:
        data = r.json()
        title = f"r/{subreddit}" if subreddit else domain or "kddit"
        header = generate_header(subreddit=subreddit, domain=domain)
        content = ()
        content += (generate_menu(generate_subreddit_menu(option, subreddit, domain)))
        if option in EXPANDED_OPTIONS:
            content += (generate_expanded_menu(
                subreddit, option or DEFAULT_OPTION, t),)
        if option == "gilded":
            content += (generate_mixed_content(
                data["data"]["children"]) or NOTHING,)
        else:
            content += (generate_posts(data, not bool(subreddit)) or NOTHING,)
        if nav := generate_nav(
                data,
                subreddit,
                domain=domain,
                option=option,
                t=t):
            content += (nav,)
        return generate_page(title, header, content).render()
    else:
        return abort(r.status_code)


@app.route("/r/<subreddit>/comments/<post_id>/<path>", "GET")
@app.route("/r/<subreddit>/comments/<post_id>/<path>/", "GET")
@app.route("/r/<subreddit>/comments/<post_id>/<path>/<comment_id>", "GET")
@app.route("/r/<subreddit>/comments/<post_id>/<path>/<comment_id>/", "GET")
def post_page(subreddit, post_id, path, comment_id=""):
    u = f"https://old.reddit.com/r/{subreddit}/comments/{post_id}/{path}/{comment_id}.json"
    r = requests.get(u, params=dict(request.query), headers=headers)
    if r.status_code == 200:
        data = r.json()
        post = data[0]["data"]["children"][0]["data"]
        comments = data[1]["data"]["children"]
        title = post["title"]
        content = (generate_post(post), generate_comments(comments))
        header = generate_header(subreddit=subreddit)
        return generate_page(title, header, content).render()
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
def user_page(user, option="overview"):
    if option and option not in USER_OPTIONS:
        return abort(404)
    query = dict(request.query)
    r = requests.get(
        f"https://old.reddit.com/user/{user}/{option}/.json",
        query,
        headers=headers)
    if r.status_code == 200:
        data = r.json()
        title = f"{option} by {user}"
        content = (generate_menu(generate_user_menu(option, user)),)
        content += (generate_mixed_content(data["data"]["children"]),)
        header = generate_header(user=user)
        if nav := generate_nav(data, user=user, option=option):
            content += (nav,)
        return generate_page(title, header, content).render()
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
def error_redirect(error):
    title = f"{error.status}!"
    content = html.h1(title)
    header = generate_header()
    return generate_page(title, header, content).render()


application = app
