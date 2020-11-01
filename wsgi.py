from bottle import Bottle, request, response, abort, redirect
from bottle import SimpleTemplate, static_file
import requests
import html
import os
from datetime import datetime, timezone
from urllib.parse import urlparse


def env(var):
    try:
        return request.environ[var]
    except:
        return ""


app = Bottle()
root = os.path.dirname(os.path.realpath(__file__))

index_page = SimpleTemplate(open(f"{root}/templates/index.html").read())
page_header = SimpleTemplate(open(f"{root}/templates/header.html").read())
post_template = SimpleTemplate(open(f"{root}/templates/post.html").read())
video_template = SimpleTemplate(
    '<video class="media" controls poster="/proxy/{{post["thumbnail"]}}" preload="none" src="/proxy/{{post["media"]["reddit_video"]["fallback_url"]}}">')
nsfw_video_template = SimpleTemplate(
    '<video class="media" controls preload="none" src="/proxy/{{post["media"]["reddit_video"]["fallback_url"]}}"></video>'
)

image_template = SimpleTemplate('<img class="media" src="/proxy/{{post["url"]}}">')
nsfw_image_template = SimpleTemplate(
    '<label><input type="checkbox" class="nsfw"><img class="media" src="/proxy/{{post["url"]}}"></label>')
url_template = SimpleTemplate('<a href="{{post["url"]}}">{{post["url"]}}</a>')
subreddit_template = SimpleTemplate(
    '<a href="/{{post["subreddit_name_prefixed"]}}">{{post["subreddit_name_prefixed"]}}</a>')
text_template = SimpleTemplate('<div class="text">{{!text}}</div>')
before_template = SimpleTemplate(
    '<a class="button" href="{{subreddit+"/"}}{{option}}?count=25&before={{data["data"]["before"]}}">&lt;prev</a> | ')
after_template = SimpleTemplate(
    '<a class="button" href="{{subreddit+"/"}}{{option}}?count=25&after={{data["data"]["after"]}}">next&gt;</a>')
single_comment_template = SimpleTemplate("""
<li>
    <div class="sub-header"><a href="{{comment["permalink"]}}">
        <b>{{comment["link_title"]}}</b>
    </a> by <a href="/u/{{comment["link_author"]}}">{{comment["link_author"]}}</a> at {{created}} in
    <a href="/{{comment["subreddit_name_prefixed"]}}">
        {{comment["subreddit_name_prefixed"]}}
    </a>
    </div>
    {{!text}}
</li>
""")

subreddit_link = SimpleTemplate(
    '<a href="/r/{{subreddit}}"><span class="title link">r/{{subreddit}}</span></a>')
user_link = SimpleTemplate(
    '<a href="/u/{{user}}"><span class="title link">u/{{user}}</span></a>')

comment_template = SimpleTemplate(
    '<li><div class="comment"><a href="/u/{{comment["author"]}}">{{comment["author"]}}</a> at {{created}} <br>{{!text}}{{!replies}}</div></li>')

reply_template = SimpleTemplate(
    '<li><div class="reply"><a href="/u/{{comment["author"]}}">{{comment["author"]}}</a> at {{created}} <br>{{!text}}{{!replies}}</div></li>')

menu = SimpleTemplate(
    '<a class="menu {{"focus" if option == o else ""}}" href="{{"/r/"+subreddit+"/" if subreddit else "/"}}{{o}}">{{o}} </a>')

user_menu = SimpleTemplate(
    '<a class="menu {{"focus" if option == o else ""}}" href="/u/{{user}}/{{o}}">{{o}} </a>')

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:81.0) Gecko/20100101 Firefox/81.0"
}

subreddit_options = ["hot", "new", "rising", "controversial", "top"]
user_options = ["overview", "comments", "submitted"]

proxy_allow = ["i.redd.it", "v.redd.it", "b.thumbs.redditmedia.com"]


def default_fmt():
    return {
        "host": env("HTTP_HOST"),
        "prot": "https" if env("HTTPS") else "http"
    }


def get_created(data):
    return datetime.fromtimestamp(
        data["created"],
        timezone.utc).strftime("%d/%m/%y %H:%M")


def generate_post(post, full=False):
    if "crosspost_parent_list" in post:
        content = generate_post(post['crosspost_parent_list'][0], True)
    elif text := post["selftext_html"]:
        content = text_template.render(text=html.unescape(text))
    elif post["is_reddit_media_domain"]:
        if post["is_video"]:
            if post["thumbnail"] == "nsfw":
                content = nsfw_video_template.render(post=post)
            else:
                content = video_template.render(post=post)
        else:
            if full and post["thumbnail"] == "nsfw":
                content = nsfw_image_template.render(post=post)
            else:
                content = image_template.render(post=post)
    elif post["is_self"]:
        content = ""
    else:
        content = url_template.render(post=post)
    sub = subreddit_template.render(post=post) if full else ""
    created = get_created(post)
    return post_template.render(
        post=post,
        created=created,
        subreddit_link=sub,
        content=content)


def generate_posts(data, full=False):
    posts = []
    for children in data["data"]["children"]:
        post = children["data"]
        posts.append(generate_post(post, full))
    return '<hr>'.join(posts)


def generate_nav(data, subreddit, option):
    nav = ""
    if data["data"]["before"]:
        nav += before_template.render(data=data,
                                      subreddit=subreddit, option=option)
    if data["data"]["after"]:
        nav += after_template.render(data=data,
                                     subreddit=subreddit, option=option)
    return f"<hr><b>view more: {nav}</b>" if nav else ""


