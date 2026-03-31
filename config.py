import os
from dotenv import load_dotenv

load_dotenv()

# 텔레그램 설정 (.env 또는 GitHub Secrets)
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID   = os.getenv("CHAT_ID", "150470795")   # 기본값 설정

# 상태 파일 경로 (GitHub Actions에서는 repo 루트에 위치)
STATE_FILE = os.getenv("STATE_FILE", "seen_jobs.json")

# 사이트 검색에 사용할 키워드
SEARCH_KEYWORDS = [
    "사회적가치", "중간지원", "위원회", "사무국", "공익재단",
    "사회혁신", "지원단", "연구원 정책",
]

# 공고 제목/기관명에 이 단어 중 하나라도 포함되면 알림 전송
INCLUDE_KEYWORDS = [
    "위원회", "사무국", "중간지원", "사회적가치", "공익",
    "재단", "연구원", "정책", "보좌", "지원단", "사회혁신",
    "협동조합", "사회적경제", "비영리", "공공기관", "임팩트",
]

# 공고 제목에 포함되면 알림 제외
EXCLUDE_KEYWORDS = [
    "단순노무", "청소", "경비", "주차", "환경미화",
]

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
