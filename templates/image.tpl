% if post["thumbnail"] == "nsfw" and full:
<label><input type="checkbox" class="nsfw"/><img class="media" src="/proxy/{{post["url"]}}"/></label>
% else:
<img class="media" src="/proxy/{{post["url"]}}"/>
% end