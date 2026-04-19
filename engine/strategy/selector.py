"""Strategy Selector — picks ruleset based on regime type."""
import logging
from engine.regime.regime_types import RegimeResult
from engine.strategy.rules.base_rule import BaseRule, EntrySignal
from engine.strategy.rules.trend_rule import TrendRule
from engine.strategy.rules.reversal_rule import ReversalRule
from engine.strategy.rules.range_rule import RangeRule

logger = logging.getLogger(__name__)


class StrategySelector:
    def __init__(self):
        self._rules: list[BaseRule] = [
            TrendRule(),
            ReversalRule(),
            RangeRule(),
        ]

    def select(
        self,
        regime: RegimeResult,
        features: dict,
        account_balance: float,
        anomaly_score: float,
    ) -> EntrySignal | None:
        if regime.should_abstain:
            logger.info("Abstaining: %s", regime.abstain_reason)
            return None

        for rule in self._rules:
            if rule.supports(regime.regime_type.value):
                signal = rule.evaluate(regime, features, account_balance, anomaly_score)
                if signal:
                    logger.info("Signal: %s", signal.reason)
                    return signal

        logger.debug("No rule matched regime: %s", regime.regime_type.value)
        return None

    def reload_rules(self):
        """Hot-reload rules after OTA update."""
        import importlib
        import engine.strategy.rules.trend_rule as tr
        import engine.strategy.rules.reversal_rule as rr
        import engine.strategy.rules.range_rule as rng
        importlib.reload(tr)
        importlib.reload(rr)
        importlib.reload(rng)
        self._rules = [tr.TrendRule(), rr.ReversalRule(), rng.RangeRule()]
        logger.info("Strategy rules hot-reloaded")
