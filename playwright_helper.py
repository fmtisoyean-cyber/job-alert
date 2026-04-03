"""
curl_cffi 기반 HTML 페치 헬퍼
Chrome TLS 핑거프린팅을 그대로 흉내내어 봇 탐지 우회.
Playwright 없이 GitHub Actions에서 동작.
"""
import logging

logger = logging.getLogger(__name__)


def fetch_html(url: str, **kwargs) -> str:
    """
    curl_cffi로 Chrome을 완벽히 흉내낸 요청.
    설치: pip install curl_cffi
    """
    try:
        from curl_cffi import requests as cf
        resp = cf.get(
            url,
            impersonate="chrome120",
            headers={"Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8"},
            timeout=20,
        )
        resp.raise_for_status()
        logger.debug(f"curl_cffi OK ({resp.status_code}): {url}")
        return resp.text
    except ImportError:
        logger.warning("curl_cffi 미설치. pip install curl_cffi")
    except Exception as e:
        logger.error(f"curl_cffi 오류 ({url}): {e}")
    return ""
