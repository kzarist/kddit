import os

from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, Response
from kddit import app
from urllib.parse import urlparse
from kddit import settings
from kddit.utils import req, success, req_url
import yt_dlp
from kddit import html
from kddit.utils import nsfw_mode
from kddit.settings import SUBREDDIT_OPTIONS, USER_OPTIONS
from kddit.content import (
    subreddit_content,
    search_content,
    domain_content,
    user_content,
    multi_content,
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return HTMLResponse(html.error_page(exc.status_code).render(), status_code=exc.status_code)


@app.get('/search')
@app.get('/r/{subreddit}/search')
def search_page(request: Request, subreddit: str = None):
    url = f'/r/{subreddit}/search/.json' if subreddit else '/search/.json'
    query = dict(request.query_params)
    query.update({'restrict_sr': bool(subreddit), 'include_over_18': 'true'})
    print(f'search query: {query}')
    r = req(url, query)
    if success(r):
        data = r.json()
        time = query.get('t')
        sort = query.get('sort')
        q = query.get('q') or ''
        title = f'search results - {q}'
        header = html.page_header(subreddit=subreddit)
        content = search_content(data, subreddit, sort, time, query)
        return HTMLResponse(html.page(title, header, content).render())
    raise HTTPException(status_code=r.status_code)


@app.get('/u/{user}/m/{multi}')
@app.get('/user/{user}/m/{multi}')
@app.get('/u/{user}/m/{multi}/{option}')
@app.get('/user/{user}/m/{multi}/{option}')
def multi_page(request: Request, user: str, multi: str, option: str = None):
    if option and option not in SUBREDDIT_OPTIONS:
        raise HTTPException(status_code=404)
    url = f'/user/{user}/m/{multi}/{option or settings.DEFAULT_OPTION}/.json'
    query = dict(request.query_params)
    r = req(url, query)
    if success(r):
        data = r.json()
        sort = query.get('t')
        title = f'm/{multi} by u/{user}'
        header = html.page_header(user=user, multi=multi)
        content = multi_content(data, user, multi, option, sort)
        return HTMLResponse(html.page(title, header, content).render())
    raise HTTPException(status_code=r.status_code)


@app.get('/u/{user}')
@app.get('/user/{user}')
@app.get('/u/{user}/{option}')
@app.get('/user/{user}/{option}')
def user_page(request: Request, user: str, option: str = 'overview'):
    if option and option not in USER_OPTIONS:
        raise HTTPException(status_code=404)
    url = f'/user/{user}/{option}/.json'
    query = dict(request.query_params)
    r = req(url, query)
    if success(r):
        data = r.json()
        sort = query.get('sort')
        title = f'{option} by u/{user}'
        header = html.page_header(user=user)
        content = user_content(data, user, option, sort)
        return HTMLResponse(html.page(title, header, content).render())
    raise HTTPException(status_code=r.status_code)


@app.get('/u/{user}/comments/{post_id}/{path}')
@app.get('/user/{user}/comments/{post_id}/{path}')
@app.get('/u/{user}/comments/{post_id}/comment/{comment_id}')
@app.get('/user/{user}/comments/{post_id}/comment/{comment_id}')
def user_comment_page(request: Request, user: str, post_id: str, path: str = None, comment_id: str = None):
    if path:
        url = f'/user/{user}/comments/{post_id}/{path}/.json'
    else:
        url = f'/user/{user}/comments/{post_id}/comment/{comment_id}/.json'
    query = dict(request.query_params)
    r = req(url, query)
    if success(r):
        data = r.json()
        header = html.page_header(user=user)
        safe = data[0]['data']['children'][0]['data']['over_18'] = False
        sort = query.get('sort') or settings.DEFAULT_OPTION
        content = html.mixed_content(data[0], safe)
        if path:
            content += html.user_comments_sort_menu(path, sort)
        title = f'{data[0]["data"]["children"][0]["data"]["title"]} by u/{user}'
        comments = data[1]['data']['children']
        content += html.comments(comments)
        return HTMLResponse(html.page(title, header, content).render())
    raise HTTPException(status_code=r.status_code)


@app.get('/')
@app.get('/{option}')
@app.get('/r/{subreddit}')
@app.get('/r/{subreddit}/{option}')
def subreddit_page(request: Request, subreddit: str = None, option: str = None):
    if option and option not in SUBREDDIT_OPTIONS:
        raise HTTPException(status_code=404)
    subreddit_url = f'/r/{subreddit}' if subreddit else ''
    url = f'{subreddit_url}/{option or settings.DEFAULT_OPTION}.json'
    query = dict(request.query_params)
    r = req(url, query)
    if success(r):
        data = r.json()
        time = query.get('t')
        title = f'r/{subreddit}' if subreddit else 'kddit'
        header = html.page_header(subreddit=subreddit)
        safe = nsfw_mode(subreddit)
        content = subreddit_content(data, subreddit, option, time, safe)
        return HTMLResponse(html.page(title, header, content).render())
    raise HTTPException(status_code=r.status_code)


@app.get('/domain/{domain}')
@app.get('/domain/{domain}/{option}')
def domain_page(request: Request, domain: str, option: str = None):
    if option and option not in SUBREDDIT_OPTIONS:
        raise HTTPException(status_code=404)
    query = dict(request.query_params)
    time = query.get('t')
    url = f'/domain/{domain}/{option or settings.DEFAULT_OPTION}.json'
    r = req(url, query)
    if success(r):
        data = r.json()
        title = domain
        header = html.page_header(domain=domain)
        content = domain_content(data, domain, option, time)
        return HTMLResponse(html.page(title, header, content).render())
    raise HTTPException(status_code=r.status_code)


@app.get('/r/{subreddit}/comments/{post_id}/{path}')
@app.get('/r/{subreddit}/comments/{post_id}/{path}/{comment_id}')
def post_page(request: Request, subreddit: str, post_id: str, path: str, comment_id: str = ''):
    u = f'/r/{subreddit}/comments/{post_id}/{path}/{comment_id}.json'
    query = dict(request.query_params)
    r = req(u, query)
    if success(r):
        data = r.json()
        post = data[0]['data']['children'][0]['data']
        comments = data[1]['data']['children']
        title = post['title']
        content = (html.post(post), html.comments(comments))
        header = html.page_header(subreddit=subreddit)
        return HTMLResponse(html.page(title, header, content).render())
    raise HTTPException(status_code=r.status_code)


@app.get('/video/{url:path}')
def video_proxy(url: str):
    uri = urlparse(url)
    if uri.netloc not in settings.PROXY_ALLOW['video']:
        raise HTTPException(status_code=403)

    # reddit hands us a video-only track (.../CMAF_720.mp4); the audio lives in a
    # sibling representation, so feed yt-dlp the DASH manifest instead and let it
    # mux the two together.
    video_id = next((part for part in uri.path.split('/') if part), None)
    if not video_id:
        raise HTTPException(status_code=400)
    source = f'https://{uri.netloc}/{video_id}/DASHPlaylist.mpd'

    out_path = f'{settings.FILE_PATH}{video_id}.mp4'
    if not os.path.exists(out_path):
        opts = {**settings.YDL_OPTS, 'outtmpl': out_path}
        with yt_dlp.YoutubeDL(opts) as local_ydl:
            local_ydl.download([source])
    return FileResponse(out_path)


@app.get('/proxy/{url:path}')
def proxy(url: str, request: Request):
    uri = urlparse(url)
    netloc = uri.netloc
    query = dict(request.query_params)
    if netloc not in settings.PROXY_ALLOW['image']:
        raise HTTPException(status_code=403)
    r = req_url(url, query)
    if success(r):
        return Response(content=r.content, media_type=r.headers['content-type'])
    raise HTTPException(status_code=r.status_code)
