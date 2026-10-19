# -*- coding: utf-8 -*-
"""브리프 파일을 텔레그램으로 보낸다.

사용법:  python scripts/send_brief.py [briefs/2026-10-19.md]
  - 파일을 안 주면 오늘 날짜(한국 시간) 파일을 보낸다.
  - 토큰·chat id는 환경 변수 TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID 를 먼저 보고,
    없으면 프로젝트 폴더의 .env 파일에서 읽는다.
  - 4,000자가 넘으면 빈 줄 기준으로 여러 통으로 나눠 보낸다.
"""
import io, json, os, sys, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIMIT = 4000


def load_env():
    env = {}
    p = os.path.join(ROOT, ".env")
    if os.path.exists(p):
        for line in io.open(p, encoding="utf-8"):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    token = os.environ.get("TELEGRAM_BOT_TOKEN") or env.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID") or env.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        sys.exit("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID 가 없습니다 (.env 또는 환경 변수)")
    return token, chat


def today_kst():
    return datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")


def body_of(path):
    text = io.open(path, encoding="utf-8").read()
    lines = text.splitlines()
    if lines and lines[0].startswith("# "):   # 파일 제목 줄은 뺀다
        lines = lines[1:]
    return "\n".join(lines).strip()


def split(text, limit=LIMIT):
    parts, cur = [], ""
    for block in text.split("\n\n"):
        cand = (cur + "\n\n" + block) if cur else block
        if len(cand) <= limit:
            cur = cand
        else:
            if cur:
                parts.append(cur)
            cur = block
    if cur:
        parts.append(cur)
    return parts


def send(token, chat, text):
    data = urllib.parse.urlencode({
        "chat_id": chat,
        "text": text,
        "disable_web_page_preview": "true",
    }).encode("utf-8")
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data)
    with urllib.request.urlopen(req, timeout=30) as r:
        res = json.load(r)
    if not res.get("ok"):
        raise RuntimeError(res)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "briefs", today_kst() + ".md")
    if not os.path.exists(path):
        sys.exit(f"브리프 파일이 없습니다: {path}")
    token, chat = load_env()
    parts = split(body_of(path))
    n = len(parts)
    for i, p in enumerate(parts, 1):
        head = f"({i}/{n})\n" if n > 1 else ""
        send(token, chat, head + p)
    print(f"sent {n} message(s) from {os.path.basename(path)}")


if __name__ == "__main__":
    main()
