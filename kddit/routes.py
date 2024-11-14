from bottle import request, response, abort, static_file
from kddit import app
from urllib.parse import urlparse
from kddit import settings
from kddit.utils import req, success, ydl, req_url
from kddit import html
from kddit.utils import verify_subreddit_option, verify_user_option
from kddit.utils import get_subreddit_url, get_subreddit
from kddit.utils import nsfw_mode, get_query


def subreddit_content(data, subreddit, option, time, safe):
    content = (html.subreddit_menu(option, subreddit))
    if option in settings.EXPANDED_OPTIONS:
        content += (html.subreddit_sort_menu(subreddit, option or settings.DEFAULT_OPTION, time))
    content += (html.mixed_content(data, safe) or html.nothing,)
    content += html.subreddit_nav(data, subreddit, option, time)
    return content

def search_content(data, subreddit, sort, time, query):
    content = html.search_sort_menu(subreddit, query)
    content += html.search_time_menu(subreddit, query )
    content += html.mixed_content(data, True) or html.nothing
    content += html.search_nav(data, subreddit, query)
    return content

def domain_content(data, domain, option, time):
    content = html.domain_menu(option, domain)
    if option in settings.EXPANDED_OPTIONS:
        content += html.domain_sort_menu(domain, option or settings.DEFAULT_OPTION, time)
    content += html.mixed_content(data, True) or html.nothing
    content += html.domain_nav(data, domain, option, time)
    return content

def user_content(data, user, option, sort):
    content = html.user_menu(option, user)
    content += html.user_sort_menu(option, sort, user)
    content += (html.mixed_content(data, True, True),)
    content += html.user_nav(data, user, option, sort)
    return content

def multi_content(data, user, multi, option, sort):
    content = html.multi_menu(option, user, multi)
    content += html.multi_sort_menu(user, multi, option, sort)
    content += (html.mixed_content(data, True),)
    content += html.multi_nav(data, user, multi, option, sort)
    return content


@app.route("/search", "GET")
@app.route("/r/<subreddit>/search", "GET")
def search_page(subreddit=None):
    url = f'{get_subreddit_url()}/search/.json'
    query = dict(request.query)
    r = req(url, query)
    if success(r):
        data = r.json()
        time = query.get("t")
        sort = query.get("sort")
        q = query.get("q") or ""
        title = f"search results - {q}"
        header = html.page_header(subreddit=subreddit)
        content = search_content(data, subreddit, sort, time, query)
        return html.page(title, header, content).render()
    else:
        return abort(r.status_code)


@app.route("/u/<user>/m/<multi>", "GET")
@app.route("/user/<user>/m/<multi>", "GET")
@app.route("/u/<user>/m/<multi>/<option>", "GET")
@app.route("/user/<user>/m/<multi>/<option>", "GET")
def multi_page(user, multi=None ,option=None):
    verify_subreddit_option()
    url = f"/user/{user}/m/{multi}/{option or settings.DEFAULT_OPTION}/.json"
    query = dict(request.query)
    r = req(url, query)
    if success(r):
        data = r.json()
        sort = query.get("t")
        title = f"m/{multi} by u/{user}"
        header = html.page_header(user=user, multi=multi)
        content = multi_content(data, user, multi, option, sort)
        return html.page(title, header, content).render()
    else:
        return abort(r.status_code)


@app.route("/u/<user>", "GET")
@app.route("/user/<user>", "GET")
@app.route("/u/<user>/<option>", "GET")
@app.route("/user/<user>/<option>", "GET")
def user_page(user, option="overview"):
    verify_user_option()
    url = f"/user/{user}/{option}/.json"
    query = dict(request.query)
    r = req(url, query)
    if success(r):
        data = r.json()
        sort = query.get("sort")
        title = f"{option} by u/{user}"
        header = html.page_header(user=user)
        content = user_content(data, user, option, sort)
        return html.page(title, header, content).render()
    else:
        return abort(r.status_code)

@app.route("/u/<user>/comments/<post_id>/<path>", "GET")
@app.route("/user/<user>/comments/<post_id>/<path>", "GET")
@app.route("/u/<user>/comments/<post_id>/comment/<comment_id>", "GET")
@app.route("/user/<user>/comments/<post_id>/comment/<comment_id>", "GET")
def user_comment_page(user, post_id, path=None, comment_id=None):
    if path:
        url = f"/user/{user}/comments/{post_id}/{path}/.json"
    else:
        url = f"/user/{user}/comments/{post_id}/comment/{comment_id}/.json"
    query = dict(request.query)
    r = req(url, query)
    if success(r):
        data = r.json()
        header = html.page_header(user=user)
        safe = data[0]["data"]["children"][0]["data"]["over_18"]
        sort = query.get("sort") or settings.DEFAULT_OPTION
        content = html.mixed_content(data[0], safe)
        if path:
            content += html.user_comments_sort_menu(path, sort)
        title = f"{data[0]['data']['children'][0]['data']['title']} by u/{user}"
        comments = data[1]["data"]["children"]
        content += html.comments(comments, True)
        return html.page(title, header, content).render()
    else:
        return abort(r.status_code)

@app.route("/", "GET")
@app.route("/<option>", "GET")
@app.route("/r/<subreddit>", "GET")
@app.route("/r/<subreddit>/<option>", "GET")
def subreddit_page(subreddit=None, option=None):
    verify_subreddit_option()
    url = f'{get_subreddit_url()}/{option or settings.DEFAULT_OPTION}.json'
    query = dict(request.query)
    r = req(url, query)
    if success(r):
        data = r.json()
        time = query.get("t")
        title = get_subreddit() or "kddit"
        header = html.page_header(subreddit=subreddit)
        safe = nsfw_mode(subreddit)
        content = subreddit_content(data, subreddit, option, time, safe)
        return html.page(title, header, content).render()
    return abort(r.status_code)


@app.route("/domain/<domain>", "GET")
@app.route("/domain/<domain>/<option>", "GET")
def domain_page(domain, option=None):
    verify_subreddit_option()
    query = get_query()
    time = query.get("t")
    url = f'/domain/{domain}/{option or settings.DEFAULT_OPTION}.json'
    r = req(url, query)
    if success(r):
        data = r.json()
        title = domain
        header = html.page_header(domain=domain)
        content = domain_content(data, domain, option, time)
        return html.page(title, header, content).render()
    else:
        return abort(r.status_code)


@app.route("/r/<subreddit>/comments/<post_id>/<path>", "GET")
@app.route("/r/<subreddit>/comments/<post_id>/<path>/<comment_id>", "GET")
def post_page(subreddit, post_id, path, comment_id=""):
    u = f"/r/{subreddit}/comments/{post_id}/{path}/{comment_id}.json"
    query = get_query()
    r = req(u, query)
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


@app.route("/static/<file>")
def static(file):
    return static_file(file, root=f"{settings.ROOT}/static")


@app.route("/video/<url:path>")
def video_proxy(url):
    uri = urlparse(url)
    if uri.netloc in settings.PROXY_ALLOW["video"]:
        with ydl:
            result = ydl.extract_info(url, download=True)
            return static_file(
                f'{result["id"]}.mp4',
                root=settings.FILE_PATH)
    else:
        return abort(403)


@app.route("/proxy/<url:path>")
def proxy(url):
    uri = urlparse(url)
    netloc = uri.netloc
    query = get_query()
    if netloc not in settings.PROXY_ALLOW["image"]:
        return abort(403)
    r = req_url(url, query)
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
@app.error(429)
@app.error(451)
@app.error(500)
@app.error(503)
def error_redirect(error):
    return html.error_page(error).render()
