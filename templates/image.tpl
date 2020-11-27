% if not defined("url"):
% url =  post["url"]
<a href="{{url}}">{{url}}</a><br/>
% end
% if post["over_18"]  and full:
<label><input type="checkbox" class="nsfw"/><img class="media" src="/proxy/{{post["url"]}}"/></label>
% else:
<img class="media" src="/proxy/{{post["url"]}}"/>
% end