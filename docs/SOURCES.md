# 출처 목록 (SOURCES)

작성일: 2026-10-16 · **2026-11-11 정리: 돌아보는 방법을 셋으로 나눔** (매일 열기 / 검색만 / 월요일만). 한 줄 추가·삭제하면 다음 브리프부터 반영됩니다.

## 읽는 법 ("방법" 칸)
| 방법 | 뜻 |
|---|---|
| **매일** | 매일 아침 주소를 직접 연다(WebFetch). 적힌 주소가 RSS(글 목록 파일)이면 최신 글 제목·날짜가 한 번에 보인다. 못 열면 `site:도메인` 검색 1회로 대체하고 "못 연 출처"에 적는다 |
| **검색** | 직접 열면 항상 막히는 곳. 열어 보지 말고 **검색 1회**(`site:도메인 + 이번 주 주제어`)만 한다. 못 연 출처로 세지 않는다 |
| **월요일** | 새 글이 드문 곳. **월요일 브리프 때만** 연다 (다른 요일엔 건너뛴다) |
| 아니오 | 쓰지 않음 |

하루에 같은 출처에서 2건 이상 고르지 않고, 최근 7일에 3건 이상 실린 출처는 다른 출처를 먼저 본다(`python3 scripts/pick_hints.py`가 알려 준다).
2026-11-11 점검: RSS 주소로 바꾸니 OpenAI·Google AI·DeepMind·McKinsey·Product Hunt·Ben's Bites가 열림. ATD·Gartner·Ars Technica·The Verge·미라클레터·요즘IT는 어느 주소로도 안 열려 "검색"으로 돌림.

## A. AI 트렌드 (새 모델·기능·서비스 출시, "그래서 뭘 해 볼까"의 재료)
| 이름 | 주소 | 언어 | 메모 | 방법 |
|---|---|---|---|---|
| Anthropic News | https://www.anthropic.com/news | 영 | Claude 제작사. 자사 발표는 사실로만, 효과 평가 근거로 쓰지 않음 | 매일 |
| OpenAI News | https://openai.com/news/rss.xml | 영 | 자사 발표. 옛 주소(openai.com/news/)는 403, 이 RSS는 열림. 개별 글이 403이면 Simon Willison·The Batch 글로 확인 | 매일 |
| Google DeepMind Blog | https://deepmind.google/blog/rss.xml | 영 | 자사 발표. RSS에 날짜가 있음 | 매일 |
| Google AI Blog | https://blog.google/technology/ai/rss/ | 영 | Gemini·Workspace 기능 소식. RSS에 날짜가 있음 | 매일 |
| Simon Willison | https://simonwillison.net/atom/everything/ | 영 | 새 모델·도구를 직접 써 본 기록, "해볼 것" 재료 | 매일 |
| GeekNews (핵심 출처) | https://news.hada.io/ | 한 | 국내 개발자 커뮤니티. **매일 반드시** 첫 화면을 읽고, AI 관련 글은 토론 페이지(댓글)까지 열어 반응을 본다 | 매일 |
| The Batch (DeepLearning.AI) | https://www.deeplearning.ai/the-batch/ | 영 | 주간(금요일), 균형 잡힌 요약 | 매일 |
| Import AI (Jack Clark) | https://importai.substack.com/archive | 영 | 저자는 Anthropic 공동창업자 — 표시할 것 | 매일 |
| Microsoft AI Blog | https://news.microsoft.com/source/topics/ai/feed/ | 영 | Copilot·업무용 기능. 새 글이 드묾(11/11 기준 최신이 3주 전) | 월요일 |

## B. AI × 일·학습 (연구·조사, work redesign)
| 이름 | 주소 | 언어 | 메모 | 방법 |
|---|---|---|---|---|
| One Useful Thing (Ethan Mollick) | https://www.oneusefulthing.org/feed | 영 | AI와 일·교육. 가장 정독할 만한 출처 | 매일 |
| MIT Sloan Management Review | https://sloanreview.mit.edu/feed/ | 영 | AI와 조직 연구. 일부 유료. AI와 무관한 글이 섞여 있으니 제목으로 거른다 | 매일 |
| HBR — AI & 일 | https://hbr.org/topic/subject/ai-and-machine-learning | 영 | 공개 요약까지만. 유료 벽 표시 | 매일 |
| Stanford HAI | https://hai.stanford.edu/news | 영 | 연구·정책, AI Index (RSS는 비어 있어 이 주소 그대로) | 매일 |
| Charter (Work) | https://www.charterworks.com/feed/ | 영 | AI와 일의 재설계 뉴스레터 | 매일 |
| McKinsey Insights | https://www.mckinsey.com/insights/rss | 영 | 전체 글 RSS. 조직·인재·AI 글만 제목으로 고른다. 자문업 표시 | 월요일 |
| Microsoft WorkLab / Work Trend Index | https://www.microsoft.com/en-us/worklab | 영 | 일하는 방식 조사. MS 자사 자료 표시. 목록에 날짜가 없어 개별 글을 열어 확인 | 월요일 |
| Anthropic Economic Index | https://www.anthropic.com/economic-index | 영 | 실제 AI 사용 데이터로 본 업무 변화. 갱신이 드묾 | 월요일 |

