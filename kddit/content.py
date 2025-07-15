from kddit import html
from kddit import settings


def subreddit_content(data, subreddit, option, time, safe):
    content = html.subreddit_menu(option, subreddit)
    if option in settings.EXPANDED_OPTIONS:
        content += html.subreddit_sort_menu(
            subreddit, option or settings.DEFAULT_OPTION, time
        )
    content += (html.mixed_content(data, safe) or html.nothing,)
    content += html.subreddit_nav(data, subreddit, option, time)
    return content


def search_content(data, subreddit, sort, time, query):
    content = html.search_sort_menu(subreddit, query)
    content += html.search_time_menu(subreddit, query)
    content += html.mixed_content(data, True) or html.nothing
    content += html.search_nav(data, subreddit, query)
    return content


def domain_content(data, domain, option, time):
    content = html.domain_menu(option, domain)
    if option in settings.EXPANDED_OPTIONS:
        content += html.domain_sort_menu(
            domain, option or settings.DEFAULT_OPTION, time
        )
    content += html.mixed_content(data, True) or html.nothing
    content += html.domain_nav(data, domain, option, time)
    return content


def user_content(data, user, option, sort):
    content = html.user_menu(option, user)
    content += html.user_sort_menu(option, sort, user)
    content += (html.mixed_content(data, True),)
    content += html.user_nav(data, user, option, sort)
    return content


def multi_content(data, user, multi, option, sort):
    content = html.multi_menu(option, user, multi)
    content += html.multi_sort_menu(user, multi, option, sort)
    content += (html.mixed_content(data, True),)
    content += html.multi_nav(data, user, multi, option, sort)
    return content
