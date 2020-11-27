% if defined("post"):
% url = post["media"]["reddit_video"]["dash_url"]
% end
% if defined("thumbnail"):
<video class="media" poster="/proxy/{{thumbnail}}" controls="" preload="none" src="/video/{{url}}"/>
% else:
<video class="media" controls="" preload="metadata" src="/video/{{url}}"/>
% end