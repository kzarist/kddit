from pyhtml import *
from html import unescape, escape
from bs4 import BeautifulSoup
from glom import glom as g
from glom import Coalesce
from kddit.settings import *
from urllib.parse import urlparse, parse_qs, urlencode
from kddit.utils import get_time, human_format, preview_re, builder, processing_re
from kddit.utils import tuplefy, get_metadata, replace_tag

nothing = (p("there doesn't seem to be anything here"),)

style_css = link(rel="stylesheet", type="text/css", href="/static/style.css")
slider_css = link(rel="stylesheet", type="text/css", href="/static/slider.css")
favicon = link(rel="icon", href="/static/favicon.svg")

viewport = meta(name="viewport", content_="width=device-width, initial-scale=1.0")

default_head = (style_css, slider_css, favicon, viewport)

class progress(Tag):
    self_closing = False

class svg(Tag):
    self_closing = False

class path(Tag):
    self_closing = False

def subreddit_link(sub):
    return a(Class="sub-link", href=f"/r/{sub}")(f"r/{sub}")


def header_div(*args):
    return div(Class="header")(*args)

def content_div(*args):
    return div(Class="content")(*args)

def post_div(*args):
    return div(Class="post")(*args)

def inner_post_div(*args):
    return div(Class="inner-post")(*args)

def media_div(*args):
    return div(Class="media")(*args)

def menu_div(*args):
    return div(Class="menu")(*args)

def awards_div(*args):
    return div(Class="awards")(*args)

def post_info_div(*args):
    return div(Class="post-info")(*args)

def post_content_div(*args):
    return div(Class="post-content")(*args)

def comment_content_div(*args):
    return div(Class="comment-content")(*args)

def slider(arg):
    mask = div(Class="css-slider-mask")
    ul_ = ul(Class="css-slider with-responsive-images")
    return builder(mask, ul_, arg)

def slider_media(arg):
    slider = li(Class="slide", tabindex=1)
    outer = span(Class="slide-outer")
    inner = span(Class="slide-inner")
    gfx = span(Class="slide-gfx")(arg)    
    return builder(slider, outer, inner, gfx)

def nsfw_label(arg):
    return label(input_(Class="nsfw", type="checkbox"),arg)

def get_thumbnail(data):
    thumbnail = g(data, Coalesce("secure_media.oembed.thumbnail_url", "preview.images.0.source.url"), default="")
    return unescape(thumbnail)
    
@tuplefy
def alternate_video(data, url, safe=False):
    opts = {}
    opts["src"] = f"/video/{url}"
    opts["controls"] = ""
    thumbnail = get_thumbnail(data)
    if nsfw(data) and safe:
        opts["preload"] = "none"
    elif thumbnail:
        opts["preload"] = "none"
        opts["poster"] = f"/proxy/{thumbnail}"        
    else:
        opts["preload"] = "metadata"
        
    video_ = media_div(video(**opts))
    return video_

def nsfw(data):
    return data.get("over_18")

@tuplefy
def reddit_video(data, thumbnail=None, safe=False):
    url = g(data, "media.reddit_video.dash_url")
    opts = {"controls":"", "src":f"/video/{url}"}
    opts["preload"] = "none"
    if not (nsfw(data) and safe):
        thumbnail = get_thumbnail(data)
        opts["poster"] = f"/proxy/{thumbnail}"

    video_ = video(**opts)
    output = media_div(video_)
    return output

@tuplefy
def reddit_image(data, url=None, safe=False, text=None):
    url = url or data["url"] 
    image_ = media_div(img(src=f'/proxy/{url}'), em(text))
    if nsfw(data) and safe:
        output = nsfw_label(image_)
    else:
        output = image_
    return output

def gallery(data, safe=False):
    output = (a(Class="post-link",href=data["url"])(data["url"]),)
    images = ()
    for item in reversed(g(data,"gallery_data.items", default=[])):
        media_id = item["media_id"]
        url = get_metadata(data, media_id)
        if url:
            images += reddit_image(data, url, safe)
    if images:
        output += slider((slider_media(media) for media in images))
        
    return output

