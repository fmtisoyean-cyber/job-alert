"""
시민사회단체연대회의 (civilnet.net) 크롤러
구인구직 게시판: /recruits
공고 상세 URL:  /recruits/{id}

CSS 힌트 (페이지 소스 확인):
  .li_board ul li        — 공고 리스트 항목
  .list_text_title       — 공고 제목
  .pagination            — 페이지 네비게이션
"""
import hashlib
import logging
import re
from bs4 import BeautifulSoup
from .base import BaseCrawler

logger = logging.getLogger(__name__)

BASE_URL = "https://civilnet.net"
LIST_URL = f"{BASE_URL}/recruits"


class CivilnetCrawler(BaseCrawler):
    name = "시민사회연대회의"
    curated = True  # 시민사회단체 구인구직 전문 게시판

    def fetch(self) -> list[dict]:
        jobs = {}
        # 1~2 페이지 수집 (최신 공고 위주)
        for page in range(1, 3):
            try:
                items = self._parse_page(page)
                for item in items:
                    jobs[item["id"]] = item
                if not items:
                    break
            except Exception as e:
                logger.error(f"[{self.name}] 페이지 {page} 오류: {e}")
        return list(jobs.values())

    def _parse_page(self, page: int) -> list[dict]:
        resp = self.get(LIST_URL, params={"page": page})
        if not resp:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        results = []

        # 방법1: .li_board 구조 (CSS에서 확인된 클래스)
        items = (
            soup.select(".li_board ul li")
            or soup.select(".li_board li")
            or soup.select("ul.board_list li")
        )

        for item in items:
            try:
                job = self._parse_item(item)
                if job:
                    results.append(job)
            except Exception as e:
                logger.debug(f"[{self.name}] 항목 파싱 오류: {e}")

        # 방법2: /recruits/{숫자} 패턴 링크 직접 탐색
        if not results:
            results = self._fallback_link_parse(soup)

        return results

    def _parse_item(self, item) -> dict | None:
        # 제목 — .list_text_title 클래스 또는 a 태그
        title_tag = (
            item.select_one(".list_text_title a")
            or item.select_one(".list_text_title")
            or item.select_one(".tit a")
            or item.select_one("a")
        )
        if not title_tag:
            return None

        title = title_tag.get_text(strip=True)
        if not title:
            return None

        href = title_tag.get("href", "") if title_tag.name == "a" else (
            title_tag.select_one("a") or title_tag
        ).get("href", "")

        full_url = self._resolve_url(href)
        job_id   = self._extract_id(full_url)

        # 날짜 — 다양한 위치 시도
        deadline = ""
        date_tag = (
            item.select_one(".date")
            or item.select_one("[class*='date']")
            or item.select_one("[class*='period']")
        )
        if date_tag:
            deadline = date_tag.get_text(strip=True)
        else:
            text = item.get_text(" ", strip=True)
            dm = re.search(r"\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}", text)
            if dm:
                deadline = dm.group()

        # 기관명 — 배지 또는 부가 텍스트
        company_tag = (
            item.select_one(".badge")
            or item.select_one("[class*='company']")
            or item.select_one("[class*='org']")
        )
        company = company_tag.get_text(strip=True) if company_tag else ""

        return {
            "id":       job_id,
            "title":    title,
            "company":  company,
            "deadline": deadline,
            "url":      full_url,
            "source":   self.name,
        }

    def _fallback_link_parse(self, soup) -> list[dict]:
        """href=/recruits/{id} 패턴으로 직접 탐색"""
        results = []
        pattern = re.compile(r"^/recruits/(\d+)$")
        seen = set()

        for a in soup.find_all("a", href=pattern):
            m = pattern.match(a.get("href", ""))
            if not m:
                continue
            post_id = m.group(1)
            if post_id in seen:
                continue
            seen.add(post_id)

            title = a.get_text(strip=True)
            if not title:
                continue

            full_url = BASE_URL + a.get("href", "")
            parent_text = (a.parent or a).get_text(" ", strip=True)
            dm = re.search(r"\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}", parent_text)

            results.append({
                "id":       post_id,
                "title":    title,
                "company":  "",
                "deadline": dm.group() if dm else "",
                "url":      full_url,
                "source":   self.name,
            })

        return results

    def _resolve_url(self, href: str) -> str:
        if href.startswith("http"):
            return href
        if href.startswith("/"):
            return BASE_URL + href
        return BASE_URL + "/" + href.lstrip("./")

    def _extract_id(self, url: str) -> str:
        m = re.search(r"/recruits/(\d+)", url)
        if m:
            return m.group(1)
        return hashlib.md5(url.encode()).hexdigest()[:12]
