"""
seen_jobs.json 기반 상태 관리 (SQLite db.py 대체)
GitHub Actions 환경에서 repo에 커밋하여 중복 알림을 방지합니다.
"""
import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

STATE_FILE = os.getenv("STATE_FILE", "seen_jobs.json")


class StateManager:
    def __init__(self, path: str = STATE_FILE):
        self.path = path
        self.data = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"seen_jobs.json 로드 실패, 새로 시작합니다: {e}")
        return {"jobs": {}}

    def is_seen(self, job_id: str) -> bool:
        return job_id in self.data.get("jobs", {})

    def mark_seen(self, job_id: str, job: dict):
        self.data.setdefault("jobs", {})[job_id] = {
            "title":    job.get("title", ""),
            "company":  job.get("company", ""),
            "source":   job.get("source", ""),
            "sent_at":  datetime.now().isoformat(),
        }

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            logger.info(f"상태 저장 완료 ({self.count()}개 누적)")
        except IOError as e:
            logger.error(f"상태 저장 실패: {e}")

    def count(self) -> int:
        return len(self.data.get("jobs", {}))
