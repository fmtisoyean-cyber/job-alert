# 채용공고 자동 알림 시스템 (GitHub Actions 버전)

사회적가치 추구 조직, 공공기관, 중간지원조직, 위원회 사무국 등의
신규 채용공고를 **하루 2회** 자동 수집하여 텔레그램으로 알림을 보냅니다.
GitHub Actions + `seen_jobs.json` 방식으로 서버 없이 동작합니다.

---

## 수집 사이트

| 사이트 | 설명 |
|--------|------|
| 나라일터 (gojobs.go.kr) | 공공기관 채용 공식 포털 |
| 사람인 (saramin.co.kr) | 키워드 검색 |
| 잡코리아 (jobkorea.co.kr) | 키워드 검색 |
| 임팩트커리어 (impact.career) | 사회적가치 조직 채용 전문 |
| 한국지역사회교육협의회 (rcda.or.kr) | 기관 채용공고 게시판 |
| 시민사회단체연대회의 (civilnet.net) | 구인구직 게시판 |

## 필터링 키워드

- **포함**: 위원회, 사무국, 중간지원, 사회적가치, 공익, 재단, 연구원, 정책, 보좌, 지원단, 임팩트
- **제외**: 단순노무, 청소, 경비

---

## 빠른 시작

### 1단계: 텔레그램 봇 만들기

**봇 생성**
1. 텔레그램 → `@BotFather` 검색 → 채팅 시작
2. `/newbot` 입력 → 봇 이름과 사용자명 설정
3. 발급된 **API Token** 복사 (예: `1234567890:ABCdef...`)

**채팅 ID 확인**
1. 생성한 봇에서 `/start` 전송
2. 브라우저에서 접속 (`YOUR_TOKEN`을 실제 토큰으로 교체):
   ```
   https://api.telegram.org/botYOUR_TOKEN/getUpdates
   ```
3. 응답 JSON의 `"chat":{"id": 150470795}` 숫자가 **CHAT_ID**

> 그룹 알림을 원하면: 그룹에 봇을 초대하고 위 URL을 다시 조회하면 그룹 CHAT_ID(음수값)를 확인할 수 있습니다.

---

### 2단계: GitHub Repository 생성

```bash
# 이 프로젝트 폴더를 GitHub에 업로드
git init
git add .
git commit -m "feat: 채용공고 알림 시스템 초기 설정"
git remote add origin https://github.com/YOUR_USERNAME/job-alert.git
git push -u origin main
```

---

### 3단계: GitHub Secrets 등록

GitHub 저장소 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret 이름 | 값 | 설명 |
|-------------|-----|------|
| `BOT_TOKEN` | `1234567890:ABCdef...` | BotFather에서 발급한 토큰 |
| `CHAT_ID`   | `150470795` | 알림 받을 채팅 ID |

---

### 4단계: 자동 실행 확인

- GitHub 저장소 → **Actions** 탭에서 워크플로우 활성화
- **수동 실행**: Actions → `채용공고 자동 알림` → `Run workflow`
- **자동 실행**: 매일 오전 9시, 오후 6시 (KST) 자동 실행

---

## 동작 원리

```
GitHub Actions 스케줄 트리거 (09:00 / 18:00 KST)
       │
       ▼
main.py 실행
       │
       ├─ seen_jobs.json 로드 (이미 알림 전송한 공고 목록)
       │
       ├─ 6개 사이트 크롤링
       │       ├─ 나라일터 / 사람인 / 잡코리아 (키워드 검색)
       │       └─ 임팩트커리어 / RCDA / 시민사회연대 (기관 게시판)
       │
       ├─ 키워드 필터링 (포함/제외)
       │
       ├─ 신규 공고만 텔레그램 전송
       │
       └─ seen_jobs.json 업데이트
              │
              ▼
       git commit → repo에 자동 push
       (다음 실행 시 중복 방지에 활용)
```

---

## 파일 구조

```
job-alert/
├── .github/
│   └── workflows/
│       └── job-alert.yml     # GitHub Actions 스케줄 워크플로우
│
├── crawlers/
│   ├── base.py               # 공통 크롤러 베이스
│   ├── gojobs.py             # 나라일터
│   ├── saramin.py            # 사람인
│   ├── jobkorea.py           # 잡코리아
│   ├── impactcareer.py       # 임팩트커리어 (신규)
│   ├── rcda.py               # 한국지역사회교육협의회 (신규)
│   └── civilnet.py           # 시민사회단체연대회의 (신규)
│
├── main.py                   # 메인 실행 스크립트
├── state.py                  # seen_jobs.json 상태 관리
├── config.py                 # 키워드 및 설정
├── notifier.py               # 텔레그램 알림 전송
├── seen_jobs.json            # 전송 이력 (자동 커밋 관리)
├── .env.example              # 환경변수 예시
├── requirements.txt
└── README.md
```

---

## 알림 메시지 예시

```
📢 새 채용공고 알림

🏢 기관명: 한국사회혁신진흥원
📋 공고명: 사회적가치 정책연구원 채용
📅 마감일: 2026.04.15
🔗 출처: 임팩트커리어
공고 바로가기
```

---

## 키워드 커스터마이징

`config.py`에서 수정:

```python
# 사이트 검색 키워드
SEARCH_KEYWORDS = ["사회적가치", "중간지원", ...]

# 공고 제목/기관명 포함 필터
INCLUDE_KEYWORDS = ["위원회", "사무국", ...]

# 제외 필터
EXCLUDE_KEYWORDS = ["단순노무", "청소", ...]
```

---

## 로컬 테스트

```bash
# 패키지 설치
pip install -r requirements.txt

# .env 파일 생성
cp .env.example .env
# BOT_TOKEN, CHAT_ID 수정

# 직접 실행
python main.py
```

---

## seen_jobs.json 구조

```json
{
  "jobs": {
    "임팩트커리어_a1b2c3d4e5f6": {
      "title": "사회적가치 정책연구원 채용",
      "company": "한국사회혁신진흥원",
      "source": "임팩트커리어",
      "sent_at": "2026-03-31T09:00:00.123456"
    }
  }
}
```

- 키: `{사이트명}_{공고ID의 MD5 해시}`
- 누적 관리되며 GitHub에 자동 커밋

---

## 주의사항

- 크롤링 대상 사이트의 HTML 구조가 변경되면 `crawlers/*.py`의 CSS 선택자를 업데이트해야 합니다.
- 임팩트커리어·시민사회연대회의는 JS 렌더링 여부에 따라 크롤링이 제한될 수 있습니다.
- GitHub Actions의 UTC 기준 스케줄 → KST 변환: `0 0 * * *` = 오전 9시, `0 9 * * *` = 오후 6시
- 워크플로우의 `[skip ci]` 커밋 메시지는 무한 루프를 방지합니다.
