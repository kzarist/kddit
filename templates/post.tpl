<div class="post">
  <div class="sub-header">
  % if full:
  {{!generate_subreddit_link(post["subreddit"])}}
  % end
  <a href="{{post['permalink']}}" >
    <b>{{!post['title']}}</b>
  </a>
  <span class="flair">{{post['link_flair_text'] or ''}}</span>
  <br/>
  by <a href="/u/{{post['author']}}">{{post['author']}}</a> at {{get_created(post)}}
  <br/>
  </div>
  <div>
    {{!content}}
  </div>
</div>
