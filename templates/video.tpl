% thumbnail = post["thumbnail"]
% poster = f'poster="/proxy/{thumbnail}" ' if thumbnail != "nsfw" else "" 
<video class="media" controls="" {{!poster}}preload="none" src="/proxy/{{post["media"]["reddit_video"]["fallback_url"]}}"/>