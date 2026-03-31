"""
나라일터 (gojobs.go.kr) 크롤러
공공기관 채용 공식 포털 — 키워드별 검색 결과 수집
"""
import hashlib
import logging
from bs4 import BeautifulSoup
from config import SEARCH_KEYWORDS
from .base import BaseCrawler

logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.gojobs.go.kr/recruit/recruitList.do"


class GojobsCrawler(BaseCrawler):
    name = "나라일터"

    def fetch(self) -> list[dict]:
        jobs = {}
        for keyword in SEARCH_KEYWORDS:
            try:
                items = self._search(keyword)
                for item in items:
                    jobs[item["id"]] = item  # 중복 제거
            except Exception as e:
                logger.error(f"[{self.name}] 키워드 '{keyword}' 오류: {e}")
        return list(jobs.values())

    def _search(self, keyword: str) -> list[dict]:
        params = {
            "pageIndex": "1",
            "recruitGbCd": "",
            "workRgnCd": "",
            "empTypeCd": "",
            "schWord": keyword,
        }
        resp = self.get(SEARCH_URL, params=params)
        if not resp:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        results = []

        # 나라일터 공고 목록 테이블 파싱
        # 실제 HTML 구조에 따라 선택자를 조정하세요
        rows = soup.select("table.tbl_list tbody tr")
        if not rows:
            # 대체 선택자 시도
            rows = soup.select(".list_wrap .item") or soup.select("ul.list li")

        for row in rows:
            try:
                job = self._parse_row(row)
                if job:
                    results.append(job)
            except Exception as e:
                logger.debug(f"[{self.name}] 행 파싱 오류: {e}")

        return results

    def _parse_row(self, row) -> dict | None:
        # 제목/링크
        title_tag = (
            row.select_one("td.title a")
            or row.select_one("a.title")
            or row.select_one(".tit a")
            or row.select_one("a")
        )
        if not title_tag:
            return None

        title = title_tag.get_text(strip=True)
        if not title:
            return None

        href = title_tag.get("href", "")
        if href.startswith("/"):
            href = "https://www.gojobs.go.kr" + href
        elif not href.startswith("http"):
            href = "https://www.gojobs.go.kr/" + href.lstrip("./")

        # 기관명
        cells = row.select("td")
        company = cells[1].get_text(strip=True) if len(cells) > 1 else ""

        # 마감일 — 보통 마지막에서 두 번째 셀
        deadline = ""
        for cell in reversed(cells):
            text = cell.get_text(strip=True)
            if "." in text and len(text) <= 12:
                deadline = text
                break

        job_id = hashlib.md5(href.encode()).hexdigest()[:16]

        return {
            "id": job_id,
            "title": title,
            "company": company,
            "deadline": deadline,
            "url": href,
            "source": self.name,
        }
