from engine.strategy.rules.base_rule import BaseRule, EntrySignal
from engine.regime.regime_types import RegimeResult, DEFAULT_REGIME_STATS, RegimeType
from engine.strategy.sizing import compute_lot_size


class RangeRule(BaseRule):
    supported_regimes = ["ranging"]

    def evaluate(
        self,
        regime: RegimeResult,
        features: dict,
        account_balance: float,
        anomaly_score: float,
    ) -> EntrySignal | None:
        if regime.should_abstain:
            return None

        stats = regime.stats or DEFAULT_REGIME_STATS.get(RegimeType.RANGING)
        if not stats:
            return None

        # In ranging regime: buy at range low OB, sell at range high OB
        ob_dist = features.get("ob_distance_pips", 999)
        bos = features.get("bos_recent", 0)

        # No BOS in range — price inside range
        if bos != 0:
            return None

        if ob_dist > 15:
            return None  # Too far from OB

        # Determine direction from price vs EMA
        pve = features.get("price_vs_ema50", 0)
        direction = "buy" if pve < -0.1 else "sell" if pve > 0.1 else None
        if direction is None:
            return None

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
            expiry_bars=32,
            reason=f"Range {direction} | OB@{ob_dist:.0f}pips | conf={regime.confidence:.0%}",
        )
