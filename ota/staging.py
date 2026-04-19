"""Atomic swap of OTA updates into live engine."""
import logging
from pathlib import Path
from ota.validator import verify_params_file, verify_strategy_module

logger = logging.getLogger(__name__)


def apply_params_update(path: Path, engine=None) -> bool:
    """Validate and hot-swap strategy_params.json."""
    ok, reason = verify_params_file(path)
    if not ok:
        logger.error("OTA params validation failed: %s — keeping old config", reason)
        _alert_failure(path.name, reason)
        return False

    # Atomic swap: invalidate cache
    from config.strategy_params import reload_params
    reload_params()

    # Notify engine to re-read params
    if engine and hasattr(engine, "strategy_selector"):
        try:
            engine.strategy_selector.reload_rules()
        except Exception as e:
            logger.warning("Could not reload strategy rules after params update: %s", e)

    logger.info("OTA params applied: %s", path.name)
    return True


def apply_module_update(path: Path, module_name: str, engine=None) -> bool:
    """Validate and hot-reload a strategy module."""
    ok, reason = verify_strategy_module(path)
    if not ok:
        logger.error("OTA module validation failed: %s — keeping old module", reason)
        _alert_failure(path.name, reason)
        return False

    from ota.loader import hot_reload_module
    success = hot_reload_module(module_name)
    if not success:
        _alert_failure(path.name, f"reload failed for {module_name}")
        return False

    logger.info("OTA module applied: %s → %s", path.name, module_name)
    return True


def _alert_failure(filename: str, reason: str):
    try:
        from notifications.telegram_notifier import send_alert
        send_alert(f"⚠️ OTA failed for {filename}: {reason}")
    except Exception:
        pass