def page(title_, header_, content_):
    head_ = head(title(unescape(title_)), default_head)
    body_ = (header_div(header_), content_div(content_))
    output = html(head_, body_)
    return output


def post_content(data, safe):
    text = unescape(data["selftext_html"])
    soup = BeautifulSoup(text, "html.parser")
    for preview_link in soup.find_all("a", href=preview_re):
        url = preview_link.attrs["href"]
        preview_text = preview_link.text
        caption = preview_text if preview_text != url else None
        r_image = reddit_image(data, url, safe, text=caption)
        replace_tag(preview_link.parent, r_image)
    for preview_em in soup.find_all("em", string=processing_re):
        name = processing_re.match(preview_em.text).group(1)
        if url := get_metadata(data, name):
            r_image = reddit_image(data, url, safe)
            replace_tag(preview_em , r_image)
    return builder(post_content_div, Safe,str,soup)

def awards(data):
    if not "all_awardings" in data:
        return
    
    output = []
    url = f'/{data["subreddit_name_prefixed"]}/gilded'
    for awarding in data["all_awardings"]:
        award = [img(src=f'/proxy/{awarding["icon_url"]}')]
        count = awarding["count"]
        name = escape(awarding["name"])
        if count > 1:
            award.append(span(count))
        a_ = a(href=url, Class="awarding-icon", title=name)(award)
        output.append(a_)
                              
    return awards_div(output)



@tuplefy
def subreddit_menu(option, subreddit):
    output = []
    focused = option or DEFAULT_OPTION
    for o in SUBREDDIT_OPTIONS:
        focus = o == focused
        sub = f"/r/{subreddit}" if subreddit else ""
        url = f"{sub}/{o}"
        a_ = a(href=url, Class="focus")(o) if focus else a(href=url)(o)
        output.append(a_)

    return menu_div(output)

@tuplefy
def search_sort_menu(subreddit, params):
    output = []
    focused = params.get("sort", "relevance")
    for o in SEARCH_SORT:
        query = params.copy()
        query["sort"] = o
        focus = o == focused
        sub = f"/r/{subreddit}" if subreddit else ""
        url = f"{sub}/search?{urlencode(query)}"
        a_ = a(href=url, Class="focus")(o) if focus else a(href=url)(o)
        output.append(a_)

    return menu_div(output)

@tuplefy
def search_time_menu(subreddit, params):
    output = []
    focused = params.get("t", "hour") 
    for i, v in TIME_OPTIONS.items():
        query = params.copy()
        query["t"] = i
        focus = i == focused
        sub = f"/r/{subreddit}" if subreddit else ""
        url = f"{sub}/search?{urlencode(query)}"
        a_ = a(Class="focus",href=url)(v) if focus else a(href=url)(v)
        output.append(a_)
    
    return menu_div(output)


@tuplefy
def domain_menu(option, domain):
    output = []
    focused = option or DEFAULT_OPTION
    for o in SUBREDDIT_OPTIONS:
        focus = o == focused
        url = f"/domain/{domain}/{o}"
        a_ = a(href=url, Class="focus")(o) if focus else a(href=url)(o)        
        output.append(a_)

    return menu_div(output)

@tuplefy
def subreddit_sort_menu(subreddit, option, time=None):
    p = f"/r/{subreddit}" if subreddit else ""
    focused = time or "hour"
    output = []
    for i, v in TIME_OPTIONS.items():
        focus = i == focused
        url = f'{p}/{option}?t={i}'
        a_ = a(Class="focus",href=url)(v) if focus else a(href=url)(v)
        output.append(a_)
    
    return menu_div(output)

@tuplefy
def domain_sort_menu(domain, option, time=None):
    output = []
    focused = time or "hour"
    for i, v in TIME_OPTIONS.items():
        focus = i == focused
        url = f"/domain/{domain}/{option}?t={i}"
        a_ = a(Class="focus",href=url)(v) if focus else a(href=url)(v)
        output.append(a_)
    
    return menu_div(output)


