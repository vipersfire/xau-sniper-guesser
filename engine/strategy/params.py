"""Hot-reloadable strategy parameters proxy."""
from config.strategy_params import load_params, reload_params


def get(key: str, default=None):
    return load_params().get(key, default)


def reload():
    return reload_params()
