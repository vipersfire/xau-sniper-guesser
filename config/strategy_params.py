import json
from pathlib import Path
from config.settings import settings

_params_path = Path(settings.ota_strategy_params_path)
_cache: dict | None = None


def load_params(force_reload: bool = False) -> dict:
    global _cache
    if _cache is None or force_reload:
        try:
            with open(_params_path) as f:
                _cache = json.load(f)
        except Exception:
            _cache = {}
    return _cache


def reload_params() -> dict:
    global _cache
    _cache = None
    return load_params()
