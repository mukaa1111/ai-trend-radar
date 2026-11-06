# -*- coding: utf-8 -*-
"""텔레그램 봇에게 보낸 내 답장을 읽어 글 반응으로 기록한다.

사용법:  python scripts/sync_reactions.py [--dry-run]
  - 봇 대화에서 새로 온 메시지를 읽는다 (Telegram getUpdates, 읽은 자리는 data/tg_offset.json에 저장).
  - "3번 좋아", "2번 별로", "3번 감독능력 글 좋아", "1번 메모: 팀 공유" 처럼 쓰면
    그 메시지를 보낸 날 아침 브리프의 N번 글에 반응을 기록한다 (07:00 전에 보냈으면 전날 브리프).
      좋아/굿/최고/👍/♥/좋네/좋다 → like,  별로/싫/패스/👎/아님 → dislike,  그 외 → note
    숫자 없이 보낸 글은 그날 브리프 전체에 대한 메모로 기록한다.
  - 기록: data/items.json의 해당 글에 my_reaction / my_note / my_reacted_at 를 넣고,
          data/reactions.json 에 한 줄 추가한다.
  - 봇이 "✅ 기록했어요" 라고 답장한다 (--dry-run 이면 답장도 저장도 안 함).
  - /start 같은 명령은 무시한다.
"""
import io, json, os, re, sys, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone, date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from send_brief import load_env, send as tg_send   # 같은 토큰·chat id, 같은 보내기 함수

KST = timezone(timedelta(hours=9))
OFFSET_FILE = os.path.join(ROOT, "data", "tg_offset.json")
ITEMS_FILE = os.path.join(ROOT, "data", "items.json")
REACT_FILE = os.path.join(ROOT, "data", "reactions.json")
LIKE = re.compile(r"(좋아|좋네|좋다|좋았|굿|최고|👍|♥|❤|🔥|유용|도움)")
DISLIKE = re.compile(r"(별로|싫|패스|👎|아님|아니|재미없|약하|글쎄)")
NUM = re.compile(r"(\d+)\s*번")


def norm(u):
    u = u.strip().rstrip("/").lower()
    u = re.sub(r"^https?://(www\.|m\.)?", "", u)
    u = re.sub(r":\d+", "", u, count=1)
    u = re.sub(r"[?#].*$", "", u)
    return u


def load_json(p, default):
    if os.path.exists(p):
        return json.load(io.open(p, encoding="utf-8"))
    return default


def save_json(p, obj):
    io.open(p, "w", encoding="utf-8", newline="\n").write(json.dumps(obj, ensure_ascii=False, indent=1))


def brief_file_for(d):
    """그날 보낸 브리프 중 마지막 것 (YYYY-MM-DD-3.md > -2.md > .md)"""
    base = os.path.join(ROOT, "briefs", d.isoformat())
    cands = [base + "-%d.md" % i for i in (5, 4, 3, 2)] + [base + ".md"]
    for c in cands:
        if os.path.exists(c):
            return c
    return None


def parse_brief(path):
    """{번호: (제목, url)} 를 돌려준다."""
    out, cur = {}, None
    for line in io.open(path, encoding="utf-8"):
        s = line.strip()
        m = re.match(r"^(\d+)\.\s+(.*)$", s)
        if m:
            cur = int(m.group(1)); out[cur] = [m.group(2), ""]
            continue
        if cur and s.startswith("🔗"):
            u = re.search(r"https?://\S+", s)
            if u:
                out[cur][1] = u.group(0)
            cur = None
    return {k: tuple(v) for k, v in out.items()}


def classify(text):
    if LIKE.search(text):
        return "like"
    if DISLIKE.search(text):
        return "dislike"
    return "note"


def main():
    dry = "--dry-run" in sys.argv
    token, chat = load_env()
    offset = load_json(OFFSET_FILE, {}).get("offset", 0)
    q = urllib.parse.urlencode({"offset": offset, "timeout": 0, "allowed_updates": json.dumps(["message"])})
    with urllib.request.urlopen("https://api.telegram.org/bot%s/getUpdates?%s" % (token, q), timeout=30) as r:
        res = json.load(r)
    if not res.get("ok"):
        sys.exit("getUpdates 실패: %s" % res)
    updates = res.get("result", [])
    if not updates:
        print("새 메시지 없음")
        return

    items = load_json(ITEMS_FILE, [])
    by_url = {norm(it["url"]): it for it in items if it.get("url")}
    reactions = load_json(REACT_FILE, [])
    last_id = offset
    recorded, replies = 0, []

    for up in updates:
        last_id = max(last_id, up["update_id"] + 1)
        msg = up.get("message") or {}
        if str((msg.get("chat") or {}).get("id")) != str(chat):
            continue
        text = (msg.get("text") or "").strip()
        if not text or text.startswith("/"):
            continue
        when = datetime.fromtimestamp(msg["date"], KST)
        bday = when.date() if when.hour >= 7 else when.date() - timedelta(days=1)
        bfile = brief_file_for(bday)
        nums = [int(n) for n in NUM.findall(text)]
        kind = classify(text)
        note = NUM.sub("", text).strip(" ,.:·-")

        if not bfile:
            replies.append("❓ %s 브리프를 못 찾아 기록 못 함: \"%s\"" % (bday.strftime("%m/%d"), text))
            continue
        table = parse_brief(bfile)
        if not nums:
            reactions.append({"at": when.isoformat(), "brief": bday.isoformat(), "n": None, "url": "", "title": "",
                              "kind": kind, "note": text})
            replies.append("📝 %s 브리프 전체 메모로 기록: \"%s\"" % (bday.strftime("%m/%d"), text))
            recorded += 1
            continue
        for n in nums:
            if n not in table:
                replies.append("❓ %s 브리프에 %d번 글이 없어요" % (bday.strftime("%m/%d"), n))
                continue
            title, url = table[n]
            it = by_url.get(norm(url))
            if it is not None:
                it["my_reaction"] = kind
                it["my_note"] = note
                it["my_reacted_at"] = when.isoformat()
            reactions.append({"at": when.isoformat(), "brief": bday.isoformat(), "n": n, "url": url, "title": title,
                              "kind": kind, "note": note})
            mark = {"like": "👍", "dislike": "👎", "note": "📝"}[kind]
            replies.append("%s 기록했어요 · %s %d번 \"%s\"%s" % (mark, bday.strftime("%m/%d"), n, title[:40],
                                                           (" · 메모: " + note) if note else ""))
            recorded += 1

    if dry:
        print("\n".join(replies) or "기록할 반응 없음")
        print("(--dry-run: 저장·답장 안 함, offset 유지)")
        return
    save_json(ITEMS_FILE, items)
    save_json(REACT_FILE, reactions)
    save_json(OFFSET_FILE, {"offset": last_id})
    if replies:
        tg_send(token, chat, "\n".join(replies) + "\n\n⭐ 모아 보기: https://mukaa1111.github.io/ai-trend-radar/")
    print("반응 %d건 기록, 답장 %d줄" % (recorded, len(replies)))


if __name__ == "__main__":
    main()
