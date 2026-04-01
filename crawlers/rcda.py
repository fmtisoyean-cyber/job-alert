"""
한국지역사회교육협의회 (rcda.or.kr) 크롤러
채용공고 게시판: /home/kor/board.do?menuCode=7

※ 게시판 링크가 javascript:void(0) 방식이라 idx를 직접 추출할 수 없음.
  대신 페이지 텍스트에서 공고 제목만 추출하고 게시판 URL로 연결.
"""
import hashlib
import logging
import re
from bs4 import BeautifulSoup
from .base import BaseCrawler

logger = logging.getLogger(__name__)

BASE_URL    = "https://www.rcda.or.kr"
BOARD_URL   = f"{BASE_URL}/home/kor/board.do?menuCode=7"
LIST_PARAMS = {"menuCode": "7"}


class RcdaCrawler(BaseCrawler):
    name    = "한국지역사회교육협의회"
    curated = True

    def fetch(self) -> list[dict]:
        try:
            resp = self.get(f"{BASE_URL}/home/kor/board.do", params=LIST_PARAMS)
            if not resp:
                return []
            return self._parse(resp.text)
        except Exception as e:
            logger.error(f"[{self.name}] 오류: {e}")
            return []

    def _parse(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        results = []
        seen_titles = set()

        # 전략1: 테이블 행에서 제목 셀 탐색
        for row in soup.select("table tbody tr"):
            title_td = (
                row.select_one("td.title")
                or row.select_one("td.subject")
                or row.select_one("td:nth-child(2)")
            )
            if not title_td:
                continue
            title = title_td.get_text(strip=True)
            if not self._valid_title(title, seen_titles):
                continue
            seen_titles.add(title)

            # 날짜 셀
            deadline = self._extract_date(row)
            job_id   = hashlib.md5(title.encode()).hexdigest()[:12]
            results.append(self._make_job(job_id, title, deadline))

        # 전략2: 텍스트에서 "채용" 포함 문장 추출 (JS 렌더링 사이트 보완)
        if not results:
            for tag in soup.find_all(string=re.compile(r"채용|모집|공고")):
                text = tag.strip()
                if len(text) < 6 or len(text) > 100:
                    continue
                if not self._valid_title(text, seen_titles):
                    continue
                seen_titles.add(text)
                job_id = hashlib.md5(text.encode()).hexdigest()[:12]
                results.append(self._make_job(job_id, text, ""))

        logger.info(f"[{self.name}] 수집: {len(results)}개")
        return results

    def _make_job(self, job_id, title, deadline):
        return {
            "id":       job_id,
            "title":    title,
            "company":  "한국지역사회교육협의회",
            "deadline": deadline,
            "url":      BOARD_URL,
            "source":   self.name,
        }

    def _valid_title(self, title: str, seen: set) -> bool:
        if not title or title in seen:
            return False
        if title.isdigit() or len(title) < 5:
            return False
        skip = {"접수마감", "접수중", "접수예정", "번호", "제목", "등록일", "조회수"}
        if title in skip:
            return False
        return True

    def _extract_date(self, row) -> str:
        for cell in reversed(row.select("td")):
            text = cell.get_text(strip=True)
            if re.search(r"\d{4}[.\-]\d{1,2}", text):
                return text
        return ""
