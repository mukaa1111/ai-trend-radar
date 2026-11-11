# -*- coding: utf-8 -*-
"""주소 두 개가 '같은 글'인지 비교할 때 쓰는 공통 규칙.

같은 글로 보는 차이:  http/https, www. / m., :443 / :80, 맨 끝 /, # 뒤, 추적용 꼬리표(utm_*, fbclid, gclid, ref, ref_src, source)
다른 글로 보는 차이:  ? 뒤의 나머지 값 (예: aitimes.com/...?idxno=217019, news.ycombinator.com/item?id=…, news.hada.io/topic?id=…)
index.html 의 normUrl 과 같은 규칙이어야 한다.
"""
import re

_TRACK = re.compile(r"^(utm_[^=]*|fbclid|gclid|ref|ref_src|source)(=|$)")


def norm_url(u):
    u = (u or "").strip().lower()
    u = re.sub(r"#.*$", "", u)
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^(www\.|m\.)", "", u)
    u = re.sub(r"^([^/?]+):(443|80)(?=[/?]|$)", r"\1", u)
    path, sep, query = u.partition("?")
    path = path.rstrip("/")
    if sep:
        keep = [p for p in query.split("&") if p and not _TRACK.match(p)]
        if keep:
            return path + "?" + "&".join(keep)
    return path


if __name__ == "__main__":
    tests = [
        ("https://www.aitimes.com/news/articleView.html?idxno=217019", "https://m.aitimes.com:443/news/articleView.html?idxno=217019", True),
        ("https://www.aitimes.com/news/articleView.html?idxno=217019", "https://www.aitimes.com/news/articleView.html?idxno=217084", False),
        ("https://news.ycombinator.com/item?id=1", "https://news.ycombinator.com:443/item?id=1#c", True),
        ("https://hbr.org/2026/11/x/", "http://hbr.org/2026/11/x?utm_source=rss&ref=home", True),
        ("https://news.hada.io/topic?id=36684", "https://news.hada.io/topic?id=36135", False),
    ]
    for a, b, same in tests:
        assert (norm_url(a) == norm_url(b)) == same, (a, b, norm_url(a), norm_url(b))
    print("urlnorm ok")
