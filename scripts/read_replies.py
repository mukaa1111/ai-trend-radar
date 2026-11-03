# -*- coding: utf-8 -*-
"""텔레그램 봇에 온 내 답장을 받아 wiki/inbox/YYYY-MM-DD.md 에 적어 둔다.

사용법:  python scripts/read_replies.py [--dry-run]
  - 토큰은 환경 변수 RADAR_TELEGRAM_BOT_TOKEN, chat id는 TELEGRAM_CHAT_ID (없으면 프로젝트 폴더 .env 에서 읽음).
  - 마지막으로 읽은 위치는 data/telegram_offset.json 에 기억한다 (저장소에 올라가므로 PC와 클라우드가 같이 쓴다).
  - 내 chat id 가 아닌 곳에서 온 메시지는 기록하지 않고 건너뛴다.
  - 글자 메시지만 다룬다 (사진·파일은 "[사진]"처럼 표시만).
  - --dry-run 이면 파일에 쓰지 않고 offset 도 올리지 않는다 (같은 메시지를 다음에 또 받는다).
  - 텔레그램은 봇이 안 받아 간 메시지를 24시간만 보관한다. 하루 한 번은 돌려야 안 잃는다.

inbox 파일 모양 (docs/wiki/FORMAT.md):
  # 2026-11-04 답장
  ## 처리 전
  - 07:12 · 3 좋았음 팀 공유   <!-- u123456 -->
  ## 처리됨
  (루틴이나 Claude Code가 옮겨 적음)
"""
import io, json, os, re, sys, time, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OFFSET_PATH = os.path.join(ROOT, "data", "telegram_offset.json")
INBOX_DIR = os.path.join(ROOT, "wiki", "inbox")
KST = timezone(timedelta(hours=9))


def load_env():
    env = {}
    p = os.path.join(ROOT, ".env")
    if os.path.exists(p):
        for line in io.open(p, encoding="utf-8"):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    token = (os.environ.get("RADAR_TELEGRAM_BOT_TOKEN") or env.get("RADAR_TELEGRAM_BOT_TOKEN"))
    chat = os.environ.get("TELEGRAM_CHAT_ID") or env.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        sys.exit("RADAR_TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID 가 없습니다 (.env 또는 환경 변수)")
    return token, str(chat)


def api(token, method, **params):
    data = urllib.parse.urlencode(params).encode("utf-8") if params else None
    req = urllib.request.Request("https://api.telegram.org/bot%s/%s" % (token, method), data=data)
    last = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                res = json.load(r)
            if not res.get("ok"):
                raise RuntimeError(res.get("description", res))
            return res["result"]
        except RuntimeError:
            raise
        except Exception as e:
            last = e
            time.sleep(3 * (attempt + 1))
    raise last


def load_offset():
    if os.path.exists(OFFSET_PATH):
        try:
            return int(json.load(io.open(OFFSET_PATH, encoding="utf-8")).get("offset", 0))
        except Exception:
            return 0
    return 0


def save_offset(n):
    with io.open(OFFSET_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({"offset": n, "saved": datetime.now(KST).strftime("%Y-%m-%d %H:%M")}, ensure_ascii=False) + "\n")


def describe(msg):
    """메시지 하나를 한 줄 글자로. 글자가 아니면 종류만 표시."""
    text = msg.get("text") or msg.get("caption") or ""
    kinds = [k for k in ("photo", "document", "voice", "audio", "video", "sticker") if k in msg]
    if kinds:
        text = ("[%s] " % {"photo": "사진", "document": "파일", "voice": "음성", "audio": "오디오", "video": "영상", "sticker": "스티커"}[kinds[0]]) + text
    # 링크를 보냈을 때 텔레그램이 따로 주는 주소(entities)는 text 에 이미 들어 있다.
    return text.replace("\r", " ").replace("\n", " ⏎ ").strip()


def append_inbox(day, lines):
    os.makedirs(INBOX_DIR, exist_ok=True)
    path = os.path.join(INBOX_DIR, day + ".md")
    if os.path.exists(path):
        body = io.open(path, encoding="utf-8").read()
    else:
        body = "# %s 답장\n\n## 처리 전\n\n## 처리됨\n" % day
    head, sep, tail = body.partition("## 처리됨")
    head = head.rstrip("\n") + "\n" + "\n".join(lines) + "\n\n"
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(head + sep + tail)
    return path


def main():
    dry = "--dry-run" in sys.argv
    token, chat = load_env()
    offset = load_offset()
    updates = api(token, "getUpdates", offset=offset, timeout=0, allowed_updates=json.dumps(["message"]))
    got, skipped, per_day = [], 0, {}
    max_id = offset - 1
    for u in updates:
        max_id = max(max_id, int(u["update_id"]))
        m = u.get("message")
        if not m:
            continue
        if str(m.get("chat", {}).get("id")) != chat:
            skipped += 1
            continue
        text = describe(m)
        if not text or text.startswith("/"):          # /start 같은 명령은 기록하지 않음
            continue
        ts = datetime.fromtimestamp(int(m.get("date", 0)), KST)
        day = ts.strftime("%Y-%m-%d")
        per_day.setdefault(day, []).append("- %s · %s   <!-- u%s -->" % (ts.strftime("%H:%M"), text, u["update_id"]))
        got.append((day, text))
    if dry:
        for d, t in got:
            print(d, "|", t)
        print("dry-run: %d건 (기록·offset 변경 없음)" % len(got))
        return
    files = []
    for day in sorted(per_day):
        files.append(os.path.relpath(append_inbox(day, per_day[day]), ROOT))
    if max_id >= offset:
        save_offset(max_id + 1)
    print("replies: %d건 기록%s%s" % (len(got), (" → " + ", ".join(files)) if files else "",
                                     (" · 다른 채팅 %d건 무시" % skipped) if skipped else ""))


if __name__ == "__main__":
    main()
