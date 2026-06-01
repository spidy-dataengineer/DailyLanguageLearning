# 고도화 계획 — Daily Bilingual Expression Logger (Enhancement Phase)

## Context
기본 시스템(매일 EN10+ZH10 플래시카드 → Notion 2개 DB + 연습, Discord 알림)은 구축·검증 완료.
이제 **지속적 고도화 단계**. 이 plan은 그 로드맵이고, **전체 설계의 source of truth는 `docs/`** 다 —
각 increment를 칠 때 해당 `docs/*.md` + `CLAUDE.md`를 같은 변경에서 갱신한다.

사용자 결정: **Reddit·VOA 제거**, 그리고 4개 고도화(**SRS·오디오·cloze·통계**)를 **전부, 순차 increment**로.

### 작동 원칙 (불변)
- **Python은 I/O만** — 생성은 `/schedule` 루틴의 Claude (LLM API 키 없음).
- **피드백은 Notion으로** — Discord 웹훅은 단방향(버튼 없음).
- EN/ZH 분리; `data_source_id(db_id)` + `pages.create(parent={"type":"data_source_id",...})` 패턴 재사용.
- 기존 헬퍼 재사용: `_page_body` `_callout` `_para` `_practice_body` `notify_discord` `similar` `data_source_id` `existing_rows` `_rich` `_plain` `_select_name`.
- 한 번에 한 increment, 작게 shippable, `git diff`는 그 increment만.

### 확정 기본값 (승인 단계서 조정 가능)
1. 기존 ~24개 행: **유지**(SRS가 첫 `review` 때 지연 백필, 통계에 카운트). 원하면 언제든 archive로 정리.
2. SRS 속성 추가: **코드 기반 `migrate` 모드**(개인PC→GitHub→/schedule 재현성). + 새 `init`엔 스키마 포함.
3. 오디오: **YouGlish 링크(v1)**, edge-tts mp3는 phase 2로 보류.
4. 통계 전달: **review 핑 푸터에 합침** + 온디맨드 `stats` 모드도 둠.

### 확인된 기술 사실 (Plan 에이전트 WebFetch)
- `notion.data_sources.update(data_source_id, properties={...})` = 기존 DB에 컬럼 추가, **기존 행 보존**(2025-09-03 모델, 버전업 불필요).
- Discord `||spoiler||` 웹훅 `content`에서 작동 — 단 **코드블록 안에선 안 됨**(평문으로).
- `_EXPR_SCHEMA_BASE`에 **`Audio`(url) 이미 존재**하나 미사용 → increment 2가 바로 활용.

---

## Increment 0 — Reddit·VOA 제거 (의존성 0, 삭제만)
- `daily_notion.py`: `EN_SOURCES`(L31)에서 `"VOA"`,`"Reddit"` 제거 · `EN_SUBREDDITS`(L33) 삭제 · `fetch("en")` candidates(L174–176)에서 `"voa"`,`"reddit"` 제거.
- `sources.py`: `voa_words_stories()` · `reddit_hot()` · `VOA_RSS`/`VOA_RSS_URL`(L47–49) · "Reddit is the only fetcher…" 문장 삭제. (`import praw`는 reddit_hot 내부라 같이 사라짐.)
- `requirements.txt`: `praw>=7.7` 제거. `.env.example`: `REDDIT_CLIENT_ID`/`SECRET`/`VOA_RSS_URL` 줄 제거.
- `routine_prompt.md`: 영어 우선순위 "`bbc / voa / lukes / reddit`" → "`bbc / lukes`".
- docs: `sources.md`(영어표서 VOA·Reddit 행 삭제), `overview.md`(소스목록·로드맵), `deployment.md`(Reddit creds 체크 제거), `CLAUDE.md`(Status의 "Reddit creds →" 제거).
- Notion 스키마: 손대지 않음(미사용 select 옵션 잔존은 무해). 기존 행 영향 없음.
- **검증**: `fetch en` 정상 + JSON에 voa/reddit 키 없음; `reddit|voa|praw` Grep 결과 없음.

