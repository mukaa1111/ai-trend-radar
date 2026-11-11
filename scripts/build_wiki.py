# -*- coding: utf-8 -*-
"""data/items.json + data/notes.json + briefs/*.md 로 wiki/ 페이지를 다시 그린다.

사용법:  python scripts/build_wiki.py
  - wiki/index.md, wiki/주제/*.md, wiki/실험.md, wiki/메모.md 를 전부 새로 쓴다 (몇 번 돌려도 같은 결과).
  - wiki/주간/, wiki/inbox/ 는 건드리지 않는다.
  - 실험.md 의 [x] 체크와 "→ 결과" 줄은 다시 그릴 때 보존한다 (브리프 파일 이름 기준).
양식은 docs/wiki/FORMAT.md 에 있다.
"""
import sys, glob, io, json, os, re
from datetime import datetime
from collections import OrderedDict, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIKI = os.path.join(ROOT, "wiki")
TOPIC_DIR = os.path.join(WIKI, "주제")
AUTO_NOTE = "> 이 페이지는 `scripts/build_wiki.py`가 자동으로 그립니다. 손으로 고친 내용은 다음 실행 때 사라져요. 반응·메모는 텔레그램 봇 답장으로."

TOPICS = OrderedDict([
    ("AI 트렌드", "새 모델·기능·에이전트·도구·서비스 출시와 \"그래서 내가 뭘 해 볼 수 있나\". 얼리어답터 반응 포함."),
    ("학습·변화관리", "AI/AX 시대의 성인학습·변화관리: 리스킬링, 학습 전이, 저항과 수용, 리더십, 조직문화, AI 리터러시, 측정."),
    ("기술 화제", "AI 때문에 \"예전엔 전문가만 하던 일\"이 갑자기 쉬워진 기술 현상. 일·학습·조직에 뜻하는 것."),
    ("Work redesign", "AI를 넣어 직무·역할·팀을 다시 짜는 방법론과 사례."),
    ("스킬 기반 조직", "AI 시대의 역량 프레임워크·스킬 데이터·직무 정의 재설계."),
    ("학습 방식의 변화", "AI 코치·튜터·시뮬레이션·롤플레이 등 \"가르치는 방식\" 자체가 바뀌는 사례."),
    ("리더·관리자", "관리자 역할 변화, 리더 대상 AI 교육, 임원의 AI 활용 시범."),
    ("측정", "학습 효과·채택률·생산성 지표, 학습 분석, \"교육했는데 안 쓴다\" 문제."),
    ("AI 거버넌스·윤리 교육", "사내 가이드라인, 책임 있는 사용 교육, 에이전트 권한 설계."),
    ("신입·주니어 육성", "AI가 반복 업무를 가져간 뒤의 경력 초기 학습 파이프라인."),
    ("조직문화·심리적 안전감", "실험 문화, 실패 허용, AI 도입 저항의 정서적 측면."),
    ("HR 자체의 AX", "채용·평가·온보딩·교육 운영에 AI를 쓰는 HR 부서 사례."),
])
AREA_ALIAS = {"work redesign": "Work redesign", "work_redesign": "Work redesign"}
LANG = {"en": "영어", "영": "영어", "ko": "한국어", "한": "한국어"}


STALE_DAYS = 7            # 이보다 오래된 '해볼 것'은 찜(keep)하지 않았으면 '지나간 것'으로 내린다


def read_json(path, default):
    if not os.path.exists(path):
        return default
    return json.load(io.open(path, encoding="utf-8"))


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from urlnorm import norm_url               # ? 뒤 글 번호는 살리고 추적용 꼬리표만 무시 (scripts/urlnorm.py)


def topics_of(item):
    out = []
    area = (item.get("area") or "").strip()
    if area:
        name = AREA_ALIAS.get(area.lower(), area)
        if name in TOPICS:
            out.append(name)
    tags = set(item.get("tags") or [])
    if "work_redesign" in tags:
        out.append("Work redesign")
    if tags & {"AI트렌드", "해볼것", "더보기"}:
        out.append("AI 트렌드")
    if "학습변화관리" in tags:
        out.append("학습·변화관리")
    if "기술화제" in tags:
        out.append("기술 화제")
    if "탐색주제" in tags and not out:
        out.append("학습·변화관리")          # 영역 이름이 비어 있는 옛 항목의 안전망
    seen, uniq = set(), []
    for t in out:
        if t not in seen:
            seen.add(t); uniq.append(t)
    return uniq or ["AI 트렌드"]


