# -*- coding: utf-8 -*-
"""텔레그램으로 짧은 글 한 통을 보낸다 (확인 메시지용).

사용법:  python scripts/tg_say.py "보낼 내용"
  - 토큰·chat id는 send_brief.py와 같은 곳(환경 변수 또는 .env)에서 읽는다.
  - 글자만 보낸다 (꾸밈 없음, 링크 미리보기 없음). 4,000자 넘으면 잘라 보낸다.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from send_brief import load_env, esc, send


def main():
    text = " ".join(sys.argv[1:]).strip()
    if not text:
        sys.exit("보낼 내용이 비어 있습니다")
    token, chat = load_env()
    send(token, chat, esc(text[:4000]))
    print("sent")


if __name__ == "__main__":
    main()
