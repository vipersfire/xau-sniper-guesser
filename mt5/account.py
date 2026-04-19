"""MT5 account info helper."""
import logging
from config.settings import settings

logger = logging.getLogger(__name__)


def get_balance() -> float:
    if settings.account_balance_override > 0:
        return settings.account_balance_override
    try:
        from mt5.adapter import MT5Adapter
        adapter = MT5Adapter()
        if adapter.connect():
            info = adapter.account_info()
            adapter.disconnect()
            return float(info.get("balance", 10000.0))
    except Exception as e:
        logger.warning("Could not get MT5 balance: %s", e)
    return 10000.0  # fallback for paper trading


def get_margin_free() -> float:
    try:
        from mt5.adapter import MT5Adapter
        adapter = MT5Adapter()
        if adapter.connect():
            info = adapter.account_info()
            adapter.disconnect()
            return float(info.get("margin_free", 0.0))
    except Exception:
        pass
    return 0.0
