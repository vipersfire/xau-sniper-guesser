from datetime import date, timedelta, datetime
from preflight.checks.base_check import BaseCheck, CheckResult
from config.constants import MIN_OHLCV_ROWS, SYMBOL, TIMEFRAMES


class FREDDataCheck(BaseCheck):
    name = "FRED data"
    fix_command = "cli ingest --source fred"

    async def run(self) -> CheckResult:
        try:
            from data.db import AsyncSessionLocal
            from data.repositories.macro_repo import MacroRepository
            async with AsyncSessionLocal() as session:
                repo = MacroRepository(session)
                latest = await repo.latest_date("DGS10")
            if not latest:
                return self._fail("No FRED data found")
            days_old = (date.today() - latest).days
            if days_old > 30:
                return self._fail(f"FRED data stale: {days_old} days old")
            return self._pass(f"last updated: {latest.isoformat()}")
        except Exception as e:
            return self._fail(str(e))


class COTDataCheck(BaseCheck):
    name = "COT data"
    fix_command = "cli ingest --source cot"

    async def run(self) -> CheckResult:
        try:
            from data.db import AsyncSessionLocal
            from data.repositories.cot_repo import COTRepository
            async with AsyncSessionLocal() as session:
                repo = COTRepository(session)
                latest = await repo.latest_date("GOLD_COT")
            if not latest:
                return self._fail("No COT data found")
            days_old = (date.today() - latest).days
            if days_old > 7:
                return self._fail(f"COT data stale: {days_old} days old")
            return self._pass(f"last updated: {latest.isoformat()}")
        except Exception as e:
            return self._fail(str(e))


class OHLCVDataCheck(BaseCheck):
    name = "OHLCV data"
    fix_command = "cli ingest --source mt5_ohlcv"

    async def run(self) -> CheckResult:
        try:
            from data.db import AsyncSessionLocal
            from data.repositories.ohlcv_repo import OHLCVRepository
            async with AsyncSessionLocal() as session:
                repo = OHLCVRepository(session)
                count = await repo.count(symbol=SYMBOL)
            if count < MIN_OHLCV_ROWS:
                return self._fail(f"Only {count:,} OHLCV rows (need {MIN_OHLCV_ROWS:,})")
            return self._pass(f"{count:,} rows")
        except Exception as e:
            return self._fail(str(e))
