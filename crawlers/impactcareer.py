"""
임팩트커리어 (impact.career) 크롤러
Rails 서버 렌더링 — 공고 링크 패턴: /impactcareer/grantors/careers/{slug}
링크 텍스트가 "[기관명] 공고제목" 형태.
"""
import hashlib
import logging
import re
import requests
from bs4 import BeautifulSoup
from .base import BaseCrawler

logger = logging.getLogger(__name__)

BASE_URL = "https://impact.career"
LIST_URL = f"{BASE_URL}/impactcareer/grantors/careers"
SLUG_RE  = re.compile(r"/impactcareer/grantors/careers/([A-Za-z0-9_-]+)")
ORG_RE   = re.compile(r"^\[(.+?)\]\s*(.+)$")   # "[기관명] 공고제목" 파싱


class ImpactCareerCrawler(BaseCrawler):
    name    = "임팩트커리어"
    curated = True

    def fetch(self) -> list[dict]:
        results = {}
        for url in [LIST_URL, BASE_URL]:
            try:
                items = self._parse_page(url)
                for item in items:
                    results[item["id"]] = item
                if results:
                    break   # 성공하면 중단
            except Exception as e:
                logger.error(f"[{self.name}] {url} 오류: {e}")
        logger.info(f"[{self.name}] 수집: {len(results)}개")
        return list(results.values())

    def _parse_page(self, url: str) -> list[dict]:
        # Session + 브라우저 헤더로 요청
        session = requests.Session()
        session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
            "Referer": BASE_URL,
        })
        try:
            resp = session.get(url, timeout=20)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"[{self.name}] 요청 실패 ({url}): {e}")
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        results = {}

        # 모든 <a> 태그를 순회하며 slug 패턴 탐색
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            m = SLUG_RE.search(href)
            if not m:
                continue
            slug = m.group(1)
            if slug in results:
                continue

            full_url = BASE_URL + href if href.startswith("/") else href

            # 링크 텍스트 → 없으면 상위 컨테이너 텍스트
            title_text = a.get_text(" ", strip=True)
            if not title_text:
                parent = a.find_parent(["li", "div", "article"])
                title_text = parent.get_text(" ", strip=True) if parent else ""
            title_text = re.sub(r"\s+", " ", title_text).strip()
            if not title_text or len(title_text) < 3:
                continue

            # "[기관명] 제목" 분리
            org_m = ORG_RE.match(title_text)
            company = org_m.group(1).strip() if org_m else ""
            title   = org_m.group(2).strip() if org_m else title_text

            # 제목 안 마감일 힌트 추출 (예: ~4/15)
            deadline = ""
            dm = re.search(r"~(\d{1,2}/\d{1,2}|\d{4}[.\-]\d{2}[.\-]\d{2})", title)
            if dm:
                deadline = dm.group(1)
                title = title.replace(dm.group(0), "").strip()

            results[slug] = {
                "id":       hashlib.md5(full_url.encode()).hexdigest()[:16],
                "title":    title,
                "company":  company,
                "deadline": deadline,
                "url":      full_url,
                "source":   self.name,
            }

        return list(results.values())
