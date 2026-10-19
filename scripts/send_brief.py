# -*- coding: utf-8 -*-
"""브리프 파일을 텔레그램으로 보낸다 (굵게·기울임·숨긴 링크로 꾸며서).

사용법:  python scripts/send_brief.py [briefs/2026-10-19.md] [--dry-run]
  - 파일을 안 주면 오늘 날짜(한국 시간) 파일을 보낸다.
  - --dry-run 이면 보내지 않고 변환 결과만 출력한다.
  - 토큰은 환경 변수 RADAR_TELEGRAM_BOT_TOKEN (없으면 TELEGRAM_BOT_TOKEN), chat id는 TELEGRAM_CHAT_ID 를 먼저 보고,
    없으면 프로젝트 폴더의 .env 파일에서 읽는다.
    (클라우드 환경에는 '주말 뭐하지?' 봇의 TELEGRAM_BOT_TOKEN이 이미 있어서, 이 봇은 RADAR_ 이름을 따로 쓴다)
  - 4,000자가 넘으면 글 단위로 여러 통으로 나눠 보낸다.

꾸밈 규칙 (docs/FORMAT.md 양식을 전제로 함):
  - 글 제목 줄 "1. 제목"  → 태그 색 이모지 + 굵게. 다음 줄이 "(영어 원제)"면 뺀다.
  - 출처 줄 "출처 · 언어 · 분량 … #태그" → 기울임, #태그는 지움
  - "→ 왜 중요한가: …" → "💡 …"
  - "🔗 주소" → "원문 보기"에 링크 숨김. 다른 줄의 주소도 "링크"로 숨김
  - 꼬리 코너(📎 🧪 🔥 📂) 제목은 굵게. "---" 아래(못 연 출처)는 보내지 않는다.
"""
import io, json, os, re, sys, time, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIMIT = 4000
TAG_EMOJI = {"work_redesign": "🟠", "해볼것": "🟢", "학습변화관리": "🔵", "기술화제": "🟣", "더보기": "⚪"}
TAG_LABEL = {"work_redesign": "work redesign", "해볼것": "해볼 것", "학습변화관리": "학습·변화관리", "기술화제": "기술 화제", "더보기": "더 보기"}
URL_RE = re.compile(r"https?://[^\s<>\"')\]]+")
TAIL_HEADS = ("📎", "🧪", "🔥", "📂")


def load_env():
    env = {}
    p = os.path.join(ROOT, ".env")
    if os.path.exists(p):
        for line in io.open(p, encoding="utf-8"):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    token = (os.environ.get("RADAR_TELEGRAM_BOT_TOKEN") or env.get("RADAR_TELEGRAM_BOT_TOKEN")
             or os.environ.get("TELEGRAM_BOT_TOKEN") or env.get("TELEGRAM_BOT_TOKEN"))
    chat = os.environ.get("TELEGRAM_CHAT_ID") or env.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        sys.exit("RADAR_TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID 가 없습니다 (.env 또는 환경 변수)")
    return token, chat


def today_kst():
    return datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def link(url, label):
    return '<a href="%s">%s</a>' % (esc(url), esc(label))


def linkify(text, label="링크"):
    """줄 안의 주소를 '링크' 글자로 바꾼다 (HTML 이스케이프 포함)."""
    out, pos = [], 0
    for m in URL_RE.finditer(text):
        out.append(esc(text[pos:m.start()]))
        out.append(link(m.group(0), label))
        pos = m.end()
    out.append(esc(text[pos:]))
    return "".join(out)


def split_blocks(path):
    """파일을 머리 / 글 블록들 / 꼬리 블록들 로 나눈다. 각 블록은 줄 목록."""
    lines = io.open(path, encoding="utf-8").read().splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    head, items, tails = [], [], []
    cur, mode = None, "head"
    for raw in lines:
        line = raw.rstrip()
        if line.strip() == "---":
            break                                   # 못 연 출처 등 기록용 꼬리는 안 보냄
        s = line.strip()
        if re.match(r"^\d+\.\s", s):
            cur = [s]; items.append(cur); mode = "item"; continue
        if s.startswith(TAIL_HEADS):
            cur = [s]; tails.append(cur); mode = "tail"; continue
        if mode == "head":
            head.append(s)
        elif cur is not None:
            cur.append(s)
    return head, items, tails


def fmt_head(head):
    out = []
    for i, s in enumerate(l for l in head if l):
        out.append("<b>%s</b>" % esc(s) if i == 0 else "<i>%s</i>" % esc(s))
    return "\n".join(out)


