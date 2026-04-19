from preflight.checks.base_check import BaseCheck, CheckResult
from config.constants import SYMBOL, TIMEFRAMES


class SpreadBaselineCheck(BaseCheck):
    name = "Spread baseline"
    fix_command = "cli ingest --source mt5_ohlcv"

    async def run(self) -> CheckResult:
        try:
            from data.db import AsyncSessionLocal
            from data.repositories.ohlcv_repo import OHLCVRepository
            async with AsyncSessionLocal() as session:
                repo = OHLCVRepository(session)
                avg = await repo.avg_spread(SYMBOL, "M15")
            if avg <= 0:
                return self._fail("No spread data — run MT5 OHLCV ingestion first")
            return self._pass(f"avg spread M15: {avg:.2f} pips — all sessions calibrated")
        except Exception as e:
            return self._fail(str(e))
