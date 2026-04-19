from engine.regime.regime_types import RegimeType, RegimeResult, DEFAULT_REGIME_STATS
from config.strategy_params import load_params


def should_abstain(result: RegimeResult) -> tuple[bool, str]:
    """Returns (abstain, reason)."""
    params = load_params()
    thresholds = params.get("regime_confidence_thresholds", {})
    threshold = thresholds.get(result.regime_type.value, params.get("confidence_threshold", 0.65))

    if result.regime_type == RegimeType.UNKNOWN:
        return True, "Regime type is UNKNOWN"

    if result.confidence < threshold:
        return True, f"Confidence {result.confidence:.1%} < threshold {threshold:.1%}"

    stats = result.stats or DEFAULT_REGIME_STATS.get(result.regime_type)
    if stats and not stats.is_tradeable:
        return True, f"Regime stats not tradeable (n={stats.occurrences}, wr={stats.win_rate:.0%})"

    return False, ""
