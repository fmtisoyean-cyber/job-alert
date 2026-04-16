"""
사람인 (saramin.co.kr) 크롤러
키워드 검색 결과 수집
"""
import hashlib
import logging
from bs4 import BeautifulSoup
from config import SEARCH_KEYWORDS
from .base import BaseCrawler

logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.saramin.co.kr/zf_user/search/recruit"


class SaraminCrawler(BaseCrawler):
    name = "사람인"

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
            "searchType": "search",
            "searchword": keyword,
            "recruitPage": "1",
            "recruitPageCount": "40",
            "recruitSort": "reg_dt",  # 최신순
        }
        resp = self.get(SEARCH_URL, params=params)
        if not resp:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        results = []

        # 사람인 공고 카드 파싱
        # 구조: div.item_recruit 안에 각 공고
        cards = soup.select("div.item_recruit") or soup.select(".list_body .list_item")

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
            card.select_one("h2.job_tit a")
            or card.select_one(".job_tit a")
            or card.select_one("a.str_tit")
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
            href = "https://www.saramin.co.kr" + href

        # 기관명
        company_tag = (
            card.select_one("strong.corp_name a")
            or card.select_one(".corp_name a")
            or card.select_one(".company_nm")
        )
        company = company_tag.get_text(strip=True) if company_tag else ""

        # 마감일
        deadline_tag = (
            card.select_one("span.date")
            or card.select_one(".job_date .date")
            or card.select_one(".deadlines")
        )
        deadline = deadline_tag.get_text(strip=True) if deadline_tag else "미정"
        # "D-7" 같은 형태가 올 수 있으니 그대로 사용

        # 근무지역
        location_tag = (
            card.select_one(".work_place")
            or card.select_one(".job_condition .work_place")
            or card.select_one("[class*='work_place']")
        )
        location = location_tag.get_text(strip=True) if location_tag else ""

        job_id = hashlib.md5(href.encode()).hexdigest()[:16]

        return {
            "id": job_id,
            "title": title,
            "company": company,
            "deadline": deadline,
            "location": location,
            "url": href,
            "source": self.name,
        }
