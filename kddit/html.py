from pyhtml import *
from html import unescape, escape
from bs4 import BeautifulSoup
from glom import glom as g
from kddit.settings import *
from urllib.parse import urlparse, parse_qs
from kddit.utils import get_time, human_format, preview_re, builder
from kddit.utils import tuplefy

nothing = p("there doesn't seem to be anything here")

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
    
def header_div(arg):
    return div(Class="header")(arg)

def content_div(arg):
    return div(Class="content")(arg)
    
def media_div(arg):
    return div(Class="media")(arg)

def menu_div(arg):
    return div(Class="menu")(arg)

def awards_div(arg):
    return div(Class="awards")(arg)


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


@tuplefy
def alternate_video(url, thumbnail=None):
    opts = {}
    opts["src"] = f"/video/{url}"
    opts["controls"] = ""
    
    if thumbnail:
        opts["preload"] = "none"
        opts["poster"] = f"/proxy/{thumbnail}"        
    else:
        opts["preload"] = "metadata"
        
    video_ = media_div(video(**opts))
    return video_

@tuplefy
def reddit_video(post):
    url = g(post, "media.reddit_video.dash_url")
    video_ = video(controls="", preload="metadata", src=f"/video/{url}")
    output = media_div(video_)
    return output

@tuplefy
def reddit_image(post, url=None, safe=False):
    url = url or post["url"] 
    image_ = media_div(img(src=f'/proxy/{url}'))
    if post["over_18"] and safe:
        output = nsfw_label(image_)
    else:
        output = image_
    return output


def gallery(data, safe=False):
    images = ()
    for m_id in data["media_metadata"]:
        if "s" in data["media_metadata"][m_id]:
            image = data["media_metadata"][m_id]["s"]
            if "u" in image:
                l = image["u"]
            elif "gif" in me:
                l = image["gif"]
            images += reddit_image(data, unescape(l), safe)
    
    gallery_ = slider((slider_media(media) for media in images))
    
    return gallery_


def page(title_, header_, content_):
    head_ = head(title(title_), default_head)
    body_ = (header_div(header_), content_div(content_))
    output = html(head_, body_)
    return output


def post_content(post, safe):
    text = unescape(post["selftext_html"])
    soup = BeautifulSoup(text, "html.parser")
    for preview_link in soup.find_all('a', href=preview_re):
        url = preview_link.attrs["href"]
        div_ = soup.new_tag("div")
        div_.attrs = {"class" : "media"}
        img_ = soup.new_tag("img")
        img_.attrs = {"src" : f"/proxy/{url}"}
        div_.append(img_)
        preview_link.replace_with(div_)        
    return (Safe(str(soup)),)

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
            award.append(count)
        a_ = a(href=url, Class="awarding-icon", title=name)(award)
        output.append(a_)
                              
    return awards_div(output)



@tuplefy
def subreddit_menu(option, subreddit):
    output = []
    for o in SUBREDDIT_OPTIONS:
        focus = option == o or (not option and o == DEFAULT_OPTION)
        sub = f"/r/{subreddit}" if subreddit else ""
        url = f"{sub}/{o}"
        if focus:
            a_ = a(href=url, Class="focus")(o)
        else:
            a_ = a(href=url)(o)
        output.append(a_)

    return menu_div(output)

@tuplefy
def domain_menu(option, domain):
    output = []
    for o in SUBREDDIT_OPTIONS:
        focus = option == o or (not option and o == DEFAULT_OPTION)
        url = f"/domain/{domain}/{o}"

        if focus:
            a_ = a(href=url, Class="focus")(o)
        else:
            a_ = a(href=url)(o)
        
        output.append(a_)

    return menu_div(output)

@tuplefy
def expanded_menu(subreddit, option, time=None):
    p = f"/r/{subreddit}" if subreddit else ""
    output = []
    for i, v in TIME_OPTIONS.items():
        focus = time == i or ( not time and i == "hour"  )
        url = f'{p}/{option}?t={i}'
        if focus:
            a_ = a(Class="focus",href=url)(v)
        else:
            a_ = a(href=url)(v)
        output.append(a_)
    
    return menu_div(output)

@tuplefy
def user_menu(option, user):
    output = []
    for o in USER_OPTIONS:
        focus = option == o or (not option and o == default_option)
        link_ = f"/u/{user}/{o}"
        if focus:
            a_ = a(href=link_, Class="focus")(o)
        else:
            a_ = a(href=link_)(o)
        output.append(a_)
    return menu_div(output)


def before_link(data, target, option, t=None):
    sub = f"/{target}" if target else ""
    time = f"t={t}&" if t else ""
    url = f'{sub}/{option}?{time}count=25&before={data["data"]["before"]}'
    a_ = a(Class="button", href=url)("<prev")
    return a_


def after_link(data, target, option, t=None):
    sub = f"/{target}" if target else ""
    time = f"t={t}&" if t else ""
    url = f'{sub}/{option}?{time}count=25&after={data["data"]["after"]}'
    a_ = a(Class="button", href=url)("next>")
    return a_