def short(d):            # 2026-11-03 → 11/03
    return d[5:7] + "/" + d[8:10] if d and len(d) >= 10 else (d or "")


def fmt_item(it, reactions, others):
    lang = LANG.get(it.get("lang"), it.get("lang") or "")
    meta = [it.get("source", ""), lang]
    if it.get("paid"):
        meta.append("[유료]")
    if it.get("coi"):
        meta.append("이해관계: " + it["coi"])
    lines = ["### %s · [%s](%s)" % (short(it["date"]), it["title"].strip(), it["url"]),
             " · ".join(m for m in meta if m)]
    for s in it.get("summary") or []:
        lines.append("- " + s.strip())
    if it.get("why"):
        lines.append("→ 왜 중요한가: " + it["why"].strip())
    if it.get("reaction"):
        lines.append("👀 반응: " + it["reaction"].strip())
    for r in reactions:
        mark = "👍" if r.get("liked", True) else "👎"
        memo = (" " + r["memo"].strip()) if r.get("memo") else ""
        lock = " 🔒" if r.get("private") else ""
        lines.append("%s 내 반응 (%s):%s%s" % (mark, short(r.get("date", "")), memo, lock))
    if others:
        lines.append("같이 보기: " + " · ".join("[[%s]]" % o for o in others))
    return "\n".join(lines)


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text.rstrip() + "\n")


def build_topics(items, notes):
    by_url = defaultdict(list)
    for r in notes.get("reactions") or []:
        by_url[norm_url(r.get("url"))].append(r)
    pages = defaultdict(list)
    for it in items:
        ts = topics_of(it)
        for t in ts:
            pages[t].append((it, [o for o in ts if o != t]))
    counts, latest = {}, {}
    for name, desc in TOPICS.items():
        rows = sorted(pages.get(name, []), key=lambda x: x[0]["date"], reverse=True)
        counts[name] = len(rows)
        latest[name] = rows[0][0]["date"] if rows else ""
        out = ["---", "주제: " + name, "글 수: %d" % len(rows), "마지막 글: " + (latest[name] or "없음"), "---", "",
               "# " + name, "", "> " + desc, "", AUTO_NOTE, ""]
        if not rows:
            out.append("아직 글이 없습니다. 레이더가 이 영역 글을 고르면 여기에 쌓여요.")
        month = None
        for it, others in rows:
            m = it["date"][:7]
            if m != month:
                month = m
                out += ["", "## %s년 %s월" % (m[:4], m[5:7].lstrip("0")), ""]
            out.append(fmt_item(it, by_url.get(norm_url(it["url"]), []), others))
            out.append("")
        write(os.path.join(TOPIC_DIR, name + ".md"), "\n".join(out))
    return counts, latest


# ---------- 실험 ----------

def parse_experiments():
    """briefs/*.md 의 🧪 줄 → [{brief, date, label, text, minutes, article}]
    🧪 다음 줄이 "짧은 이름 — 긴 설명" 꼴이면 짧은 이름을 label로 쓴다 (10/28 이후 루틴 양식)."""
    exps = []
    for f in sorted(glob.glob(os.path.join(ROOT, "briefs", "*.md"))):
        stem = os.path.splitext(os.path.basename(f))[0]
        m = re.search(r"(\d{4}-\d{2}-\d{2})", stem)
        if not m:
            continue
        date = m.group(1)
        lines = io.open(f, encoding="utf-8").read().splitlines()
        titles = {}
        for l in lines:
            mm = re.match(r"^\s*(\d+)\.\s+(.*)$", l)
            if mm:
                titles[mm.group(1)] = mm.group(2).strip()
        for k, l in enumerate(lines):
            if not l.strip().startswith("🧪"):
                continue
            text = lines[k + 1].strip() if k + 1 < len(lines) else ""
            if not text:
                continue
            label = ""
            mm = re.match(r"^(.{4,40}?)\s+[—–-]\s+(.*)$", text)
            if mm:
                label, text = mm.group(1).strip(), mm.group(2).strip()
            art = ""
            mm = re.match(r"^(\d+)번(?:에서|처럼)?[:\s,]", text)
            if mm and mm.group(1) in titles:
                art = titles[mm.group(1)]
                text = re.sub(r"^\d+번(?:에서|처럼)?[:,]?\s*", "", text)
            minutes = ""
            mm = re.search(r"\((\d+)분\)", text)
            if mm:
                minutes = mm.group(1) + "분"
                text = (text[:mm.start()] + text[mm.end():]).strip()
            exps.append({"brief": stem, "date": date, "label": label, "text": text, "minutes": minutes, "article": art})
    return exps


