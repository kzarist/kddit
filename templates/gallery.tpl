<a href="{{post["url"]}}">{{post["url"]}}</a><br/>
<div class="css-slider-mask">
  <ul class="css-slider with-responsive-images">
    % for m in media:
    <li class="slide" tabindex="1">
      <span class="slide-outer">
        <span class="slide-inner">
          <span class="slide-gfx">
	    % if post["over_18"] and full:
	    <label><input type="checkbox" class="nsfw"/><img class="slider-img" src="/proxy/{{unescape(m)}}"/></label>
	    % else:
	    <img class="slider-img" src="/proxy/{{unescape(m)}}" />
	    % end
	  </span>
	</span>
      </span>
    </li>
    % end
  </ul>
</div>
