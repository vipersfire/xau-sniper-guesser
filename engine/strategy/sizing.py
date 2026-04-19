"""Kelly fraction + anomaly-adjusted position sizing."""
import logging
from utils.math_utils import kelly_fraction, anomaly_adjusted_size
from config.constants import MAX_KELLY_FRACTION
from config.strategy_params import load_params

logger = logging.getLogger(__name__)

LOT_STEP = 0.01
CONTRACT_SIZE = 100  # XAU/USD: 1 lot = 100 oz


def compute_lot_size(
    account_balance: float,
    sl_pips: float,
    anomaly_score: float = 0.0,
    regime_confidence: float = 1.0,
    win_rate: float | None = None,
    avg_win_pips: float | None = None,
    avg_loss_pips: float | None = None,
) -> float:
    p = load_params()
    sizing = p.get("position_sizing", {})
    base_risk_pct = sizing.get("base_risk_pct", 1.0) / 100
    min_lot = sizing.get("min_lot", 0.01)
    max_lot = sizing.get("max_lot", 1.0)

    if sl_pips <= 0 or account_balance <= 0:
        return min_lot

    # Kelly fraction (if stats available)
    if win_rate and avg_win_pips and avg_loss_pips:
        k = kelly_fraction(win_rate, avg_win_pips, avg_loss_pips)
        k = min(k, MAX_KELLY_FRACTION)
        k = max(k, 0.0)
    else:
        k = base_risk_pct

    # Apply anomaly penalty
    effective_k = anomaly_adjusted_size(k, anomaly_score)

    # Risk amount in currency
    risk_amount = account_balance * effective_k

    # Lot size: risk_amount / (sl_pips * pip_value_per_lot)
    pip_value_per_lot = 1.0  # USD per pip per lot for XAU/USD (approx, broker-dependent)
    lot = risk_amount / (sl_pips * pip_value_per_lot)

    # Round to lot step and clamp
    lot = round(lot / LOT_STEP) * LOT_STEP
    lot = max(min_lot, min(lot, max_lot))

    logger.debug(
        "Sizing: balance=%.0f sl=%.0f k=%.4f anomaly=%.3f → lot=%.2f",
        account_balance, sl_pips, effective_k, anomaly_score, lot,
    )
    return lot
