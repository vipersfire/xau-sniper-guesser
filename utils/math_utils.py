import numpy as np


def kelly_fraction(win_rate: float, avg_win: float, avg_loss: float) -> float:
    """Full Kelly. Caller should apply a fractional multiplier (e.g. 0.25)."""
    if avg_loss == 0 or win_rate <= 0:
        return 0.0
    b = avg_win / avg_loss
    q = 1.0 - win_rate
    return (b * win_rate - q) / b


def anomaly_adjusted_size(base_size: float, anomaly_score: float) -> float:
    """Exponential decay. score=0 → full size, score=1 → zero."""
    anomaly_score = max(0.0, min(1.0, anomaly_score))
    return base_size * (1.0 - anomaly_score) ** 3


def r_multiple(entry: float, exit_: float, sl: float, direction: int) -> float:
    """direction: +1 long, -1 short."""
    risk = abs(entry - sl)
    if risk == 0:
        return 0.0
    return direction * (exit_ - entry) / risk


def atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> np.ndarray:
    n = len(closes)
    tr = np.zeros(n)
    tr[0] = highs[0] - lows[0]
    for i in range(1, n):
        tr[i] = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
    atr_vals = np.zeros(n)
    if n >= period:
        atr_vals[period - 1] = tr[:period].mean()
        for i in range(period, n):
            atr_vals[i] = (atr_vals[i - 1] * (period - 1) + tr[i]) / period
    return atr_vals


def psi(expected: np.ndarray, actual: np.ndarray, buckets: int = 10) -> float:
    """Population Stability Index between two distributions."""
    bins = np.percentile(expected, np.linspace(0, 100, buckets + 1))
    bins[0] -= 1e-9
    bins[-1] += 1e-9
    exp_counts, _ = np.histogram(expected, bins=bins)
    act_counts, _ = np.histogram(actual, bins=bins)
    exp_pct = exp_counts / exp_counts.sum()
    act_pct = act_counts / act_counts.sum()
    # Avoid log(0)
    exp_pct = np.where(exp_pct == 0, 1e-9, exp_pct)
    act_pct = np.where(act_pct == 0, 1e-9, act_pct)
    return float(np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct)))


def ema(values: np.ndarray, period: int) -> np.ndarray:
    result = np.zeros_like(values, dtype=float)
    k = 2.0 / (period + 1)
    result[0] = values[0]
    for i in range(1, len(values)):
        result[i] = values[i] * k + result[i - 1] * (1 - k)
    return result


def zscore(values: np.ndarray, window: int = 20) -> np.ndarray:
    result = np.full_like(values, np.nan, dtype=float)
    for i in range(window - 1, len(values)):
        window_vals = values[i - window + 1 : i + 1]
        std = window_vals.std()
        if std > 0:
            result[i] = (values[i] - window_vals.mean()) / std
    return result
