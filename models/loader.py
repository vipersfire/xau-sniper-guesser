import logging
import pickle
from pathlib import Path
from models.registry import ModelRegistry

logger = logging.getLogger(__name__)


class ModelLoader:
    def __init__(self):
        self.registry = ModelRegistry()
        self._cache: dict | None = None

    def load(self, force_reload: bool = False) -> dict:
        if self._cache is None or force_reload:
            self._cache = self.registry.load()
            logger.info("Model loaded from registry")
        return self._cache

    def get_classifier(self):
        artifact = self.load()
        return artifact["model"]

    def get_feature_names(self) -> list[str]:
        artifact = self.load()
        return artifact.get("feature_names", [])

    def invalidate(self):
        self._cache = None
