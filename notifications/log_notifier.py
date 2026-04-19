import logging
from notifications.base_notifier import BaseNotifier

logger = logging.getLogger("notifications")


class LogNotifier(BaseNotifier):
    def send(self, message: str) -> bool:
        logger.info("[NOTIFY] %s", message)
        return True