def generate_user_content(data_list):
    content = []
    for data in data_list:
        if data["kind"] == "t1":
            content.append(generate_comment(data, True))
        elif data["kind"] == "t3":
            content.append(generate_post(data["data"], True))
        else:
            print(data["kind"])
    return "<hr>".join(content)


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

    return f'<hr><div class="comments">{"<hr>".join(comments)}</div>'


def generate_replies(data):
    replies = []
    if data['kind'] == "more":
        replies.append("...")
    elif data['data']['replies']:
        for children in data['data']['replies']['data']['children']:
            if children['kind'] == "more":
                replies.append("...")
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


def generate_header(subreddit="", option=""):
    fmt = {}
    fmt["host"] = env("HTTP_HOST")
    fmt["prot"] = "https" if env("HTTPS") else "http"
    fmt["title"] = "kddit"
    fmt["url"] = "/"
    fmt["subreddit"] = subreddit
    extra = ""
    if subreddit:
        extra += subreddit_link.render(subreddit=subreddit)
    if option:
        extra += " | ".join(menu.render(o=o, option=option,
                                        subreddit=subreddit) for o in subreddit_options)
    fmt["extra"] = extra
    return page_header.render(**fmt)


def generate_user_header(user, option=""):
    fmt = {}
    fmt["host"] = env("HTTP_HOST")
    fmt["prot"] = "https" if env("HTTPS") else "http"
    fmt["title"] = "kddit"
    fmt["url"] = "/"
    fmt["subreddit"] = user
    extra = user_link.render(user=user)
    if option:
        extra += " | ".join(user_menu.render(o=o, option=option, user=user)
                            for o in user_options)
    fmt["extra"] = extra
    return page_header.render(**fmt)


@app.route("/", "GET")
@app.route("/<option>", "GET")
def index(option=""):
    if option and option not in subreddit_options:
        return abort(404)
    r = requests.get(
        f"https://old.reddit.com/{option}.json",
        params=dict(
            request.query),
        headers=headers)
    if r.status_code == 200:
        data = r.json()
        fmt = {}
        fmt["header"] = generate_header(option=option or "hot")
        fmt["title"] = "kddit"
        content = generate_posts(data, True) + generate_nav(data, "", option)
        return index_page.render(**fmt, content=content)
    else:
        return abort(r.status_code)


@app.route("/r/<subreddit>", "GET")
@app.route("/r/<subreddit>/", "GET")
@app.route("/r/<subreddit>/<option>", "GET")
@app.route("/r/<subreddit>/<option>/", "GET")
def subreddit(subreddit, option=""):
    if option and option not in subreddit_options:
        return abort(404)
    r = requests.get(
        f"https://old.reddit.com/r/{subreddit}/{option}/.json",
        params=dict(
            request.query),
        headers=headers)
    if r.status_code == 200:
        data = r.json()
        url = f"r/{subreddit}"
        fmt = {}
        fmt["host"] = env("HTTP_HOST")
        fmt["prot"] = "https" if env("HTTPS") else "http"
        fmt["title"] = url
        fmt["url"] = f"/{url}"
        fmt["subreddit"] = url
        fmt["header"] = generate_header(subreddit, option=option or "hot")
        content = generate_posts(
            data) + generate_nav(data, f"/r/{subreddit}", option)
        return index_page.render(**fmt, content=content)
    else:
        return abort(r.status_code)


@app.route("/r/<subreddit>/comments/<post_id>/<path>/", "GET")
@app.route("/r/<subreddit>/comments/<post_id>/<path>/<comment_id>/", "GET")
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
        url = f"r/{subreddit}"
        fmt = {}
        fmt["host"] = env("HTTP_HOST")
        fmt["prot"] = "https" if env("HTTPS") else "http"
        fmt["url"] = f"/{url}"
        fmt["title"] = post["title"]
        fmt["subreddit"] = url
        fmt["content"] = generate_post(post) + generate_comments(comments)
        header = generate_header(subreddit)
        return index_page.render(**fmt, header=header)
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
    if option and option not in user_options:
        return abort(404)
    r = requests.get(
        f"https://old.reddit.com/user/{user}/{option}/.json",
        params=dict(
            request.query),
        headers=headers)
    if r.status_code == 200:
        data = r.json()
        url = f"/u/{user}"
        fmt = {}
        fmt["host"] = env("HTTP_HOST")
        fmt["prot"] = "https" if env("HTTPS") else "http"
        fmt["url"] = url
        fmt["title"] = f"{option} by {user}"
        fmt["subreddit"] = url
        fmt["content"] = generate_user_content(data["data"]["children"])
        header = generate_user_header(user, option)
        return index_page.render(**fmt, header=header)
    else:
        return abort(r.status_code)


@app.route("/static/<file>")
def static(file):
    return static_file(file, root=f"{root}/static")


@app.route("/proxy/<url:path>")
def proxy(url):
    uri = urlparse(url)
    if uri.netloc not in proxy_allow:
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
def error_redirect(error):
    fmt = default_fmt()
    fmt["title"] = f"{error.status}!"
    fmt["content"] = f"<br><br><br><br><br><br><h1>{error.status}!\n</h1>"
    header = generate_header()
    return index_page.render(**fmt, header=header)


application = app
