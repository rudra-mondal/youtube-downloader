import pytest
from platform_utils import DownloaderAppLogic

@pytest.mark.parametrize("url, expected_platform", [
    # YouTube
    ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "youtube"),
    ("https://youtu.be/dQw4w9WgXcQ", "youtube"),
    ("https://m.youtube.com/watch?v=dQw4w9WgXcQ", "youtube"),
    ("https://www.youtube.com/shorts/oHg5SJYRHA0", "youtube"),
    ("https://www.youtube.com/embed/dQw4w9WgXcQ", "youtube"),
    ("https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ", "youtube"),
    ("youtube.com/watch?v=dQw4w9WgXcQ", "youtube"),

    # Facebook
    ("https://fb.watch/xyz123/", "facebook"),
    ("https://www.facebook.com/watch/?v=123456789", "facebook"),
    ("https://www.facebook.com/reel/123456789", "facebook"),
    ("https://www.facebook.com/share/v/xyz123/", "facebook"),
    ("https://www.facebook.com/videos/123456789/", "facebook"),
    ("https://m.facebook.com/story.php/foo", "facebook"),

    # Pinterest
    ("https://pin.it/xyz123", "pinterest"),
    ("https://www.pinterest.com/pin/123456789/", "pinterest"),
    ("https://www.pinterest.ca/pin/123456789/", "pinterest"),
    ("https://www.pinterest.co.uk/pin/123456789/", "pinterest"),
    ("https://www.pinterest.com/pin/123456789/", "pinterest"),

    # Invalid/Unsupported
    ("https://twitter.com/hugo", None),
    ("https://google.com", None),
    ("not a url", None),
    ("", None),
])
def test_detect_video_platform(url, expected_platform):
    assert DownloaderAppLogic.detect_video_platform(url) == expected_platform
