import requests
import logging
from config import BOT_TOKEN, CHAT_ID

logger = logging.getLogger(__name__)

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


class TelegramNotifier:
    def send(self, job: dict) -> bool:
        if not BOT_TOKEN or not CHAT_ID:
            logger.error("BOT_TOKEN 또는 CHAT_ID가 설정되지 않았습니다. .env 파일을 확인하세요.")
            return False

        title    = job.get("title", "(제목 없음)")
        company  = job.get("company", "(기관명 없음)")
        deadline = job.get("deadline", "미정")
        url      = job.get("url", "")
        source   = job.get("source", "")

        text = (
            f"📢 *새 채용공고 알림*\n\n"
            f"🏢 *기관명:* {self._escape(company)}\n"
            f"📋 *공고명:* {self._escape(title)}\n"
            f"📅 *마감일:* {self._escape(deadline)}\n"
            f"🔗 *출처:* {self._escape(source)}\n"
            f"[공고 바로가기]({url})"
        )

        try:
            resp = requests.post(
                TELEGRAM_API,
                json={
                    "chat_id": CHAT_ID,
                    "text": text,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": False,
                },
                timeout=10,
            )
            if resp.status_code == 200:
                return True
            else:
                logger.error(f"텔레그램 전송 실패: {resp.status_code} {resp.text}")
                return False
        except Exception as e:
            logger.error(f"텔레그램 전송 오류: {e}")
            return False

    @staticmethod
    def _escape(text: str) -> str:
        """Markdown 특수문자 이스케이프"""
        for ch in ["_", "*", "[", "]", "(", ")", "~", "`", ">", "#", "+", "-", "=", "|", "{", "}", ".", "!"]:
            text = text.replace(ch, f"\\{ch}")
        return text

    def send_summary(self, count: int):
        """실행 완료 후 요약 메시지 전송"""
        if not BOT_TOKEN or not CHAT_ID:
            return
        text = f"✅ 채용공고 수집 완료 — 신규 공고 *{count}개* 알림 전송"
        try:
            requests.post(
                TELEGRAM_API,
                json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"},
                timeout=10,
            )
        except Exception:
            pass
