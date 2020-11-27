<div class="css-slider-mask">
  <ul class="css-slider with-responsive-images">
    % for m in media:
    <li class="slide" tabindex="1">
      <span class="slide-outer">
        <span class="slide-inner">
          <span class="slide-gfx">
	    <img class="slider-img" src="/proxy/{{unescape(m)}}" />
	  </span>
	</span>
      </span>
    </li>
    % end
  </ul>
</div>
