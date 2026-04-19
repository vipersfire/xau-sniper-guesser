"""Hash verification + dry-run validation before OTA swap."""
import json
import logging
from pathlib import Path
from utils.hashing import sha256_file

logger = logging.getLogger(__name__)


def verify_params_file(path: Path) -> tuple[bool, str]:
    """Validate strategy_params.json before accepting OTA update."""
    try:
        with open(path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"
    except Exception as e:
        return False, str(e)

    required_keys = ["confidence_threshold", "position_sizing", "circuit_breaker"]
    for key in required_keys:
        if key not in data:
            return False, f"Missing required key: {key}"

    conf = data.get("confidence_threshold")
    if not isinstance(conf, (int, float)) or not (0.0 < conf < 1.0):
        return False, f"confidence_threshold must be float in (0, 1): {conf}"

    return True, "OK"


def verify_strategy_module(path: Path) -> tuple[bool, str]:
    """Dry-run validate a Python strategy module."""
    try:
        import ast
        with open(path) as f:
            source = f.read()
        ast.parse(source)
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, str(e)
    return True, "OK"


def file_hash(path: Path) -> str:
    return sha256_file(path)
