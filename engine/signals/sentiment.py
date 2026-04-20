"""Derived sentiment signals — computed entirely from OHLCV + COT, no external API."""
import logging
from datetime import datetime, timezone, timedelta
from config.constants import SYMBOL

logger = logging.getLogger(__name__)

# Lookback bars for range-position calculation
RANGE_LOOKBACK = 96  # ~4 days of H1 bars


class SentimentSignals:
    async def extract_features(self) -> dict:
        features = {}
        try:
            snap = await self._compute_derived_sentiment()
            features["cot_net_noncomm_norm"] = await self._cot_net_norm()
            features["range_position"] = snap.get("range_position", 0.5)
            features["retail_trap_score"] = snap.get("retail_trap_score", 0.0)
            features["session_momentum"] = snap.get("session_momentum", 0.0)
            features["sentiment_composite"] = snap.get("composite_score", 0.0)
            features["news_pressure_score"] = await self._news_pressure()
        except Exception as e:
            logger.warning("Sentiment features unavailable: %s", e)
            features = {
                "cot_net_noncomm_norm": 0.0,
                "range_position": 0.5,
                "retail_trap_score": 0.0,
                "session_momentum": 0.0,
                "sentiment_composite": 0.0,
                "news_pressure_score": 0,
            }
        return features

    async def _compute_derived_sentiment(self) -> dict:
        """Compute and persist a DerivedSentimentSnapshot, return as dict."""
        from data.db import AsyncSessionLocal
        from data.repositories.ohlcv_repo import OHLCVRepository
        from data.repositories.cot_repo import COTRepository
        from data.repositories.sentiment_repo import SentimentRepository

        async with AsyncSessionLocal() as session:
            ohlcv_repo = OHLCVRepository(session)
            cot_repo = COTRepository(session)
            sent_repo = SentimentRepository(session)

            bars = await ohlcv_repo.get_bars(SYMBOL, "H1", limit=RANGE_LOOKBACK)
            cot_reports = await cot_repo.get_range(
                "GOLD - COMMODITY EXCHANGE INC.",
                (datetime.now(timezone.utc) - timedelta(days=365)).date(),
            )

            range_pos = _range_position(bars)
            session_mom = _session_momentum(bars)
            cot_div = _cot_divergence(bars, cot_reports)
            composite = round((range_pos - 0.5) * 2 * 0.4 + session_mom * 0.4 + cot_div * 0.2, 4)

            snap = {
                "range_position": range_pos,
                "retail_trap_score": 0.0,  # filled by RetailTrapSignal separately
                "cot_divergence": cot_div,
                "session_momentum": session_mom,
                "composite_score": composite,
            }

            await sent_repo.upsert(
                symbol=SYMBOL,
                timestamp=datetime.now(timezone.utc),
                **snap,
                source="derived",
            )
            return snap

    async def _cot_net_norm(self) -> float:
        """Normalize COT net non-commercial position to [-1, 1]."""
        try:
            from data.db import AsyncSessionLocal
            from data.repositories.cot_repo import COTRepository
            from datetime import date, timedelta
            async with AsyncSessionLocal() as session:
                repo = COTRepository(session)
                reports = await repo.get_range(
                    "GOLD - COMMODITY EXCHANGE INC.",
                    date.today() - timedelta(days=365),
                )
            if not reports:
                return 0.0
            nets = [r.net_noncomm for r in reports]
            latest = nets[-1]
            max_abs = max(abs(n) for n in nets)
            return round(float(latest / max_abs), 4) if max_abs > 0 else 0.0
        except Exception:
            return 0.0

    async def _news_pressure(self) -> int:
        try:
            from data.db import AsyncSessionLocal
            from data.repositories.event_repo import EventRepository
            async with AsyncSessionLocal() as session:
                repo = EventRepository(session)
                return await repo.count_high_impact_next_24h()
        except Exception:
            return 0


# ── Pure functions (testable without DB) ─────────────────────────────────────

def _range_position(bars: list) -> float:
    """Where is current price within the recent high-low range? [0=bottom, 1=top]"""
    if not bars:
        return 0.5
    closes = [b.close if hasattr(b, "close") else b["close"] for b in bars]
    highs = [b.high if hasattr(b, "high") else b["high"] for b in bars]
    lows = [b.low if hasattr(b, "low") else b["low"] for b in bars]
    rng = max(highs) - min(lows)
    if rng == 0:
        return 0.5
    pos = (closes[-1] - min(lows)) / rng
    return round(max(0.0, min(1.0, pos)), 4)


def _session_momentum(bars: list) -> float:
    """Directional bias: close vs session open, normalized to [-1, 1]."""
    if len(bars) < 2:
        return 0.0
    opens = [b.open if hasattr(b, "open") else b["open"] for b in bars]
    closes = [b.close if hasattr(b, "close") else b["close"] for b in bars]
    move = closes[-1] - opens[0]
    session_range = max(
        [b.high if hasattr(b, "high") else b["high"] for b in bars]
    ) - min(
        [b.low if hasattr(b, "low") else b["low"] for b in bars]
    )
    if session_range == 0:
        return 0.0
    return round(max(-1.0, min(1.0, move / session_range)), 4)


def _cot_divergence(bars: list, cot_reports: list) -> float:
    """COT divergence: if price rises but COT net falls, divergence is negative."""
    if not bars or len(cot_reports) < 2:
        return 0.0
    first_open = bars[0]["open"] if isinstance(bars[0], dict) else bars[0].open
    last_close = bars[-1]["close"] if isinstance(bars[-1], dict) else bars[-1].close
    price_dir = 1.0 if last_close > first_open else -1.0
    nets = [r.net_noncomm for r in cot_reports]
    cot_dir = 1.0 if nets[-1] > nets[-2] else -1.0
    # Agreement → 0 divergence; opposition → -1
    return round((cot_dir * price_dir - 1.0) / 2.0, 4)
