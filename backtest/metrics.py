import numpy as np
from typing import Any


def compute_metrics(trades: list[dict]) -> dict[str, Any]:
    if not trades:
        return {"error": "No trades"}

    pnls = np.array([t.get("pnl", 0.0) for t in trades])
    rs = np.array([t.get("r_multiple", 0.0) for t in trades])
    wins = pnls[pnls > 0]
    losses = pnls[pnls < 0]

    win_rate = len(wins) / len(pnls) if len(pnls) > 0 else 0
    avg_win = float(wins.mean()) if len(wins) > 0 else 0
    avg_loss = float(abs(losses.mean())) if len(losses) > 0 else 0
    expectancy = win_rate * avg_win - (1 - win_rate) * avg_loss

    equity = np.cumsum(pnls)
    peak = np.maximum.accumulate(equity)
    drawdowns = equity - peak
    max_dd = float(drawdowns.min())

    return {
        "total_trades": len(trades),
        "win_rate": round(win_rate, 4),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "expectancy": round(expectancy, 2),
        "profit_factor": round(wins.sum() / abs(losses.sum()), 2) if losses.sum() != 0 else float("inf"),
        "max_drawdown": round(max_dd, 2),
        "total_pnl": round(float(pnls.sum()), 2),
        "avg_r": round(float(rs.mean()), 3) if len(rs) > 0 else 0,
        "median_r": round(float(np.median(rs)), 3) if len(rs) > 0 else 0,
        "sharpe": _sharpe(pnls),
    }


def _sharpe(pnls: np.ndarray, periods_per_year: int = 252) -> float:
    if len(pnls) < 2 or pnls.std() == 0:
        return 0.0
    return float(pnls.mean() / pnls.std() * np.sqrt(periods_per_year))


async def compute_r_multiple_distribution() -> dict:
    from data.db import AsyncSessionLocal
    from data.repositories.trade_repo import TradeRepository
    from sqlalchemy import select
    from data.models.trade import Trade
    async with AsyncSessionLocal() as session:
        q = select(Trade.r_multiple).where(Trade.status == "closed", Trade.r_multiple.isnot(None))
        result = await session.execute(q)
        rs = [r[0] for r in result.all()]
    if not rs:
        return {}
    arr = np.array(rs)
    return {
        "avg_r": round(float(arr.mean()), 3),
        "median_r": round(float(np.median(arr)), 3),
        "expectancy": round(float(arr.mean()), 3),
        "count": len(arr),
    }
