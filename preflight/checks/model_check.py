from preflight.checks.base_check import BaseCheck, CheckResult
from models.registry import ModelRegistry


class ModelCheck(BaseCheck):
    name = "Model artifact"
    fix_command = "cli backtest --train"

    async def run(self) -> CheckResult:
        registry = ModelRegistry()
        info = registry.check()
        if not info.exists:
            return self._fail("regime_classifier.pkl not found")
        if not info.valid:
            return self._fail(f"Artifact invalid: {info.error}")
        age = ""
        if info.trained_at:
            from datetime import datetime
            delta = datetime.utcnow() - info.trained_at
            hours = int(delta.total_seconds() / 3600)
            age = f"trained {hours}h ago"
        return self._pass(f"regime_classifier.pkl ({age})")
