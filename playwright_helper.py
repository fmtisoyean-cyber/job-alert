"""
Playwright 기반 HTML 페치 헬퍼
JavaScript 렌더링이 필요한 사이트나 봇 탐지 우회에 사용
"""
import logging

logger = logging.getLogger(__name__)


def fetch_html(url: str, wait_for: str = "networkidle", timeout: int = 30000) -> str:
    """
    Playwright Chromium으로 페이지를 완전히 렌더링한 후 HTML 반환.
    playwright 미설치 시 빈 문자열 반환 (requests fallback 사용).
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("playwright 미설치. pip install playwright && playwright install chromium")
        return ""

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                ),
                locale="ko-KR",
                extra_http_headers={"Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8"},
            )
            page = context.new_page()
            page.goto(url, timeout=timeout)
            page.wait_for_load_state(wait_for, timeout=timeout)
            html = page.content()
            browser.close()
            return html
    except Exception as e:
        logger.error(f"Playwright 오류 ({url}): {e}")
        return ""