## Increment 1 — SRS 복습 루프 + Discord 스포일러 퀴즈 (유일한 스키마 변경, 최고 ROI)
- **스킴**: Leitner 박스 1→5, 간격 **1/3/7/16/35일**. 신규=박스1, `Next review=today+1`. 피드백은 Notion `Recall` select(`Got it`→박스+1, `Forgot`→1). due = `Next review<=today` 또는 빈값.
- **스키마(EN·ZH 둘 다, `data_sources.update`)**: `Box`(number) · `Next review`(date) · `Recall`(select: Got it/Forgot — 사용자가 만지는 유일한 필드) · `Last reviewed`(date). 4개를 `_EXPR_SCHEMA_BASE`에도 추가.
- **기존 행 백필**: `migrate` 후 빈 `Box`→1, 빈 `Next review`→오늘 due로 취급 → 첫 `review`가 지연 백필(별도 스크립트 X).
- **새 CLI 모드 `review`**(fetch 오염 방지): `due_rows()` 조회 → `reschedule(page_id, box, recall)`(새박스 계산, `Next review=today+간격`, `Last reviewed=today`, `Recall` 클리어) → `notify_review(due)` Discord 핑 `• **expr** — ||뜻||`(notify_discord 재사용, 1990자 클램프, 없으면 스킵).
- **신규 카드 init**: `_properties()`에 `Box=1`, `Next review=today+1` 세팅.
- **일일 흐름**: `review` → `fetch` → 생성 → `write`. `routine_prompt.md`에 Step0(`python daily_notion.py review` 먼저 실행) 추가. 생성 로직은 불변.
- docs: 신규 `docs/review.md`(스킴·간격·Recall·모드·핑) + `notion.md`(속성4)·`CLAUDE.md`(Layout+CLI)·`overview.md`(pipeline+로드맵)·`generation.md` 갱신.
- **검증**: `migrate` 1회 → `review` 실행 시 due 행에 Box/Next review 채워지고 스포일러 핑 도착; 한 행 `Recall=Got it` 후 재실행 → 박스↑·간격 점프·Recall 클리어.

## Increment 2 — 발음 오디오 (중국어 우선, 인라인 네이티브 + 폴백) ✅ 출시
- **결정 진화**: 처음엔 YouGlish 링크만(키·호스팅 0). 사용자 피드백("원어민 실제 발음 + 카드 안 임베드, 매번 클릭은 번거로움")으로 **인라인 네이티브 오디오**로 전환. 파일 업로드/edge-tts(보류) 대신 **CDN 호스팅 네이티브 녹음**이라는 제3의 길: `audio-cmn`(hugolpz, CC BY-SA) mp3를 jsDelivr로 직접 임베드 — 네트워크만 쓰고 키·호스팅·업로드 0, URL 영구.
- **3단 리졸버 `native_audio_url(expr, pinyin)`**:
  1. `zh_audio_url(word)`(lru_cache): `.../audio-cmn@master/64k/hsk/cmn-{quote(word)}.mp3` HEAD → 200이면 URL, 아니면(403/404/네트워크) None. 한자 **퍼센트 인코딩 필수**. 단일 HSK어 ~80%.
  2. `_commons_audio_url(word, pinyin)`(lru_cache): Wikimedia Commons 검색 API(`User-Agent` 필수)로 오디오 파일 찾고, **파일명 병음을 카드 병음과 대조(`_pinyin_matches`)해 일치할 때만** 채택 → 엉뚱한 발음 방지. 병음 없으면 스킵(안전). audio-cmn이 놓친 흔한 단어(예 `你好`) 일부를 ogg로 채움. Wikimedia 핫링크 비권장이라 폴백 한정.
