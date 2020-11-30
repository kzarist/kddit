% title = post["title"] if "title" in post else post["link_title"]
% flair = post["link_flair_text"] if "link_flair_text" in post else None 
<div class="post">
  <div class="sub-header">
    % if full:
    {{!generate_subreddit_link(post["subreddit"])}}
    % end
    <a href="{{post['permalink']}}" >
      <b>{{!title}}</b>
    </a>
    % if flair:
    <span class="flair">{{flair}}</span>
    % end
    <br/>
    By <a href="/u/{{post['author']}}">u/{{post['author']}}</a>
    {{get_time(post)}}<br/>
    {{!generate_awards(post)}}
  </div>
  <hr/>
  <div class="post-content">
    {{!content}}
  </div>
</div>
