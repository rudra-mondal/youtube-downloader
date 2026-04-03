import re

class DownloaderAppLogic:
    @staticmethod
    def detect_video_platform(link): # Unchanged
        fb_watch_pattern = r"^(https?://)?fb\.watch/.*"; pin_it_pattern = r"^(https?://)?pin\.it/.*"
        if re.match(pin_it_pattern, link, re.IGNORECASE): return "pinterest"
        if re.match(fb_watch_pattern, link, re.IGNORECASE): return "facebook"
        facebook_patterns=[r"^(https?://)?(www\.|m\.)?facebook\.com/(.*)?(videos|reel|watch|live|posts|story\.php|video/embed|v|photos|groups/.*/(permalink/\d+|.*)|events/.*/(permalink/\d+|.*)|share/(v|r)/.*|share/.*)/.*"]
        youtube_patterns=[r"^(https?://)?(www\.|m\.)?(youtube\.com/(watch\?v=|embed/|v/|shorts/|c/|user/|channel/|live/|playlist\?list=|attribution_link\?)|youtu\.be/).*",r"^(https?://)?(www\.)?youtube-nocookie\.com/embed/.*"]
        pinterest_patterns=[r"^(https?://)?(www\.)?pinterest\.(com|ca|co\.uk|de|fr|es|it|jp|com\.au|com\.br|ch|at|be|dk|fi|ie|kr|mx|nl|no|nz|ph|pt|ru|se|sg)\/pin\/(\d+)\/?.*"]
        for p in pinterest_patterns:
            if re.match(p,link,re.IGNORECASE): return "pinterest"
        for p in facebook_patterns:
            if re.match(p,link,re.IGNORECASE): return "facebook"
        for p in youtube_patterns:
            if re.match(p,link,re.IGNORECASE): return "youtube"
        return None
