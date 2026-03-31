"""
잡코리아 (jobkorea.co.kr) 크롤러
키워드 검색 결과 수집
"""
import hashlib
import logging
from bs4 import BeautifulSoup
from config import SEARCH_KEYWORDS
from .base import BaseCrawler

logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.jobkorea.co.kr/Search/"


class JobkoreaCrawler(BaseCrawler):
    name = "잡코리아"

    def fetch(self) -> list[dict]:
        jobs = {}
        for keyword in SEARCH_KEYWORDS:
            try:
                items = self._search(keyword)
                for item in items:
                    jobs[item["id"]] = item
            except Exception as e:
                logger.error(f"[{self.name}] 키워드 '{keyword}' 오류: {e}")
        return list(jobs.values())

    def _search(self, keyword: str) -> list[dict]:
        params = {
            "stext": keyword,
            "tabType": "recruit",
            "Page_No": "1",
        }
        resp = self.get(SEARCH_URL, params=params)
        if not resp:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        results = []

        # 잡코리아 공고 리스트 파싱
        # 구조: #recruit-list-ajax-result 또는 .list-default li
        cards = (
            soup.select("#recruit-list-ajax-result .list-post")
            or soup.select(".recruit-info-list li")
            or soup.select("article.list_item")
        )

        for card in cards:
            try:
                job = self._parse_card(card)
                if job:
                    results.append(job)
            except Exception as e:
                logger.debug(f"[{self.name}] 카드 파싱 오류: {e}")

        return results

    def _parse_card(self, card) -> dict | None:
        # 공고 제목
        title_tag = (
            card.select_one(".title a")
            or card.select_one("h2 a")
            or card.select_one(".recruit-title a")
        )
        if not title_tag:
            return None

        title = title_tag.get_text(strip=True)
        if not title:
            return None

        href = title_tag.get("href", "")
        if href.startswith("//"):
            href = "https:" + href
        elif href.startswith("/"):
            href = "https://www.jobkorea.co.kr" + href

        # 기관명
        company_tag = (
            card.select_one(".name")
            or card.select_one(".company-name")
            or card.select_one(".corp-name")
        )
        company = company_tag.get_text(strip=True) if company_tag else ""

        # 마감일
        deadline_tag = (
            card.select_one(".date")
            or card.select_one(".deadlines")
            or card.select_one(".info-period")
        )
        deadline = deadline_tag.get_text(strip=True) if deadline_tag else "미정"

        job_id = hashlib.md5(href.encode()).hexdigest()[:16]

        return {
            "id": job_id,
            "title": title,
            "company": company,
            "deadline": deadline,
            "url": href,
            "source": self.name,
        }
