"""Hot-reload Python logic modules via importlib."""
import importlib
import importlib.util
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def hot_reload_module(module_name: str) -> bool:
    """Reload a Python module by dotted name."""
    if module_name not in sys.modules:
        logger.warning("Module %s not loaded — cannot reload", module_name)
        return False
    try:
        module = sys.modules[module_name]
        importlib.reload(module)
        logger.info("Hot-reloaded module: %s", module_name)
        return True
    except Exception as e:
        logger.error("Failed to hot-reload %s: %s", module_name, e)
        return False


def load_module_from_path(path: Path, module_name: str):
    """Load a module from a file path (for external strategy files)."""
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None:
        raise ImportError(f"Cannot load spec from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
