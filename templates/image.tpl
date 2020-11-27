<a href="{{post["url"]}}">{{post["url"]}}</a><br/>
% if post["over_18"]  and full:
<label><input type="checkbox" class="nsfw"/><img class="media" src="/proxy/{{post["url"]}}"/></label>
% else:
<img class="media" src="/proxy/{{post["url"]}}"/>
% end