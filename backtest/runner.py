import logging
from datetime import datetime, timedelta
from backtest.simulator import simulate_trades
from backtest.metrics import compute_metrics
from config.constants import SYMBOL

logger = logging.getLogger(__name__)


class BacktestRunner:
    def __init__(self):
        pass

    async def run_full(self, years: int = 5) -> dict:
        start = datetime.utcnow() - timedelta(days=years * 365)
        bars = await self._load_bars(start)
        if not bars:
            return {"error": "No OHLCV data available. Run ingestion first."}
        signals = await self._generate_signals(bars)
        trades = simulate_trades(bars, signals)
        metrics = compute_metrics([
            {"pnl": t.pnl_pips, "r_multiple": t.r_multiple, "regime_type": t.regime_type}
            for t in trades
        ])
        result = {
            "start": start.isoformat(),
            "end": datetime.utcnow().isoformat(),
            "bars": len(bars),
            "signals": len(signals),
            "metrics": metrics,
            "trades": [self._trade_dict(t) for t in trades],
        }
        self._save_last_report(result)
        return result

    async def run_regime(self, regime_type: str) -> dict:
        start = datetime.utcnow() - timedelta(days=5 * 365)
        bars = await self._load_bars(start)
        signals = await self._generate_signals(bars)
        filtered = [s for s in signals if s.get("regime_type") == regime_type]
        trades = simulate_trades(bars, filtered)
        metrics = compute_metrics([
            {"pnl": t.pnl_pips, "r_multiple": t.r_multiple}
            for t in trades
        ])
        return {"regime": regime_type, "signals": len(filtered), "metrics": metrics}

    async def _load_bars(self, start: datetime) -> list[dict]:
        try:
            from data.db import AsyncSessionLocal
            from data.repositories.ohlcv_repo import OHLCVRepository
            async with AsyncSessionLocal() as session:
                repo = OHLCVRepository(session)
                bars = await repo.get_bars(SYMBOL, "H1", start)
            return [
                {
                    "timestamp": b.timestamp,
                    "open": b.open,
                    "high": b.high,
                    "low": b.low,
                    "close": b.close,
                    "volume": b.volume,
                }
                for b in bars
            ]
        except Exception as e:
            logger.error("Failed to load bars: %s", e)
            return []

    async def _generate_signals(self, bars: list[dict]) -> list[dict]:
        """Generate regime-based entry signals from historical bars."""
        from engine.signals.structural import StructuralSignals
        signals = []
        if len(bars) < 50:
            return signals

        struct = StructuralSignals()
        for i in range(50, len(bars)):
            window = bars[max(0, i - 50): i]
            sig = struct.detect_entry(window)
            if sig:
                sig["bar_index"] = i
                signals.append(sig)

        return signals

    def _trade_dict(self, t) -> dict:
        return {
            "entry_time": t.entry_time.isoformat() if t.entry_time else None,
            "exit_time": t.exit_time.isoformat() if t.exit_time else None,
            "direction": t.direction,
            "entry_price": t.entry_price,
            "pnl_pips": t.pnl_pips,
            "r_multiple": t.r_multiple,
            "status": t.status,
            "regime_type": t.regime_type,
        }

    def _save_last_report(self, result: dict):
        import json
        from pathlib import Path
        path = Path("logs/last_backtest.json")
        path.parent.mkdir(exist_ok=True)
        with open(path, "w") as f:
            json.dump(result, f, default=str, indent=2)
