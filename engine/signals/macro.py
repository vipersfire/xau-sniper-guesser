"""Macro signals: yields, DXY, real yields. No AI."""
import logging
from datetime import date, timedelta

logger = logging.getLogger(__name__)

FRED_SERIES_MAP = {
    "real_yield_10y": "DFII10",
    "fed_funds_rate": "DFF",
    "breakeven_10y":  "T10YIE",
    "treasury_10y":   "DGS10",
}


class MacroSignals:
    async def extract_features(self) -> dict:
        features = {}
        try:
            from data.db import AsyncSessionLocal
            from data.repositories.macro_repo import MacroRepository
            async with AsyncSessionLocal() as session:
                repo = MacroRepository(session)
                for feature_name, series_id in FRED_SERIES_MAP.items():
                    val = await repo.latest_value(series_id)
                    features[feature_name] = float(val) if val is not None else 0.0

            # DXY slope — use normalized difference if stored as DXY series
            dxy = await self._get_dxy_slope()
            features["dxy_slope_h4"] = dxy
        except Exception as e:
            logger.warning("Macro features unavailable: %s", e)
            features = {k: 0.0 for k in ["real_yield_10y", "fed_funds_rate", "breakeven_10y", "treasury_10y", "dxy_slope_h4"]}
        return features

    async def _get_dxy_slope(self) -> float:
        """Approximate DXY slope from OHLCV if available."""
        try:
            from data.db import AsyncSessionLocal
            from data.repositories.ohlcv_repo import OHLCVRepository
            from datetime import datetime
            import numpy as np
            async with AsyncSessionLocal() as session:
                repo = OHLCVRepository(session)
                start = datetime.utcnow() - timedelta(days=2)
                bars = await repo.get_bars("USDX", "H4", start)
            if len(bars) < 2:
                return 0.0
            closes = [b.close for b in bars[-10:]]
            if len(closes) < 2:
                return 0.0
            slope = (closes[-1] - closes[0]) / closes[0] * 100
            return round(float(slope), 4)
        except Exception:
            return 0.0