@tuplefy
def user_menu(option, user):
    output = []
    for o in USER_OPTIONS:
        focus = option == o or (not option and o == DEFAULT_OPTION)
        link_ = f"/u/{user}/{o}"
        if focus:
            a_ = a(href=link_, Class="focus")(o)
        else:
            a_ = a(href=link_)(o)
        output.append(a_)
    return menu_div(output)

@tuplefy
def user_sort_menu(option, sort, user):
    output = []
    focused = sort or DEFAULT_OPTION
    for o in USER_SORT:
        focus = o == focused
        link_ = f"/u/{user}/{option}/?sort={o}"
        a_ = a(href=link_, Class="focus")(o) if focus else a(href=link_)(o)
        output.append(a_)
    return menu_div(output)

@tuplefy
def before_link(data, target, option, t=None):
    option = option or ""
    sub = f"/{target}" if target else ""
    time = f"t={t}&" if t else ""
    url = f'{sub}/{option}?{time}count=25&before={data["data"]["before"]}'
    a_ = a(Class="button", href=url)("<prev")
    return a_


@tuplefy
def after_link(data, target, option, t=None):
    option = option or ""
    sub = f"/{target}" if target else ""
    time = f"t={t}&" if t else ""
    url = f'{sub}/{option}?{time}count=25&after={data["data"]["after"]}'
    a_ = a(Class="button", href=url)("next>")
    return a_

@tuplefy
def search_before_link(data, target, params):
    query = params.copy()
    query.pop("after", None)
    query["before"] = g(data,"data.before")
    url = f'{target}/?{urlencode(query)}'
    a_ = a(Class="button", href=url)("<prev")
    return a_


@tuplefy
def search_after_link(data, target, params):
    query = params.copy()
    query.pop("before", None)
    query["after"] = g(data, "data.after")
    url = f'{target}/?{urlencode(query)}'
    a_ = a(Class="button", href=url)("next>")
    return a_

@tuplefy
def user_before_link(data, target, option, sort=None):
    option = option or ""
    sub = f"/{target}" if target else ""
    time = f"sort={sort}&" if sort else ""
    url = f'{sub}/{option}?{time}count=25&before={data["data"]["before"]}'
    a_ = a(Class="button", href=url)("<prev")
    return a_


@tuplefy
def user_after_link(data, target, option, sort=None):
    option = option or ""
    sub = f"/{target}" if target else ""
    time = f"sort={sort}&" if sort else ""
    url = f'{sub}/{option}?{time}count=25&after={data["data"]["after"]}'
    a_ = a(Class="button", href=url)("next>")
    return a_

def alternate_media(data, safe=False):
    pass

def youtube_media(data, url, uri, safe):
    output = ()
    if uri.netloc == "youtu.be":
        output += alternate_video(data, url, safe)
    elif v := parse_qs(uri.query).get("v"):
        u = f"https://youtu.be/{v[0]}"
        output += alternate_video(data, u, safe)
    return output

def imgur_media(data, url, safe):
    if url.endswith(".gifv"):
        output = alternate_video(data, url, safe=safe)
    else:
        output = reddit_image(data, safe=safe)

    return output

def alternate_content(data, safe=False):
    url = data["url"]
    output = (a(Class="post-link",href=url)(url),)
    uri = urlparse(url)
    netloc = uri.netloc
    
    if netloc in PROXY_ALLOW["youtube"]:
        output += youtube_media(data, url, uri, safe)
    elif netloc in PROXY_ALLOW["video"]:
        output += alternate_video(data, url, safe=safe)
    elif netloc in PROXY_ALLOW["imgur"]:
        output += imgur_media(data, url, safe)
    elif netloc in PROXY_ALLOW["image"]:
        output += reddit_image(data, safe=safe)
    return post_content_div(output)

