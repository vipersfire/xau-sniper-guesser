from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str
    fix_command: str | None = None


class BaseCheck(ABC):
    name: str = "base"
    fix_command: str | None = None

    @abstractmethod
    async def run(self) -> CheckResult:
        ...

    def _pass(self, detail: str) -> CheckResult:
        return CheckResult(name=self.name, passed=True, detail=detail)

    def _fail(self, detail: str) -> CheckResult:
        return CheckResult(name=self.name, passed=False, detail=detail, fix_command=self.fix_command)
