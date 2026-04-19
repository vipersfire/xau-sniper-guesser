import logging
import urllib.request
import urllib.parse
import json
from notifications.base_notifier import BaseNotifier
from config.settings import settings

logger = logging.getLogger(__name__)


class TelegramNotifier(BaseNotifier):
    def __init__(self):
        self.token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id

    def send(self, message: str) -> bool:
        if not self.token or not self.chat_id:
            logger.debug("Telegram not configured — skipping notification")
            return False
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = json.dumps({
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML",
        }).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except Exception as e:
            logger.error("Telegram send failed: %s", e)
            return False


_notifier: TelegramNotifier | None = None


def send_alert(message: str) -> bool:
    global _notifier
    if _notifier is None:
        _notifier = TelegramNotifier()
    return _notifier.send_safe(message)
