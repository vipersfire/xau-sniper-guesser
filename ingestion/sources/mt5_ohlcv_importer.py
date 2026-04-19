import logging
from datetime import datetime, timezone, timedelta
from ingestion.base.importer import BaseImporter
from data.db import AsyncSessionLocal
from data.repositories.ohlcv_repo import OHLCVRepository
from config.constants import SYMBOL, TIMEFRAMES
from utils.data_quality import score_bar

logger = logging.getLogger(__name__)


class MT5OHLCVImporter(BaseImporter):
    source_name = "mt5_ohlcv"
    run_interval = 900  # 15 min

    async def fetch(self) -> dict[str, list]:
        from mt5.adapter import MT5Adapter
        adapter = MT5Adapter()
        adapter.connect()
        data = {}
        try:
            for tf in TIMEFRAMES:
                data[tf] = adapter.get_ohlcv(
                    symbol=SYMBOL,
                    timeframe=tf,
                    bars=50000,
                )
        finally:
            adapter.disconnect()
        return data

    async def parse(self, raw: dict[str, list]) -> list[dict]:
        records = []
        for tf, bars in raw.items():
            prev_close = None
            for bar in bars:
                q = score_bar(
                    open_=bar["open"],
                    high=bar["high"],
                    low=bar["low"],
                    close=bar["close"],
                    volume=bar.get("tick_volume", 0),
                    spread=bar.get("spread", 0),
                    prev_close=prev_close,
                )
                records.append({
                    "symbol": SYMBOL,
                    "timeframe": tf,
                    "timestamp": datetime.fromtimestamp(bar["time"], tz=timezone.utc),
                    "open": bar["open"],
                    "high": bar["high"],
                    "low": bar["low"],
                    "close": bar["close"],
                    "volume": bar.get("tick_volume", 0),
                    "spread": bar.get("spread", 0),
                    "quality_score": q.quality_score,
                    "flags": [f.value for f in q.flags],
                })
                prev_close = bar["close"]
        return records

    async def store(self, data: list[dict]) -> int:
        if not data:
            return 0
        async with AsyncSessionLocal() as session:
            repo = OHLCVRepository(session)
            await repo.upsert_bars(data)
        return len(data)
