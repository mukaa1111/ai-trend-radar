# -*- coding: utf-8 -*-
"""브리프를 보내기 전에 검사한다.

사용법:  python scripts/check_brief.py briefs/2026-10-28.md
검사 항목:
  (a) data/items.json 이 올바른 JSON인가
  (b) 오늘 브리프의 링크가 최근 30일 안에 이미 보낸 글(오늘 이전 날짜의 items.json 항목)과 겹치는가 → '중복'
  (c) 브리프 길이가 5,500자 안쪽인가 (4,500자 넘으면 경고)
모두 통과하면 'ok' 를 출력하고 0으로 끝난다. 하나라도 걸리면 이유를 출력하고 1로 끝난다.
"""
import io, json, os, re, sys
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL_RE = re.compile(r"https?://[^\s<>\"')\]]+")
LIMIT = 5500          # 이보다 길면 실패
WARN = 4500           # 이보다 길면 경고만


def norm(u):
    u = u.strip().rstrip("/").lower()
    u = re.sub(r"^https?://(www\.)?", "", u)
    u = re.sub(r"[?#].*$", "", u)          # 추적용 꼬리표는 무시
    return u


def main():
    if len(sys.argv) < 2:
        sys.exit("사용법: python scripts/check_brief.py briefs/YYYY-MM-DD.md")
    path = sys.argv[1]
    text = io.open(path, encoding="utf-8").read()
    m = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(path))
    today = date.fromisoformat(m.group(1)) if m else date.today()
    problems = []

    # (a) items.json
    try:
        items = json.load(io.open(os.path.join(ROOT, "data", "items.json"), encoding="utf-8"))
        assert isinstance(items, list)
    except Exception as e:
        print("items.json 오류:", e)
        sys.exit(1)

    # (b) 중복: 오늘 이전 30일 안에 보낸 url
    since = today - timedelta(days=30)
    sent = {}
    for it in items:
        try:
            d = date.fromisoformat(it.get("date", ""))
        except ValueError:
            continue
        if since <= d < today and it.get("url"):
            sent[norm(it["url"])] = (it["date"], it.get("title", ""))
    body = text.split("\n---", 1)[0]          # '못 연 출처' 아래는 제외
    seen = set()
    for u in URL_RE.findall(body):
        n = norm(u)
        if n in sent and n not in seen:
            seen.add(n)
            problems.append("중복: %s 는 %s 브리프에 이미 보냄 (%s)" % (u, sent[n][0], sent[n][1]))

    # (c) 길이
    if len(text) > LIMIT:
        problems.append("길이 초과: %d자 (%d자 안쪽이어야 함)" % (len(text), LIMIT))
    elif len(text) > WARN:
        print("경고: %d자, 목표(%d자)보다 김. 요약을 조금 줄이면 좋음" % (len(text), WARN))

    if problems:
        print("\n".join(problems))
        sys.exit(1)
    print("ok (%d자, 지난 30일 보낸 글 %d건과 겹침 없음)" % (len(text), len(sent)))


if __name__ == "__main__":
    main()
