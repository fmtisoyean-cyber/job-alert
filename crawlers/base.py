import requests
import logging
from config import REQUEST_HEADERS

logger = logging.getLogger(__name__)


class BaseCrawler:
    name = "BaseCrawler"

    def fetch(self) -> list[dict]:
        """공고 목록 반환. 각 항목은 dict: {id, title, company, deadline, url, source}"""
        raise NotImplementedError

    def get(self, url: str, params: dict = None, timeout: int = 15) -> requests.Response | None:
        try:
            resp = requests.get(url, headers=REQUEST_HEADERS, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            logger.error(f"[{self.name}] GET 오류 ({url}): {e}")
            return None

    def post(self, url: str, data: dict = None, timeout: int = 15) -> requests.Response | None:
        try:
            resp = requests.post(url, headers=REQUEST_HEADERS, data=data, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            logger.error(f"[{self.name}] POST 오류 ({url}): {e}")
            return None
