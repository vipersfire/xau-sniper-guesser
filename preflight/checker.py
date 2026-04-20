import asyncio
import logging
from preflight.checks.base_check import CheckResult
from preflight.checks.model_check import ModelCheck
from preflight.checks.data_check import (
    FREDDataCheck, COTDataCheck, OHLCVDataCheck, VIXBaselineCheck, DerivedSentimentCheck,
)
from preflight.checks.broker_check import BrokerCheck
from preflight.checks.spread_baseline_check import SpreadBaselineCheck
from preflight.checks.config_check import ConfigCheck

logger = logging.getLogger(__name__)


class PreflightChecker:
    def __init__(self, skip_broker: bool = False):
        self.checks = [
            ModelCheck(),
            FREDDataCheck(),
            COTDataCheck(),
            OHLCVDataCheck(),
            VIXBaselineCheck(),
            DerivedSentimentCheck(),
            SpreadBaselineCheck(),
            ConfigCheck(),
        ]
        if not skip_broker:
            self.checks.append(BrokerCheck())

    async def run(self) -> list[CheckResult]:
        results = await asyncio.gather(*[c.run() for c in self.checks])
        return list(results)

    async def all_pass(self) -> bool:
        results = await self.run()
        return all(r.passed for r in results)
