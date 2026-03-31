"""
한국지역사회교육협의회 (rcda.or.kr) 크롤러
채용공고 게시판: /home/kor/board.do?menuCode=7
공고 상세 URL:  /home/kor/board.do?menuCode=7&idx={idx}&act=detail
"""
import hashlib
import logging
import re
from bs4 import BeautifulSoup
from .base import BaseCrawler

logger = logging.getLogger(__name__)

BASE_URL  = "https://www.rcda.or.kr"
LIST_URL  = f"{BASE_URL}/home/kor/board.do"
LIST_PARAMS = {"menuCode": "7"}


class RcdaCrawler(BaseCrawler):
    name = "한국지역사회교육협의회"

    def fetch(self) -> list[dict]:
        try:
            return self._parse_list()
        except Exception as e:
            logger.error(f"[{self.name}] 오류: {e}")
            return []

    def _parse_list(self) -> list[dict]:
        resp = self.get(LIST_URL, params=LIST_PARAMS)
        if not resp:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        results = []

        # 게시판 행 탐색 — tr 또는 li 기반 구조 모두 시도
        rows = (
            soup.select("table.board_list tbody tr")
            or soup.select("table tbody tr")
            or soup.select("ul.board_list li")
            or soup.select(".board_list li")
            or soup.select(".list-wrap li")
        )

        for row in rows:
            try:
                job = self._parse_row(row)
                if job:
                    results.append(job)
            except Exception as e:
                logger.debug(f"[{self.name}] 행 파싱 오류: {e}")

        # 행이 없으면 href 패턴으로 직접 탐색
        if not results:
            results = self._fallback_link_parse(soup)

        return results

    def _parse_row(self, row) -> dict | None:
        # 제목/링크 셀 탐색
        title_tag = (
            row.select_one("td.title a")
            or row.select_one("td a")
            or row.select_one(".title a")
            or row.select_one("a")
        )
        if not title_tag:
            return None

        title = title_tag.get_text(strip=True)
        if not title or title.isdigit():
            return None

        href = title_tag.get("href", "")
        full_url = self._resolve_url(href)

        # idx 파라미터 추출
        idx_match = re.search(r"idx=(\d+)", full_url)
        job_id = idx_match.group(1) if idx_match else hashlib.md5(full_url.encode()).hexdigest()[:10]

        # 날짜 셀 — 마지막에서 두 번째 td 또는 date 클래스
        cells = row.select("td")
        deadline = ""
        date_tag = row.select_one("td.date") or row.select_one(".date")
        if date_tag:
            deadline = date_tag.get_text(strip=True)
        else:
            for cell in reversed(cells):
                text = cell.get_text(strip=True)
                if re.search(r"\d{4}[.\-]\d{1,2}", text):
                    deadline = text
                    break

        # 기관명(공공기관이므로 사이트명 사용)
        company = "한국지역사회교육협의회"

        return {
            "id":       job_id,
            "title":    title,
            "company":  company,
            "deadline": deadline,
            "url":      full_url,
            "source":   self.name,
        }

    def _fallback_link_parse(self, soup) -> list[dict]:
        """board.do?menuCode=7&idx=... 패턴 링크 직접 탐색"""
        results = []
        pattern = re.compile(r"board\.do\?menuCode=7.*idx=(\d+)")
        seen = set()

        for a in soup.find_all("a", href=pattern):
            idx_m = pattern.search(a.get("href", ""))
            if not idx_m:
                continue
            idx = idx_m.group(1)
            if idx in seen:
                continue
            seen.add(idx)

            title = a.get_text(strip=True)
            if not title:
                continue

            href   = a.get("href", "")
            detail = f"{BASE_URL}/home/kor/board.do?menuCode=7&idx={idx}&act=detail"

            # 근처 텍스트에서 날짜 추출
            parent_text = (a.parent or a).get_text(" ", strip=True)
            date_m = re.search(r"\d{4}[.\-]\d{1,2}[.\-]\d{1,2}", parent_text)
            deadline = date_m.group() if date_m else ""

            results.append({
                "id":       idx,
                "title":    title,
                "company":  "한국지역사회교육협의회",
                "deadline": deadline,
                "url":      detail,
                "source":   self.name,
            })

        return results

    def _resolve_url(self, href: str) -> str:
        if href.startswith("http"):
            return href
        if href.startswith("/"):
            return BASE_URL + href
        return BASE_URL + "/home/kor/" + href.lstrip("./")
