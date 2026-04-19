from abc import ABC, abstractmethod


class BaseNotifier(ABC):
    @abstractmethod
    def send(self, message: str) -> bool:
        ...

    def send_safe(self, message: str) -> bool:
        try:
            return self.send(message)
        except Exception:
            return False