def post(data, safe=False):
    if crosspost := "crosspost_parent_list" in data:
        output = post(data['crosspost_parent_list'][0], True)
    elif data["selftext_html"]:
        output = post_content(data, safe)
        if "poll_data" in data:
            output = poll(data)
    elif data["is_reddit_media_domain"] and data["thumbnail"]:
        output = (a(Class="post-link", href=data["url"])(data["url"]),)
        if data["is_video"]:
            output += reddit_video(data)
        else:
            output += reddit_image(data, safe=safe)
    elif "is_gallery" in data and data["media_metadata"]:
        output = (a(Class="post-link",href=data["url"])(data["url"]),)
        output += (gallery(data, safe=safe),)
    elif data["is_self"]:
        output = ""
    else:
        output = content(data, safe=safe)
    
    title_ = data["title"] if "title" in data else data["link_title"]
    flair = data["link_flair_text"] if "link_flair_text" in data else None
    author = ("Posted by", a(href=f'/u/{data["author"]}')(f'u/{data["author"]}'))
    
    post_info = (div(Class="post-info")((subreddit_link(data["subreddit"]),"•"), author, get_time(data["created"]), awards(data)),)

    div_ = ()
    
    div_ += (a(href=data["permalink"])(b(Safe(title_))),)
    if flair:
        div_ += (span(Class="flair")(Safe(flair)),)
    
    if crosspost:
        div_ += (output,)
    else:
        div_ += (div(Class="post-content")(output),)
    votes = (div(Class="votes")(span(Class="icon icon-upvote"), span(human_format(int(data["ups"] or data["downs"]))), span(Class="icon icon-downvote")))
    return div(Class="post")(votes, div(Class="inner-post")(post_info, div_))


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


def content(data, safe=False):
    url = data["url"]
    output = (a(Class="post-link",href=url)(url),)
    uri = urlparse(url)
    if (netloc := uri.netloc) in PROXY_ALLOW["youtube"]:
        if netloc in PROXY_ALLOW["video"]:
            output += alternate_video(url, url)
        elif "v" in (query := parse_qs(uri.query)):
            if v := query["v"]:
                u = f"https://youtu.be/{v[0]}"
                output += (alternate_video(u, u),)
    elif netloc in PROXY_ALLOW["video"]:
        output += (alternate_video(url),)
    elif netloc in PROXY_ALLOW["imgur"]:
        if url.endswith(".gifv"):
            output += alternate_video(url)
        else:
            output += reddit_image(data, safe=safe)
    return output


def posts(data, safe=False):
    posts_ = ()
    for children in data["data"]["children"]:
        data = children["data"]
        posts_ += (post(data, safe),)
    return posts_


def mixed_content(data_list):
    output = ()
    for data in data_list:
        if data["kind"] == "t1":
            output += (comment(data, True),)
        elif data["kind"] == "t3":
            output += (post(data["data"], True),)
    return (output,)


def comment(data, full=False):
    comment_ = data["data"]
    text = unescape(comment_["body_html"])
    if full:
        title_ = comment_["link_title"]
        header = ()
        header += ("by",
                   a(href=f'/u/{comment_["author"]}')(f'u/{comment_["author"]}'))
        header += ("in", subreddit_link(comment_["subreddit"]))
        header += (get_time(comment_["created"]),)
                   
        cin = (
            a(href=comment_["permalink"])(b(title_)), br(),
            div(Class="comment-info")(header),
            awards(comment_),
            Safe(text)
        )
        return div(Class="comment")(cin)
    else:
        replies_ = replies(data)
        a_ = a(href=f'/u/{comment_["author"]}')(f'u/{comment_["author"]}')
        link_ = a(href=comment_["permalink"])("🔗")
        points = (span(human_format(int(comment_["ups"] or comment_["downs"]))), "points", "·" )
        cin = (div(Class="comment-info")(
            a_, points,
            get_time(comment_["created"]), link_),
            awards(comment_),
            Safe(text),
               replies_)
        return div(Class="comment")(cin)


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
        replies_ += p("...")
    elif data['data']['replies']:
        for children in data['data']['replies']['data']['children']:
            if children['kind'] == "more":
                replies_ += (p("..."),)
            else:
                comment_ = children["data"]
                text = unescape(children["data"]["body_html"])
                a_ = a(
                    href=f'/u/{comment_["author"]}')(f'u/{comment_["author"]}')
                link_ = a(href=comment_["permalink"])("🔗")
                points = (span(human_format(int(comment_["ups"] or comment_["downs"]))), "points", "·" )
                cin = (div(Class="comment-info")(
                    a_, points,
                    get_time(comment_["created"]), link_),
                    awards(comment_),
                    Safe(text),
                    replies(children))
                replies_ += (li(div(Class="reply")(cin)),)
    return ul(replies_) if replies else None


def nav(
        data,
        subreddit=None,
        option=None,
        user=None,
        time=None,
        domain=None):
    buttons = ()
    target = f"r/{subreddit}" if subreddit else f"u/{user}" if user else f"domain/{domain}" if domain else ""
    if data["data"]["before"]:
        buttons += (
            before_link(
                data, target, option or "", time),)
    if data["data"]["after"]:
        buttons += (
            after_link(
                data, target, option or "", time),)
    return div(Class="nav")(buttons) if buttons else ()


def menu(items):
    g1 = ()
    g2 = ()
    for i, item in enumerate(items):
        if i > 3:
            g2 += (item, br())
        else:
            g1 += (item,)
    if g2:
        hidden = (label(Class="flex")(input_(Class="hidden", type="checkbox"), span(Class="button")("..."), div(g2)))
    else:
        hidden = None
    return (div(Class="menu")(g1, hidden),)


def page_header(subreddit=None, user=None, domain=None, option=None, q=""):
    header_ = (a(Class="main-icon",href="/")(img(src="/static/favicon.svg")),)
    if subreddit:
        header_ += (a(href=f"/r/{subreddit}"),)
    elif user:
        header_ += (a(href=f"/u/{user}"),)
    elif domain:
        header_ += (a(href=f"/domain/{domain}"),)
    placeholder = "search"
    button = input_(Class="button", type="submit", value="")
    header_ += (form(method="GET", action="/search/")(input_(name="q", required="", id="search-bar", placeholder=q or placeholder, value=q), button),)
    return header_

def error_page(error):
    title_ = f"{error.status}!"
    output = h1(title_)
    header_ = page_header()
    return page(title_, header_, output).render()
