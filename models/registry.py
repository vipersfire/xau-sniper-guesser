import logging
import pickle
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    path: Path
    exists: bool
    valid: bool
    trained_at: datetime | None
    error: str | None = None


class ModelRegistry:
    """Gates model artifact existence and validity."""

    REQUIRED_ARTIFACT = "regime_classifier.pkl"

    def __init__(self):
        self.artifacts_dir = Path(settings.artifacts_dir)

    def artifact_path(self, name: str | None = None) -> Path:
        return self.artifacts_dir / (name or self.REQUIRED_ARTIFACT)

    def check(self, name: str | None = None) -> ModelInfo:
        path = self.artifact_path(name)
        if not path.exists():
            return ModelInfo(path=path, exists=False, valid=False, trained_at=None, error="File not found")
        try:
            with open(path, "rb") as f:
                artifact = pickle.load(f)
            if not isinstance(artifact, dict) or "model" not in artifact:
                return ModelInfo(path=path, exists=True, valid=False, trained_at=None, error="Invalid artifact format")
            trained_at = artifact.get("trained_at")
            return ModelInfo(path=path, exists=True, valid=True, trained_at=trained_at)
        except Exception as e:
            return ModelInfo(path=path, exists=True, valid=False, trained_at=None, error=str(e))

    def is_ready(self) -> bool:
        info = self.check()
        return info.exists and info.valid

    def save(self, model, metadata: dict | None = None):
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        artifact = {
            "model": model,
            "trained_at": datetime.utcnow(),
            **(metadata or {}),
        }
        path = self.artifact_path()
        with open(path, "wb") as f:
            pickle.dump(artifact, f)
        logger.info("Model saved to %s", path)

    def load(self) -> dict:
        path = self.artifact_path()
        if not path.exists():
            raise FileNotFoundError(f"Model artifact not found: {path}")
        with open(path, "rb") as f:
            return pickle.load(f)
