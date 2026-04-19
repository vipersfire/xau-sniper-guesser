from enum import Enum


SYMBOL = "XAUUSD"

TIMEFRAMES = ["D1", "H4", "H1", "M15"]
TIMEFRAME_SECONDS = {
    "M15": 900,
    "H1": 3600,
    "H4": 14400,
    "D1": 86400,
}

PIP_SIZE = 0.01  # XAU/USD — 1 pip = $0.01

# Session windows in UTC
SESSION_WINDOWS = {
    "asian":   (0,  8),
    "london":  (7,  16),
    "ny":      (12, 21),
    "overlap": (12, 16),
}

SPREAD_BASELINE_MULTIPLIER = 1.5
ANOMALY_ABSTAIN_THRESHOLD = 2  # detectors that must flag before abstain

MIN_OHLCV_ROWS = 50_000

# Kelly fraction cap — never risk more than this fraction of account per trade
MAX_KELLY_FRACTION = 0.02

# Confidence below this → abstain
DEFAULT_CONFIDENCE_THRESHOLD = 0.60

# Drift thresholds (PSI)
PSI_WATCH = 0.10
PSI_INVESTIGATE = 0.20
PSI_CRITICAL = 0.25

# Circuit-breaker thresholds
CB_GOLD_30MIN_MOVE_PCT = 1.5
CB_SPREAD_VS_BASELINE = 3.0
CB_VIX_SPIKE_1HR = 20.0
CB_VOLUME_VS_BASELINE = 5.0

# Three-layer exit
MAX_LOSS_MULTIPLIER = 2.0       # secondary exit: loss > 2x expected SL
MAX_ACCOUNT_DD_24H_PCT = 5.0    # tertiary exit: 5% account drawdown in 24h


class EventLevel(int, Enum):
    KNOWN_KNOWN = 0       # FOMC etc — trade normally
    KNOWN_UNUSUAL = 1     # Surprise magnitude — reduce 40%
    KNOWN_VARIANT = 2     # New variant of known type — reduce 70%
    UNKNOWN = 3           # Black swan — abstain fully


EVENT_LEVEL_SIZE_FACTOR = {
    EventLevel.KNOWN_KNOWN:    1.00,
    EventLevel.KNOWN_UNUSUAL:  0.60,
    EventLevel.KNOWN_VARIANT:  0.30,
    EventLevel.UNKNOWN:        0.00,
}
