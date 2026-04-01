"""
임팩트커리어 (impact.career) 크롤러
Rails 서버 렌더링 + Cloudflare — Playwright로 안정적으로 수집.
공고 링크 패턴: /impactcareer/grantors/careers/{slug}
링크 텍스트 형태: "[기관명] 공고제목"
"""
import hashlib
import logging
import re
from bs4 import BeautifulSoup
from playwright_helper import fetch_html
from .base import BaseCrawler

logger = logging.getLogger(__name__)

BASE_URL = "https://impact.career"
LIST_URL = f"{BASE_URL}/impactcareer/grantors/careers"
SLUG_RE  = re.compile(r"/impactcareer/grantors/careers/([A-Za-z0-9_-]+)")
ORG_RE   = re.compile(r"^\[(.+?)\]\s*(.+)$")  # "[기관명] 제목" 파싱


class ImpactCareerCrawler(BaseCrawler):
    name    = "임팩트커리어"
    curated = True

    def fetch(self) -> list[dict]:
        results = {}
        for url in [LIST_URL, BASE_URL]:
            try:
                html = fetch_html(url)          # Playwright 렌더링
                if not html:
                    resp = self.get(url)         # fallback: requests
                    html = resp.text if resp else ""
                if html:
                    for item in self._parse(html):
                        results[item["id"]] = item
                if results:
                    break
            except Exception as e:
                logger.error(f"[{self.name}] {url} 오류: {e}")

        logger.info(f"[{self.name}] 수집: {len(results)}개")
        return list(results.values())

    def _parse(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        results = {}

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
            org_m   = ORG_RE.match(title_text)
            company = org_m.group(1).strip() if org_m else ""
            title   = org_m.group(2).strip() if org_m else title_text

            # 제목 안 마감일 힌트 (예: ~4/15)
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
