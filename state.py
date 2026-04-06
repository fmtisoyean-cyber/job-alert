"""
seen_jobs.json 기반 상태 관리
GitHub Actions 환경에서는 GitHub API로 최신 파일을 직접 읽어
체크아웃 타이밍 차이로 인한 중복 알림을 방지합니다.
"""
import base64
import json
import logging
import os
import urllib.request
from datetime import datetime

logger = logging.getLogger(__name__)

STATE_FILE = os.getenv("STATE_FILE", "seen_jobs.json")


class StateManager:
    def __init__(self, path: str = STATE_FILE):
        self.path = path
        self.data = self._load()

    def _load(self) -> dict:
        # GitHub Actions 환경: GITHUB_TOKEN + GITHUB_REPOSITORY 자동 제공
        # → API로 최신 seen_jobs.json을 직접 읽어 체크아웃 시점 차이로 인한 중복 방지
        token = os.getenv("GITHUB_TOKEN")
        repo  = os.getenv("GITHUB_REPOSITORY")
        if token and repo:
            try:
                req = urllib.request.Request(
                    f"https://api.github.com/repos/{repo}/contents/{self.path}",
                    headers={
                        "Authorization": f"token {token}",
                        "Accept": "application/vnd.github+json",
                    },
                )
                with urllib.request.urlopen(req, timeout=10) as r:
                    raw = base64.b64decode(json.loads(r.read())["content"]).decode("utf-8")
                    data = json.loads(raw)
                    logger.info(f"GitHub API에서 seen_jobs.json 로드 ({len(data.get('jobs', {}))}개)")
                    return data
            except Exception as e:
                logger.warning(f"API 로드 실패, 로컬 파일 사용: {e}")

        # 로컬 실행 fallback
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"seen_jobs.json 로드 실패: {e}")
        return {"jobs": {}}

    def is_seen(self, job_id: str) -> bool:
        return job_id in self.data.get("jobs", {})

    def mark_seen(self, job_id: str, job: dict):
        self.data.setdefault("jobs", {})[job_id] = {
            "title":   job.get("title", ""),
            "company": job.get("company", ""),
            "source":  job.get("source", ""),
            "sent_at": datetime.now().isoformat(),
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