def read_existing_checks(path):
    """기존 실험.md 에서 [x] 와 '→ 결과' 줄을 건진다. 키는 줄 끝의 <!-- brief --> 표식."""
    found = {}
    if not os.path.exists(path):
        return found
    key = None
    for l in io.open(path, encoding="utf-8").read().splitlines():
        m = re.match(r"^- \[( |x)\] .*<!-- (\S+) -->\s*$", l)
        if m:
            key = m.group(2)
            found[key] = {"done": m.group(1) == "x", "result": None}
            continue
        m2 = re.match(r"^\s+→ 결과(?: \((.*?)\))?: (.*)$", l)
        if m2 and key:
            found[key]["result"] = (m2.group(1) or "", m2.group(2))
    return found


def build_experiments(notes):
    path = os.path.join(WIKI, "실험.md")
    exps = parse_experiments()
    existing = read_existing_checks(path)
    by_brief, by_date = {}, {}
    for e in notes.get("experiments") or []:
        if e.get("brief"):
            by_brief[e["brief"]] = e
        elif e.get("date"):
            by_date.setdefault(e["date"], e)
    todo, done_rows, stale_rows, export = [], [], [], []
    latest_day = max([e["date"] for e in exps] or [""])          # 기준일: 가장 최근 브리프 날짜 (몇 번 돌려도 같은 결과)

    def too_old(day):
        try:
            a = datetime.strptime(latest_day, "%Y-%m-%d"); b = datetime.strptime(day, "%Y-%m-%d")
            return (a - b).days > STALE_DAYS
        except ValueError:
            return False
    for e in sorted(exps, key=lambda x: x["brief"], reverse=True):
        n = by_brief.get(e["brief"]) or by_date.get(e["date"])
        prev = existing.get(e["brief"], {})
        label = e["label"] or (n or {}).get("label") or ""
        done = bool(n and (n.get("done") or n.get("result"))) or prev.get("done", False)
        result = None
        if n and n.get("result"):
            result = (short(n.get("done") or ""), n["result"])
        elif prev.get("result"):
            result = prev["result"]
        keep = bool(n and n.get("keep"))
        stale = (not done) and (not keep) and too_old(e["date"])
        export.append({"brief": e["brief"], "date": e["date"], "label": label, "text": e["text"], "minutes": e["minutes"],
                       "article": e["article"], "done": done, "keep": keep, "stale": stale, "result": result[1] if result else "",
                       "resultDate": result[0] if result else "", "private": bool(n and n.get("private"))})
        head = "- [%s] %s · **%s**" % ("x" if done else " ", short(e["date"]), label or e["text"][:30] + "…")
        if e["minutes"]:
            head += " · " + e["minutes"]
        if keep:
            head += " 📌"
        if n and n.get("private"):
            head += " 🔒"
        head += "  <!-- %s -->" % e["brief"]
        sub = "      " + e["text"]
        if e["article"]:
            sub += " (글: " + e["article"] + ")"
        block = [head, sub]
        if result:
            block.append("      → 결과%s: %s" % ((" (%s)" % result[0]) if result[0] else "", result[1]))
        (done_rows if done else stale_rows if stale else todo).append("\n".join(block))
    out = ["# 실험 (오늘 해볼 것)", "",
           "할 것 %d개 · 해 본 것 %d개 · 지나간 것 %d개 · 굵은 글씨만 훑으면 됩니다." % (len(todo), len(done_rows), len(stale_rows)), "",
           "브리프 꼬리의 \"🧪 오늘 해볼 것\"을 모았어요. **할 것에는 최근 %d일 것과 📌 찜한 것만** 남기고, 나머지는 맨 아래 \"지나간 것\"으로 내려요." % STALE_DAYS,
           "봇에 \"실험 찜\"이라고 답하면 📌가 붙어 계속 남고, \"실험 했음: 결과…\"라고 답하거나 `[ ]`를 `[x]`로 바꾸면 해 본 것으로 가요.", "",
           AUTO_NOTE.replace("손으로 고친 내용은 다음 실행 때 사라져요.", "체크 표시와 → 결과 줄은 보존돼요."), "",
           "## 할 것 (%d)" % len(todo), ""]
    out += todo or ["없음"]
    out += ["", "## 해 본 것 (%d)" % len(done_rows), ""]
    out += done_rows or ["아직 없음"]
    out += ["", "## 지나간 것 (%d)" % len(stale_rows), "", "일주일 넘게 안 한 것. 다시 하고 싶으면 봇에 \"실험 11/3 찜\"처럼 날짜와 함께 답하세요.", ""]
    out += stale_rows or ["없음"]
    write(path, "\n".join(out))
    # 폰 웹페이지("내 것" 탭)가 읽는 사본. wiki/ 안에 두어 루틴 커밋에 같이 들어가게 한다.
    with io.open(os.path.join(WIKI, "실험.json"), "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(export, ensure_ascii=False, indent=1) + "\n")
    return len(exps), len(done_rows)


def build_memos(notes):
    memos = sorted(notes.get("memos") or [], key=lambda m: m.get("date", ""), reverse=True)
    out = ["# 메모", "", "봇에 보낸 자유 메모예요 (글 반응·실험 결과가 아닌 것). 새 것이 위.", "", AUTO_NOTE, ""]
    if not memos:
        out.append("아직 메모가 없습니다. 텔레그램 봇에 아무 말이나 보내면 여기에 쌓여요.")
    for m in memos:
        out.append("- %s · %s%s" % (short(m.get("date", "")), m.get("text", "").strip(), " 🔒" if m.get("private") else ""))
    write(os.path.join(WIKI, "메모.md"), "\n".join(out))
    return len(memos)


def build_index(items, counts, latest, exp_n, exp_done, memo_n):
    weeks = sorted(glob.glob(os.path.join(WIKI, "주간", "*.md")), reverse=True)
    dates = sorted({i["date"] for i in items})
    out = ["# AI 트렌드 위키", "",
           "레이더가 매일 고른 글을 주제별로 쌓아 둔 곳. 글 %d건 · %s ~ %s" % (len(items), dates[0] if dates else "", dates[-1] if dates else ""), "",
           AUTO_NOTE, "", "## 주제", "", "| 주제 | 글 수 | 마지막 글 |", "|---|---|---|"]
    for name in TOPICS:
        out.append("| [[%s]] | %d | %s |" % (name, counts[name], latest[name] or "-"))
    out += ["", "## 내 것", "",
            "- [[실험]] : 오늘 해볼 것 %d개, 해 본 것 %d개" % (exp_n, exp_done),
            "- [[메모]] : %d개" % memo_n, "", "## 주간 모아보기", ""]
    if weeks:
        for w in weeks[:12]:
            n = os.path.splitext(os.path.basename(w))[0]
            out.append("- [[주간/%s|%s]]" % (n, n))
    else:
        out.append("아직 없습니다. 월요일 아침 루틴이 지난주 변화를 적습니다 (4단계).")
    out += ["", "## 보는 법", "",
            "- PC: 옵시디언에서 이 `wiki` 폴더를 금고로 연다.",
            "- 폰: https://mukaa1111.github.io/ai-trend-radar/ 의 \"주제별\" 탭.",
            "- 글 데이터는 `data/items.json`, 내 반응·메모는 `data/notes.json`. 양식은 `docs/wiki/FORMAT.md`."]
    write(os.path.join(WIKI, "index.md"), "\n".join(out))


def main():
    items = read_json(os.path.join(ROOT, "data", "items.json"), [])
    notes = read_json(os.path.join(ROOT, "data", "notes.json"), {})
    os.makedirs(os.path.join(WIKI, "주간"), exist_ok=True)
    os.makedirs(os.path.join(WIKI, "inbox"), exist_ok=True)
    counts, latest = build_topics(items, notes)
    exp_n, exp_done = build_experiments(notes)
    memo_n = build_memos(notes)
    build_index(items, counts, latest, exp_n, exp_done, memo_n)
    print("wiki ok: 글 %d건 → %s · 실험 %d(해 본 것 %d) · 메모 %d" % (
        len(items), ", ".join("%s %d" % (k, v) for k, v in counts.items() if v), exp_n, exp_done, memo_n))


if __name__ == "__main__":
    main()