## C. HRD · L&D · 변화관리
| 이름 | 주소 | 언어 | 메모 | 방법 |
|---|---|---|---|---|
| Josh Bersin | https://joshbersin.com/feed/ | 영 | HR 자문·교육 사업 병행 — 표시 | 매일 |
| Chief Learning Officer | https://www.chieflearningofficer.com/feed/ | 영 | 기업교육 현장 사례 | 매일 |
| HR Dive | https://www.hrdive.com/feeds/news/ | 영 | HR 실무 뉴스(2026-11-11 추가, 그동안 검색으로 자주 걸리던 곳). 노동법·정치 기사는 빼고 AI·학습·채용 운영 글만 | 매일 |
| ATD (Association for Talent Development) | td.org | 영 | L&D 실무. 직접 접속 403 → `site:td.org AI learning` 검색 | 검색 |
| Gartner HR | gartner.com | 영 | 직접 접속 403, 대부분 유료 → `site:gartner.com HR AI` 검색, 공개 요약까지만 | 검색 |
| RedThread Research | https://redthreadresearch.com/ | 영 | L&D·스킬 리서치. 목록에 날짜 없음, 회원 전용 많음 | 월요일 |
| Donald H Taylor | https://donaldhtaylor.co.uk/ | 영 | L&D 글로벌 센티먼트 조사 | 월요일 |
| Deloitte Human Capital | https://www.deloitte.com/us/en/insights/topics/talent/human-capital-trends.html | 영 | 연 1회 대형 보고서 + 수시 글. 자문업 표시 | 월요일 |

## D. 국내
| 이름 | 주소 | 언어 | 메모 | 방법 |
|---|---|---|---|---|
| AI타임스 | https://www.aitimes.com/rss/allArticle.xml | 한 | 국내 AI 뉴스, 기업 도입 사례. 주가·투자 기사는 뺀다 | 매일 |
| 요즘IT | yozm.wishket.com | 한 | AI 도구 활용·일하는 방식·"써 봤다" 후기. 클라우드에서는 RSS도 405로 막힘(11/11 시험) → `site:yozm.wishket.com AI` 검색 | 검색 |
| 디스콰이엇 | https://disquiet.io/ | 한 | 국내 메이커들이 만든 제품 올리는 곳. 한국 새 AI 서비스와 반응 | 매일 |
| HR Insight | hrinsight.co.kr | 한 | 국내 HR 월간지. 직접 열면 한글이 깨짐 → `site:hrinsight.co.kr AI` 검색 | 검색 |
| 미라클레터 | mk.co.kr | 한 | 매일경제, 실리콘밸리 AI 소식. 직접 접속 차단 → `미라클레터 + 주제` 검색 | 검색 |

## E. 보완 검색 (출처 밖 좋은 글 잡기)
매일 아래 키워드로 웹 검색을 3~5개 하고, 최근 7일 안의 글만 봅니다.
- "AI upskilling reskilling survey 2026", "AI change management case study", "AI literacy training results"
- "생성형 AI 조직 변화관리 사례", "AI 리터러시 교육 사례 기업", "AX 교육 사례"
- 오늘의 탐색 영역 이름으로 2개 (예: "skills-based organization AI case", "AI 신입 육성 사례")
- 새 모델·기능이 나온 날: "<모델명> for HR / L&D / training" (그래서 뭘 해 볼까)

## F. 요즘 기술 화제 (브리프 맨 아래 "기술 화제 1건" 코너용)
| 이름 | 주소 | 언어 | 메모 | 방법 |
|---|---|---|---|---|
| Hacker News (상위 글) | https://news.ycombinator.com/best | 영 | 개발자들이 가장 많이 본 글. 댓글 수 많은 AI 관련 글 위주 | 매일 |
| 404 Media | https://www.404media.co/ | 영 | AI 악용·카피·해킹 현상 취재. 일부 유료 | 매일 |
| GeekNews | https://news.hada.io/ | 한 | A에서 이미 읽음. 국내에서 화제가 된 기술 글 | (A와 같음) |
| Ars Technica — AI | arstechnica.com | 영 | 직접 접속 차단 → `site:arstechnica.com AI` 검색 | 검색 |
| The Verge — AI | theverge.com | 영 | 직접 접속 차단 → `site:theverge.com AI` 검색 | 검색 |
| Reddit r/artificial · 클리앙·디시 | — | 혼합 | 직접 수집 안 함 | 아니오 |

기술 화제 보완 검색 (최근 7일, 2~3개): "AI reverse engineering", "vibe coded clone app", "AI generated patch bug",
"AI 리버스 엔지니어링", "바이브 코딩 화제"

## G. 새 AI 서비스 · 얼리어답터 반응 (AI 트렌드 코너의 재료)
| 이름 | 주소 | 언어 | 메모 | 방법 |
|---|---|---|---|---|
| Hacker News — Show HN | https://hnrss.org/show?points=100 | 영 | 100점 넘은 Show HN만 모은 RSS. 댓글 주소가 같이 나온다(댓글이 곧 얼리어답터 반응) | 매일 |
| Product Hunt | https://www.producthunt.com/feed | 영 | 그날 출시된 제품 RSS. AI 제품만 고른다 | 매일 |
| Ben's Bites | https://www.bensbites.com/feed | 영 | AI 제품·도구 뉴스레터, 가볍고 빠름 | 매일 |
| YouTube·X(트위터) | — | 혼합 | 직접 수집 안 함. 서비스 이름 + "후기" / "review" 검색으로만 | 아니오 |

새 서비스·반응 보완 검색 (최근 7일, 2~3개): "<서비스명> 후기", "<서비스명> review early adopters",
"새로 나온 AI 서비스 써봤다", "AI 에이전트 앱 후기" (예: 피클 → "피클 AI 에이전트 후기")

## 나중에 검토할 후보 (지금은 안 씀)
- Latent Space, Every (Dan Shipper) — 개발자·빌더 성향이 강함
- NBER 논문 (w31161, w33795, w33641) — 월 1회 직접 읽기용
- LinkedIn의 Ravin Jesuthasan, Lynda Gratton 글 — 로그인 필요해 자동 수집 어려움
