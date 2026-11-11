# -*- coding: utf-8 -*-
"""글을 고르기 전에 읽는 힌트 세 가지를 출력한다 (아무것도 바꾸지 않는다).

사용법:  python scripts/pick_hints.py
  1) 내 취향   — 최근 45일 동안 내가 봇에 답한 반응(👍/👎, 메모)과 직접 저장한 글.
                 같은 조건이면 👍와 비슷한 주제·출처·형태를 먼저 고르고, 👎와 비슷한 글은 피한다.
  2) 출처 쏠림 — 최근 7일 동안 출처별로 몇 건 실었는지. 3건 이상이면 오늘은 다른 출처를 먼저 본다.
  3) 탐색 영역 — 최근 7일에 다룬 영역과 안 다룬 영역. 오늘 탐색 주제는 안 다룬 영역에서 고른다.
재료: data/items.json, data/notes.json
"""
import io, json, os, re, sys, collections
from datetime import datetime, timedelta, timezone, date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KST = timezone(timedelta(hours=9))
AREAS = ["Work redesign", "스킬 기반 조직", "학습 방식의 변화", "리더·관리자", "측정",
         "AI 거버넌스·윤리 교육", "신입·주니어 육성", "조직문화·심리적 안전감", "HR 자체의 AX"]
TAG_LABEL = {"AI트렌드": "AI 트렌드", "학습변화관리": "학습·변화관리", "탐색주제": "탐색 주제", "해볼것": "해볼 것",
             "기술화제": "기술 화제", "work_redesign": "work redesign", "더보기": "더 보기"}


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from urlnorm import norm_url as norm


def load(name, default):
    p = os.path.join(ROOT, "data", name)
    if not os.path.exists(p):
        return default
    return json.load(io.open(p, encoding="utf-8"))


def src_name(s):
    s = re.sub(r"\s*\(.*?\)", "", s or "")
    return re.split(r"\s*[·|]\s*", s)[0].strip() or "?"


def d(s):
    try:
        return date.fromisoformat((s or "")[:10])
    except ValueError:
        return None


def short(s):
    x = d(s)
    return "%d/%d" % (x.month, x.day) if x else "?"


def main():
    today = datetime.now(KST).date()
    items = load("items.json", [])
    notes = load("notes.json", {})
    by_url = {norm(it.get("url")): it for it in items if it.get("url")}

    # 1) 내 취향
    since = today - timedelta(days=45)
    rs = [r for r in (notes.get("reactions") or []) if d(r.get("date")) and d(r["date"]) >= since]
    rs.sort(key=lambda r: r["date"], reverse=True)
    print("[1. 내 취향 — 최근 45일 반응 %d건]" % len(rs))
    like_tags, like_src, like_area = collections.Counter(), collections.Counter(), collections.Counter()
    for r in rs:
        it = by_url.get(norm(r.get("url")))
        mark = "👎" if r.get("liked") is False else "👍"
        if it:
            tags = "·".join(TAG_LABEL.get(t, t) for t in it.get("tags", []))
            line = "%s %s %s · %s · %s%s" % (mark, short(r["date"]), it.get("title", ""), src_name(it.get("source")),
                                            tags, (" · 탐색: " + it["area"]) if it.get("area") else "")
            if r.get("liked") is not False:
                like_tags.update(it.get("tags", [])); like_src[src_name(it.get("source"))] += 1
                if it.get("area"):
                    like_area[it["area"]] += 1
        else:
            line = "%s %s %s" % (mark, short(r["date"]), r.get("url", ""))
        if r.get("memo"):
            line += " · 메모: " + r["memo"]
        print("  " + line)
    if not rs:
        print("  (아직 반응 없음 — 기준 문서대로만 고른다)")
    else:
        def top(c):
            return ", ".join("%s %d" % (TAG_LABEL.get(k, k), v) for k, v in c.most_common(4)) or "-"
        print("  → 자주 좋아한 것: 태그 %s / 출처 %s / 영역 %s" % (top(like_tags), top(like_src), top(like_area)))
        print("  → 쓰는 법: 후보가 비슷하게 좋으면 👍와 닮은 쪽을 고른다. 👎와 닮은 글은 뺀다. 구성 비율·중복 금지는 그대로.")
    saved = [it for it in items if "직접 저장" in (it.get("source") or "") and d(it.get("date")) and d(it["date"]) >= since]
    if saved:
        print("  직접 저장한 글 %d건 (강한 관심 신호): %s" % (len(saved), " / ".join(it.get("title", "")[:28] for it in saved[-5:])))

    # 2) 출처 쏠림
    week = today - timedelta(days=7)
    recent = [it for it in items if d(it.get("date")) and d(it["date"]) > week and "직접 저장" not in (it.get("source") or "")]
    cnt = collections.Counter(src_name(it.get("source")) for it in recent)
    print("\n[2. 출처 쏠림 — 최근 7일 %d건]" % len(recent))
    heavy = [(k, v) for k, v in cnt.most_common() if v >= 3]
    print("  " + ", ".join("%s %d" % kv for kv in cnt.most_common(8)))
    if heavy:
        print("  ⚠ 3건 이상: %s → 오늘은 이 출처보다 다른 출처를 먼저 본다 (정말 중요한 소식이면 예외)." % ", ".join(k for k, _ in heavy))
    ko = sum(1 for it in recent if (it.get("lang") or "") in ("한", "한국어", "ko"))
    print("  한국어 글 %d / %d — 0~1건뿐이면 국내 출처(AI타임스·요즘IT·GeekNews·디스콰이엇)를 한 번 더 본다." % (ko, len(recent)))

    # 3) 탐색 영역
    used = collections.Counter(it.get("area") for it in recent if it.get("area"))
    unused = [a for a in AREAS if a not in used]
    last = {}
    for it in items:
        if it.get("area"):
            last[it["area"]] = max(last.get(it["area"], ""), it.get("date", ""))
    unused.sort(key=lambda a: last.get(a, ""))            # 가장 오래 안 다룬 영역이 앞
    print("\n[3. 탐색 영역]")
    print("  최근 7일 다룸: %s" % (", ".join("%s(%d)" % kv for kv in used.items()) or "없음"))
    print("  오늘 후보(오래 안 다룬 순): %s" % (", ".join("%s[%s]" % (a, short(last[a]) if a in last else "처음") for a in unused) or "전부 다룸 → 가장 오래된 영역"))


if __name__ == "__main__":
    main()
