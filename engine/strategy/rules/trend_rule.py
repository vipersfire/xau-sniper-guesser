from engine.strategy.rules.base_rule import BaseRule, EntrySignal
from engine.regime.regime_types import RegimeResult, DEFAULT_REGIME_STATS, RegimeType
from engine.strategy.sizing import compute_lot_size


class TrendRule(BaseRule):
    supported_regimes = ["trending_bullish", "trending_bearish"]

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

        bos = features.get("bos_recent", 0)
        if bos == 0:
            return None  # Require BOS confirmation

        fvg = features.get("fvg_present", 0)
        atr = features.get("atr_14_h1", 1.0)

        # Scale SL/TP from stats, adjusted by current ATR
        from config.strategy_params import load_params
        p = load_params()
        sl_pips = stats.suggested_sl_pips * p.get("sl_multiplier", 1.0)
        tp_pips = stats.suggested_tp_pips * p.get("tp_multiplier", 1.0)

        direction = "buy" if regime.regime_type == RegimeType.TRENDING_BULLISH else "sell"

        # Require FVG or OB for trend entries
        if not fvg and features.get("ob_distance_pips", 999) > 20:
            return None

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
            expiry_bars=int(stats.avg_duration_hours * 4 + 8),  # H1 bars + buffer
            reason=f"Trend {direction} | BOS+{'FVG' if fvg else 'OB'} | conf={regime.confidence:.0%}",
        )
