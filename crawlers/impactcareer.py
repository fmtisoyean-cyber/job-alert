"""
임팩트커리어 (impact.career) 크롤러
사회적가치 추구 조직 채용 전문 플랫폼 (Rails 서버 렌더링)
공고 URL 패턴: /impactcareer/grantors/careers/{slug}
"""
import hashlib
import logging
import re
from bs4 import BeautifulSoup
from .base import BaseCrawler

logger = logging.getLogger(__name__)

BASE_URL  = "https://impact.career"
LIST_URL  = f"{BASE_URL}/impactcareer/grantors/careers"
SLUG_RE   = re.compile(r"/impactcareer/grantors/careers/([A-Za-z0-9_-]+)")


class ImpactCareerCrawler(BaseCrawler):
    name = "임팩트커리어"

    def fetch(self) -> list[dict]:
        jobs = {}
        for url in [BASE_URL, LIST_URL]:
            try:
                items = self._parse_page(url)
                for item in items:
                    jobs[item["id"]] = item
            except Exception as e:
                logger.error(f"[{self.name}] {url} 오류: {e}")
        return list(jobs.values())

    def _parse_page(self, url: str) -> list[dict]:
        resp = self.get(url)
        if not resp:
            return []
        soup = BeautifulSoup(resp.text, "lxml")
        results = []

        # 방법1: 공고 링크 href 패턴으로 카드 탐색
        career_links = soup.find_all("a", href=SLUG_RE)
        for link in career_links:
            try:
                job = self._parse_card_from_link(link)
                if job:
                    results.append(job)
            except Exception as e:
                logger.debug(f"[{self.name}] 파싱 오류: {e}")

        # 방법2: 카드 컨테이너 직접 탐색 (링크가 없는 경우 보완)
        if not results:
            cards = (
                soup.select("div[class*='card'] a[href*='careers']")
                or soup.select("article a[href*='careers']")
                or soup.select(".job-card")
            )
            for card in cards:
                try:
                    job = self._parse_card_from_link(card)
                    if job:
                        results.append(job)
                except Exception as e:
                    logger.debug(f"[{self.name}] 카드 파싱 오류: {e}")

        return results

    def _parse_card_from_link(self, link_tag) -> dict | None:
        href = link_tag.get("href", "")
        m = SLUG_RE.search(href)
        if not m:
            return None

        slug = m.group(1)
        full_url = f"{BASE_URL}{href}" if href.startswith("/") else href

        # 링크 태그 및 상위 컨테이너에서 텍스트 추출
        container = link_tag.parent or link_tag

        # 제목 추출 — 가장 굵은 텍스트 또는 heading 태그
        title_tag = (
            container.select_one("h1, h2, h3, h4")
            or container.select_one("[class*='title']")
            or container.select_one("[class*='tit']")
            or container.select_one("strong")
        )
        title = title_tag.get_text(strip=True) if title_tag else link_tag.get_text(strip=True)
        title = title.strip()
        if not title or len(title) < 2:
            return None

        # 기관명 — 제목 다음에 오는 텍스트 또는 별도 클래스
        company_tag = (
            container.select_one("[class*='company']")
            or container.select_one("[class*='org']")
            or container.select_one("[class*='corp']")
        )
        company = company_tag.get_text(strip=True) if company_tag else ""

        # 마감일 — 날짜 패턴 탐색
        deadline = ""
        date_tag = (
            container.select_one("[class*='deadline']")
            or container.select_one("[class*='date']")
            or container.select_one("[class*='period']")
        )
        if date_tag:
            deadline = date_tag.get_text(strip=True)
        else:
            # 텍스트에서 날짜 패턴 추출
            text = container.get_text(" ", strip=True)
            date_match = re.search(r"\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}", text)
            if date_match:
                deadline = date_match.group()

        job_id = hashlib.md5(full_url.encode()).hexdigest()[:16]
        return {
            "id":       job_id,
            "title":    title,
            "company":  company,
            "deadline": deadline,
            "url":      full_url,
            "source":   self.name,
        }
