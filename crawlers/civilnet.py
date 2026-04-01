"""
시민사회단체연대회의 (civilnet.net) 크롤러
구인구직 게시판: /recruits  (JavaScript 렌더링)
공고 상세 URL:  /recruits/{id}

CSS: .li_board ul li / .list_text_title
"""
import hashlib
import logging
import re
from bs4 import BeautifulSoup
from playwright_helper import fetch_html
from .base import BaseCrawler

logger = logging.getLogger(__name__)

BASE_URL = "https://civilnet.net"
LIST_URL = f"{BASE_URL}/recruits"
ID_RE    = re.compile(r"^/recruits/(\d+)$")


class CivilnetCrawler(BaseCrawler):
    name    = "시민사회연대회의"
    curated = True

    def fetch(self) -> list[dict]:
        jobs = {}
        for page in range(1, 3):
            try:
                url  = LIST_URL if page == 1 else f"{LIST_URL}?page={page}"
                html = fetch_html(url)              # Playwright 렌더링
                if not html:
                    resp = self.get(url)             # fallback: requests
                    html = resp.text if resp else ""
                if not html:
                    break

                items = self._parse(html)
                if not items:
                    break
                for item in items:
                    jobs[item["id"]] = item
            except Exception as e:
                logger.error(f"[{self.name}] 페이지 {page} 오류: {e}")

        logger.info(f"[{self.name}] 수집: {len(jobs)}개")
        return list(jobs.values())

    def _parse(self, html: str) -> list[dict]:
        soup    = BeautifulSoup(html, "lxml")
        results = {}

        # 방법1: .li_board 구조 (CSS에서 확인된 클래스)
        for li in (soup.select(".li_board ul li") or soup.select(".li_board li")):
            job = self._parse_item(li)
            if job:
                results[job["id"]] = job

        # 방법2: /recruits/{숫자} 패턴 링크 직접 탐색
        if not results:
            seen = set()
            for a in soup.find_all("a", href=ID_RE):
                m = ID_RE.match(a.get("href", ""))
                if not m:
                    continue
                post_id = m.group(1)
                if post_id in seen:
                    continue
                seen.add(post_id)

                title = a.get_text(strip=True)
                if not title:
                    continue

                full_url    = BASE_URL + a["href"]
                parent_text = (a.parent or a).get_text(" ", strip=True)
                dm = re.search(r"\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}", parent_text)
                results[post_id] = {
                    "id":       post_id,
                    "title":    title,
                    "company":  "",
                    "deadline": dm.group() if dm else "",
                    "url":      full_url,
                    "source":   self.name,
                }

        return list(results.values())

    def _parse_item(self, li) -> dict | None:
        title_tag = (
            li.select_one(".list_text_title a")
            or li.select_one(".tit a")
            or li.select_one("a")
        )
        if not title_tag:
            return None

        title = title_tag.get_text(strip=True)
        if not title:
            return None

        href     = title_tag.get("href", "")
        full_url = BASE_URL + href if href.startswith("/") else href
        m        = ID_RE.match(href)
        post_id  = m.group(1) if m else hashlib.md5(full_url.encode()).hexdigest()[:12]

        # 날짜
        deadline = ""
        date_tag = li.select_one(".date, [class*='date'], [class*='period']")
        if date_tag:
            deadline = date_tag.get_text(strip=True)
        else:
            dm = re.search(r"\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}", li.get_text(" ", strip=True))
            if dm:
                deadline = dm.group()

        company_tag = li.select_one(".badge, [class*='company'], [class*='org']")
        company = company_tag.get_text(strip=True) if company_tag else ""

        return {
            "id":       post_id,
            "title":    title,
            "company":  company,
            "deadline": deadline,
            "url":      full_url,
            "source":   self.name,
        }