def reddit_media(data, safe):
    output = (a(Class="post-link", href=data["url"])(data["url"]),)
    if data["is_video"]:
        output += reddit_video(data, safe=safe)
    else:
        output += reddit_image(data, safe=safe)
    return post_content_div(output)
    
def reddit_content(data, safe=False):
    if data["selftext_html"]:
        output = post_content(data, safe)
    elif data["is_reddit_media_domain"] and data["thumbnail"]:
        output = reddit_media(data, safe)
    elif data.get("is_gallery"):
        output = gallery(data, safe=safe)
    else:
        output = None

    return output

def rich_text(richtext, text):
    for item in richtext:
        a_ = item.get("a")
        u = item.get("u")
        if not (a_ or u):
            continue
        text = text.replace(a_, f'<span class="flair-emoji" style="background-image:url(/proxy/{u});"></span>')

    return text

def domain_link(data):
    if data.get("is_self"):
        return None
    domain = data.get("domain")
    domain_url = f"/domain/{domain}"
    return ("(", a(href=domain_url)(f"{domain}"), ")")

@tuplefy
def post(data, safe=False):
    if data.get("crosspost_parent_list"):
        content = post(data['crosspost_parent_list'][0], True)
    elif data.get("poll_data"):
        content = poll(data)
    else:
        content = reddit_content(data, safe) or alternate_content(data, safe=safe)

    author = data.get("author")
    permalink = data.get("permalink")
    
    title_ = unescape(data.get("title"))

    domain = domain_link(data)
    
    votes = human_format(int(data.get("ups") or data.get("downs")))
    
    author = ("Posted by", a(href=f'/u/{author}')(f'u/{author}'))

    title_link = builder(a(href=permalink),Safe,b,title_)
    
    post_info = post_info_div(subreddit_link(data["subreddit"]),"•", author, get_time(data["created"]), domain,  awards(data))

    flair = post_flair(data)

    inner = (title_link, flair, content)
    
    votes = div(Class="votes")(span(Class="icon icon-upvote"), votes , span(Class="icon icon-downvote"))

    return post_div(votes, inner_post_div(post_info, inner))


def poll(data):
    options = ()
    tvotes = g(data,"poll_data.total_vote_count")
    for opt in data["poll_data"]["options"]:
        if "vote_count" in opt:
            votes = opt["vote_count"]
            cin = (
                p(f'{opt["text"]} : {votes}'),
                progress(
                    value=votes,
                    max=tvotes))
            options += cin
        else:
            cin = (p(input_(disabled="", type="radio"), opt["text"]))
            options += (cin,)
    div_ = div(Class="poll")(options)
    return div_



def posts(data, safe=False):
    posts_ = ()
    for children in g(data, "data.children"):
        data = children["data"]
        posts_ += post(data, safe)
    return posts_

@tuplefy
def mixed_content(data, safe):
    output = ()
    for children in g(data, "data.children"):
        if children["kind"] == "t1":
            output += (comment(children, safe),)
        elif children["kind"] == "t3":
            output += (post(children["data"], safe),)
    return output

def comment_flair(data):
    flair_text = g(data, "author_flair_text", default=None)
    if flair_richtext := data.get("author_flair_richtext"):
        flair_text = rich_text(flair_richtext, flair_text )
    return builder(span(Class="flair"),Safe,unescape,flair_text) if flair_text else None

def post_flair(data):
    flair_text = g(data, "link_flair_text", default=None)
    if flair_richtext := data.get("link_flair_richtext"):
        flair_text = rich_text(flair_richtext, flair_text )
    return builder(span(Class="flair"),Safe,unescape,flair_text) if flair_text else None