def fmt_item(block):
    title = block[0]
    # 제목 끝에 붙은 "(영어 원제)"는 뗀다 (괄호 안이 한글 없는 경우만)
    title = re.sub(r"\s*\(([^()]*[A-Za-z][^()]*)\)\s*(\[유료\])?$",
                   lambda m: (" " + m.group(2)) if m.group(2) else "",
                   title) if not re.search(r"\([^()]*[가-힣][^()]*\)\s*(\[유료\])?$", title) else title
    body = block[1:]
    # 영어 원제 줄 제거
    if body and body[0].startswith("(") and body[0].endswith(")"):
        body = body[1:]
    # 태그 찾기
    tag = None
    for s in body:
        m = re.search(r"#(work_redesign|해볼것|학습변화관리|기술화제|더보기)\b", s)
        if m:
            tag = m.group(1); break
    out = []
    emoji = TAG_EMOJI.get(tag, "▪️")
    out.append("%s <b>%s</b>" % (emoji, esc(title)))
    meta_done = False
    for s in body:
        if not s:
            continue
        s2 = re.sub(r"\s*#(work_redesign|해볼것|학습변화관리|기술화제|더보기)\b", "", s).strip()
        if not meta_done and not s2.startswith(("•", "→", "🔗")):
            if tag:
                s2 = TAG_LABEL[tag] + " · " + s2
            out.append("<i>%s</i>" % linkify(s2)); meta_done = True
        elif s2.startswith("•"):
            out.append("• " + linkify(s2[1:].strip()))
        elif s2.startswith("→"):
            s2 = re.sub(r"^→\s*(왜 중요한가|일·학습·조직에 뜻하는 것)\s*:\s*", "", s2)
            out.append("💡 " + linkify(s2.lstrip("→ ").strip()))
        elif s2.startswith("🔗"):
            m = URL_RE.search(s2)
            out.append(link(m.group(0), "원문 보기 →") if m else esc(s2))
        else:
            out.append(linkify(s2))
    return "\n".join(out)


def fmt_tail(block):
    head = block[0]
    out = ["<b>%s</b>" % esc(head)]
    for s in block[1:]:
        if not s:
            continue
        if s.startswith("→"):
            s = re.sub(r"^→\s*(왜 중요한가|일·학습·조직에 뜻하는 것)\s*:\s*", "", s)
            out.append("💡 " + linkify(s.lstrip("→ ").strip()))
        elif s.startswith("•"):
            out.append("• " + linkify(s[1:].strip()))
        elif URL_RE.fullmatch(s):
            out.append(link(s, "기사 보기 →"))
        else:
            out.append(linkify(s, "보기"))
    return "\n".join(out)


def build_messages(path, limit=LIMIT):
    head, items, tails = split_blocks(path)
    chunks = [fmt_head(head)] + [fmt_item(b) for b in items] + [fmt_tail(b) for b in tails]
    chunks = [c for c in chunks if c.strip()]
    msgs, cur = [], ""
    for c in chunks:
        cand = (cur + "\n\n" + c) if cur else c
        if len(cand) <= limit:
            cur = cand
        else:
            if cur:
                msgs.append(cur)
            cur = c
    if cur:
        msgs.append(cur)
    return msgs


def send(token, chat, html):
    data = urllib.parse.urlencode({
        "chat_id": chat,
        "text": html,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode("utf-8")
    req = urllib.request.Request("https://api.telegram.org/bot%s/sendMessage" % token, data=data)
    last = None
    for attempt in range(3):                      # 네트워크가 잠깐 끊기면 최대 3번 시도
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                res = json.load(r)
            if not res.get("ok"):
                raise RuntimeError(res)
            return
        except RuntimeError:
            raise
        except Exception as e:                    # SSL/연결 오류 등
            last = e
            time.sleep(3 * (attempt + 1))
    raise last


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    path = args[0] if args else os.path.join(ROOT, "briefs", today_kst() + ".md")
    if not os.path.exists(path):
        sys.exit("브리프 파일이 없습니다: %s" % path)
    msgs = build_messages(path)
    n = len(msgs)
    if dry:
        for i, m in enumerate(msgs, 1):
            print("===== 메시지 %d/%d (%d자) =====" % (i, n, len(m)))
            print(m)
        return
    token, chat = load_env()
    for i, m in enumerate(msgs, 1):
        head = "<i>(%d/%d)</i>\n" % (i, n) if n > 1 else ""
        send(token, chat, head + m)
    print("sent %d message(s) from %s" % (n, os.path.basename(path)))


if __name__ == "__main__":
    main()