- `_properties()`(ZH): `Audio` = `native_audio_url(...)` `or` YouGlish. `_page_body()`(ZH): 네이티브 있으면 **오디오 블록**(`{"type":"audio","audio":{"type":"external",...}}`, 인라인 재생) + 출처 링크(`_audio_credit`가 URL로 audio-cmn/Commons 구분, CC BY-SA 표기), 없으면 🔊 발음 듣기 YouGlish 링크 폴백. 성어·구·드문 단어는 네이티브 녹음 부재 → YouGlish行.
- 스키마 변경 없음(`Audio` url 재사용). 기존 행 백필 미실시(신규부터). EN 오디오는 후속(한 줄 게이트).
- docs: `notion.md`·`generation.md`·`overview.md` 갱신.
- **검증 완료**: 커버 단어(`学习`)는 `Audio` 속성=mp3 + 본문 audio 블록 인라인 재생; 미커버(`你好`)는 YouGlish 폴백. 오프라인 단위검증 + 라이브 카드 생성/되읽기 통과.

## Increment 3 — 능동 회상(cloze) + 역방향 카드 (스키마·행 추가 0, 렌더링만) ✅ 출시
- `cloze(example, expression)`: 표현을 `re.subn`(escape, `IGNORECASE`)로 `____` 치환, 못 찾으면 원문 유지(fail-soft). 부분문자열이라 인접 구두점은 자연 흡수.
- `_page_body()`: `_toggle()` 헬퍼 신설(2회 사용). 💬 콜아웃 = cloze 버전; `👀 뜻 보기` 토글 = 뜻 + (치환 성공 시) 전체 예문 + 번역; **두 번째 토글 `🔄 거꾸로 (뜻→표현): {뜻}`** = 라벨에 뜻 노출, 안에 표현 숨김. 행/스키마 추가 없음.
- `routine_prompt.md`: 예문에 표현을 **verbatim 포함** 요구로 강화(cloze 의존). 새 필드 없음.
- 기존 본문 재생성 안 함(신규부터). docs: `notion.md`·`generation.md` 갱신.
- **검증 완료**: 오프라인 단위(cloze EN/ZH/대소문자/fail-soft, 레이아웃) + 라이브 EN 카드(💬 `____`, 👀 토글에 뜻+전체예문+번역, 🔄 라벨=뜻·내부=표현) 통과.

## Increment 4 — 통계 (읽기 전용 집계, 1에 의존) ✅ 출시
- `compute_stats(notion)`: EN·ZH **vocab 행만**(연습 행 제외) 한 번 스캔 — 총 학습수, due 수(조건은 `due_rows`와 동일·교차검증), 박스 분포, HSK 레벨 분포(ZH), **streak**(카드 `Date`에서 오늘(없으면 어제)부터 역산). 모두 기존 데이터 파생 — **대시보드 DB·상태필드 없음**.
- 전달: `review` 핑 푸터에 3줄(`_stats_lines`: 누적+streak / 박스 / HSK) 합침 + 온디맨드 `stats` 모드(`stats()` → JSON 출력 + `notify_stats` Discord 요약, Notion 읽기 전용).
- docs: 신규 `docs/stats.md` + `CLAUDE.md`(Layout+CLI+Status)·`overview.md` 갱신.
- **검증 완료**: 오프라인 단위(`_streak`·`_stats_lines`) + 라이브(`compute_stats`가 박스합=총계, due=`due_rows` 일치, streak≥0) + `stats` 모드 JSON 출력·Discord 요약 발송 정상.

---

## 순서 & 의존성
**0 → 1 → 2 → 3 → 4.** 하드 의존성은 **4 → 1**(due/박스 지표)뿐. 2·3은 0 외 독립. 1이 유일한 스키마 변경.

## 핵심 파일
- `daily_notion.py` (전 increment), `sources.py`(inc0), `routine_prompt.md`(0·1·3), `requirements.txt`/`.env.example`(0)
- `docs/`: `sources.md`·`overview.md`·`deployment.md`(0), 신규 `review.md`(1)·`stats.md`(4), `notion.md`·`generation.md`(1·2·3), `CLAUDE.md`(1·4)

## 과잉설계 가드 (Plan 에이전트 감사 반영)
SM-2 ease 대신 Leitner 고정간격 · edge-tts/파일업로드 보류(링크로) · 역방향은 두번째 토글(행 추가 금지) · 통계는 읽기집계(대시보드DB 금지) · streak는 `Date`에서 계산(상태필드 금지) · 기존 24행 본문 재생성 안 함 · Discord 인터랙티브(버튼) 시도 안 함.
