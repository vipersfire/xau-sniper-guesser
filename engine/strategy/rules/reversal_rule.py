from engine.strategy.rules.base_rule import BaseRule, EntrySignal
from engine.regime.regime_types import RegimeResult, DEFAULT_REGIME_STATS, RegimeType
from engine.strategy.sizing import compute_lot_size


class ReversalRule(BaseRule):
    supported_regimes = ["reversal_bull", "reversal_bear"]

    def evaluate(
        self,
        regime: RegimeResult,
        features: dict,
        account_balance: float,
        anomaly_score: float,
    ) -> EntrySignal | None:
        if regime.should_abstain:
            return None

        stats = regime.stats or DEFAULT_REGIME_STATS.get(regime.regime_type)
        if not stats or not stats.is_tradeable:
            return None

        # Reversals require ChoCH confirmation
        choch = features.get("choch_recent", 0)
        if choch == 0:
            return None

        # Sentiment divergence check: retail leaning wrong way
        retail_long = features.get("retail_long_pct", 50)
        cot_net = features.get("cot_net_noncomm_norm", 0)

        if regime.regime_type == RegimeType.REVERSAL_BULL:
            if retail_long > 55:  # retail too long — no contrarian edge
                return None
            if cot_net < -0.1:   # institutions bearish — wait
                return None
            direction = "buy"
        else:
            if retail_long < 45:
                return None
            if cot_net > 0.1:
                return None
            direction = "sell"

        from config.strategy_params import load_params
        p = load_params()
        sl_pips = stats.suggested_sl_pips * p.get("sl_multiplier", 1.0)
        tp_pips = stats.suggested_tp_pips * p.get("tp_multiplier", 1.0)

        lot = compute_lot_size(
            account_balance=account_balance,
            sl_pips=sl_pips,
            anomaly_score=anomaly_score,
            regime_confidence=regime.confidence,
        )

        return EntrySignal(
            direction=direction,
            sl_pips=sl_pips,
            tp_pips=tp_pips,
            lot_size=lot,
            expiry_bars=int(stats.avg_duration_hours * 4 + 8),
            reason=f"Reversal {direction} | ChoCH | retail={retail_long:.0f}% | conf={regime.confidence:.0%}",
        )
