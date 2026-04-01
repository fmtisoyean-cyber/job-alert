"""
채용공고 자동 알림 시스템 — GitHub Actions 버전
seen_jobs.json으로 중복 관리, 텔레그램으로 알림 전송

실행 방법:
    python main.py                  # 직접 실행
    GitHub Actions cron으로 자동 실행 (.github/workflows/job-alert.yml)
"""
import logging
import sys

from config import INCLUDE_KEYWORDS, EXCLUDE_KEYWORDS
from state import StateManager
from notifier import TelegramNotifier
from crawlers.gojobs import GojobsCrawler
from crawlers.saramin import SaraminCrawler
from crawlers.jobkorea import JobkoreaCrawler
from crawlers.impactcareer import ImpactCareerCrawler
from crawlers.rcda import RcdaCrawler
from crawlers.civilnet import CivilnetCrawler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("job_alert.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def matches_filter(job: dict, curated: bool = False) -> bool:
    """
    curated=True  (임팩트커리어·RCDA·시민사회연대 등 특화 사이트)
      → 제외 키워드만 체크 (포함 키워드 불필요)
    curated=False (사람인·잡코리아·나라일터 등 일반 사이트)
      → 포함 키워드 하나 이상 & 제외 키워드 없음
    """
    text = f"{job.get('title', '')} {job.get('company', '')}".lower()
    has_exclude = any(kw in text for kw in EXCLUDE_KEYWORDS)
    if has_exclude:
        return False
    if curated:
        return True
    return any(kw in text for kw in INCLUDE_KEYWORDS)


def run():
    logger.info("=" * 55)
    logger.info("채용공고 수집 시작")
    logger.info("=" * 55)

    state    = StateManager()
    notifier = TelegramNotifier()

    crawlers = [
        # 범용 채용 사이트 (키워드 검색)
        GojobsCrawler(),
        SaraminCrawler(),
        JobkoreaCrawler(),
        # 전문 / 기관 사이트
        ImpactCareerCrawler(),
        RcdaCrawler(),
        CivilnetCrawler(),
    ]

    total_new = 0

    for crawler in crawlers:
        try:
            logger.info(f"[{crawler.name}] 크롤링 시작...")
            jobs = crawler.fetch()
            logger.info(f"[{crawler.name}] {len(jobs)}개 수집")

            passed = [j for j in jobs if matches_filter(j, crawler.curated)]
            logger.info(f"[{crawler.name}] 필터 통과: {len(passed)}개 (curated={crawler.curated})")

            for job in passed:
                job_id = f"{crawler.name}_{job['id']}"

                if state.is_seen(job_id):
                    logger.debug(f"  - 중복 건너뜀: {job['title']}")
                    continue

                success = notifier.send(job)
                if success:
                    state.mark_seen(job_id, job)
                    total_new += 1
                    logger.info(f"  ✓ 알림 전송: [{job['company']}] {job['title']}")

        except Exception as e:
            logger.error(f"[{crawler.name}] 오류: {e}", exc_info=True)

    # 상태 파일 저장 (GitHub Actions가 이후 커밋)
    state.save()

    logger.info("-" * 55)
    logger.info(f"완료 — 신규 공고 {total_new}개 알림 전송 / 누적 {state.count()}개")

    if total_new > 0:
        notifier.send_summary(total_new)


if __name__ == "__main__":
    run()
