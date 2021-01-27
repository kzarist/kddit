from bottle import request, response, abort, redirect, static_file
from kddit import app
from urllib.parse import urlparse, parse_qs
from kddit.settings import *
from kddit.utils import req, success, get_thumbnail, ydl
from kddit import html
from kddit.utils import tuplefy as t


@app.route("/", "GET")
@app.route("/<option>", "GET")
@app.route("/r/<subreddit>", "GET")
@app.route("/r/<subreddit>/<option>", "GET")
def subreddit_page(subreddit=None, option=None):
    if option and option not in SUBREDDIT_OPTIONS + ["search"]:
        return abort(404)
    query = dict(request.query)
    time = query["t"] if "t" in query else None
    q = query["q"] if "q" in query else ""
    p = f"/r/{subreddit}" if subreddit else ""
    url = f'https://old.reddit.com{p}/{option or DEFAULT_OPTION}.json'
    r = req(url, query)
    if success(r):
        data = r.json()
        if option == "search":
            title = f"search results - {q}"
        else:
            title = f"r/{subreddit}" if subreddit else "kddit"
        header = html.page_header(subreddit=subreddit, q=q)
        content = ()
        content += (html.subreddit_menu(option, subreddit))

        safe = not subreddit or subreddit in SAFE_SUBS
        
        if option in EXPANDED_OPTIONS:
            content += (html.expanded_menu(subreddit, option or DEFAULT_OPTION, time))
        
        if option in ["gilded", "search"]:
            content += (html.mixed_content(
                data["data"]["children"]) or html.nothing,)
        else:
            content += (html.posts(data, safe) or html.nothing,)
        if nav := html.nav(
                data,
                subreddit,
                option=option,
                time=time):
            content += (nav,)
        return html.page(title, header, content).render()
    else:
        return abort(r.status_code)


@app.route("/domain/<domain>", "GET")
@app.route("/domain/<domain>/<option>", "GET")
def domain_page(domain, option=None):
    if option and option not in SUBREDDIT_OPTIONS:
        return abort(404)
    query = dict(request.query)
    time = query["t"] if "t" in query else None
    q = query["q"] if "q" in query else ""
    p =  f"/domain/{domain}"
    url = f'https://old.reddit.com{p}/{option or DEFAULT_OPTION}.json'
    r = req(url, query)
    if success(r):
        data = r.json()
        if option == "search":
            title = f"search results - {q}"
        else:
            title = domain
        header = html.page_header(domain=domain, q=q)
        content = ()
        content += (html.domain_menu(option, domain))

        
        if option in EXPANDED_OPTIONS:
            content += (html.expanded_domain_menu(domain, option or DEFAULT_OPTION, time))
        
        if option in ["gilded", "search"]:
            content += (html.mixed_content(
                data["data"]["children"]) or html.nothing,)
        else:
            content += (html.posts(data, True) or html.nothing,)
        if nav := html.nav(
                data,
                domain=domain,
                option=option,
                time=time):
            content += (nav,)
        return html.page(title, header, content).render()
    else:
        return abort(r.status_code)



@app.route("/r/<subreddit>/comments/<post_id>/<path>", "GET")
@app.route("/r/<subreddit>/comments/<post_id>/<path>/<comment_id>", "GET")
def post_page(subreddit, post_id, path, comment_id=""):
    u = f"https://old.reddit.com/r/{subreddit}/comments/{post_id}/{path}/{comment_id}.json"
    r = req(u, dict(request.query))
    if success(r):
        data = r.json()
        post = data[0]["data"]["children"][0]["data"]
        comments = data[1]["data"]["children"]
        title = post["title"]
        content = (html.post(post), html.comments(comments))
        header = html.page_header(subreddit=subreddit)
        return html.page(title, header, content).render()
    else:
        return abort(r.status_code)


@app.route("/u/<user>", "GET")
@app.route("/user/<user>", "GET")
@app.route("/u/<user>/<option>", "GET")
@app.route("/user/<user>/<option>", "GET")
def user_page(user, option="overview"):
    if option and option not in USER_OPTIONS:
        return abort(404)
    url = f"https://old.reddit.com/user/{user}/{option}/.json"
    query = dict(request.query)
    r = req(url, query)
    if success(r):
        data = r.json()
        sort = query.get("sort")
        title = f"{option} by {user}"
        content = html.user_menu(option, user)
        if option != "gilded":
            content += html.user_sort_menu(option, sort, user)
        content += (html.mixed_content(data["data"]["children"]),)
        header = html.page_header(user=user)
        if nav := html.nav(data, user=user, option=option):
            content += (nav,)
        return html.page(title, header, content).render()
    else:
        return abort(r.status_code)


@app.route("/static/<file>")
def static(file):
    return static_file(file, root=f"{ROOT}/static")


@app.route("/video/<url:path>")
def video_proxy(url):
    uri = urlparse(url)
    if (netloc := uri.netloc) in PROXY_ALLOW["video"]:
        with ydl:
            result = ydl.extract_info(url, download=True)
            return static_file(
                f'{result["id"]}.mp4',
                root=FILE_PATH)
    elif netloc in PROXY_ALLOW["imgur"]:
        iurl = url.replace(".gifv", ".mp4")
        r = req(iurl)
        if success(r):
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
    r = req(f"{u}", dict(request.query))
    if success(r):
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
    return html.error_page(error).render()