def comment(data, full=False):
    comment_ = data["data"]
    text = unescape(comment_["body_html"])
    flair = comment_flair(comment_)
    if full:
        title_ = comment_["link_title"]
        header_ = ()
        header_ += ("by", a(href=f'/u/{comment_["author"]}')(f'u/{comment_["author"]}'),flair)
        header_ += ("in", subreddit_link(comment_["subreddit"]))
        header_ += (get_time(comment_["created"]),)
        
        inner = (
            a(href=comment_["permalink"])(b(title_)),
            div(Class="comment-info")(header_),
            awards(comment_),
            comment_content_div(Safe(text))
        )
        return div(Class="comment")(inner)
    else:
        replies_ = replies(data)
        a_ = a(href=f'/u/{comment_["author"]}')(f'u/{comment_["author"]}')
        link_ = a(href=comment_["permalink"])("🔗")
        points = (span(human_format(int(comment_["ups"] or comment_["downs"]))), "points", "·" )
        inner = (div(Class="comment-info")(
            a_,flair, points,
            get_time(comment_["created"]), link_),
            awards(comment_),
            comment_content_div(Safe(text)),
               replies_)
        return div(Class="comment")(inner)

@tuplefy
def reply(data):
    comment_ = data["data"]
    text = unescape(comment_["body_html"])
    flair = comment_flair(comment_)
    replies_ = replies(data)
    a_ = a(href=f'/u/{comment_["author"]}')(f'u/{comment_["author"]}')
    link_ = a(href=comment_["permalink"])("🔗")
    points = (span(human_format(int(comment_["ups"] or comment_["downs"]))), "points", "·" )
    inner = (div(Class="comment-info")(
        a_,flair, points,
        get_time(comment_["created"]), link_),
           awards(comment_),
           Safe(text),
           replies_)
    return div(Class="reply")(inner)


def comments(data_list):
    comments = ()
    for data in data_list:
        if data['kind'] == "more":
            comments += (p("..."),)
        else:
            comments += (comment(data),)
    return div(Class="comments")(comments)



def replies(data):
    replies_ = ()
    if data['kind'] == "more":
        replies_ += (p("..."),)
    for children in g(data, "data.replies.data.children", default=[]):
        if children['kind'] == "more":
            replies_ += (p("..."),)
        else:
            replies_ += reply(children)
    return ul(replies_) if replies else None



@tuplefy
def subreddit_nav(data, subreddit, option=None, time=None):
    buttons = ()
    target = f"r/{subreddit}" if subreddit else ""
    
    if data["data"]["before"]:
        buttons += before_link(data, target, option, time)
    if data["data"]["after"]:
        buttons += after_link(data, target, option, time)

    return div(Class="nav")(buttons) if buttons else ()

@tuplefy
def search_nav(data, subreddit, params):
    buttons = ()
    target = f"/r/{subreddit}/search" if subreddit else "/search"
    if g(data, "data.before"):
        buttons += search_before_link(data, target, params)
    if g(data, "data.after"):
        buttons += search_after_link(data, target, params)

    return div(Class="nav")(buttons) if buttons else None

@tuplefy
def domain_nav(data, domain, option=None, time=None):
    buttons = ()
    target = f"domain/{domain}"
    if data["data"]["before"]:
        buttons += before_link(data, target, option, time)
    if data["data"]["after"]:
        buttons += after_link(data, target, option, time)

    return div(Class="nav")(buttons) if buttons else ()

@tuplefy
def user_nav(data, user, option=None, time=None):
    buttons = ()
    target = f"u/{user}"
    if data["data"]["before"]:
        buttons += user_before_link(data, target, option, time)
    if data["data"]["after"]:
        buttons += user_after_link(data, target, option, time)
    return div(Class="nav")(buttons) if buttons else ()


def page_header(subreddit=None, user=None, domain=None, option=None, q=""):
    placeholder = "search"
    action = f"/r/{subreddit}/search" if subreddit else "/search"
    button = input_(Class="button", type="submit", value="")
    
    header_ = (a(Class="main-icon",href="/")(img(src="/static/favicon.svg")),)
    header_ += (form(method="GET", action=action)(input_(name="q", required="", id="search-bar", placeholder=q or placeholder, value=q), button),)
    
    return header_

def error_page(error):
    title_ = f"{error.status}!"
    output = h1(title_)
    header_ = page_header()
    return page(title_, header_, output)
