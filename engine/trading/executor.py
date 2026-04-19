"""Sends orders to MT5, tracks state, handles exits."""
import logging
from datetime import datetime, timezone
from config.constants import SYMBOL, PIP_SIZE
from engine.trading.position_manager import PositionManager, OpenPosition
from engine.strategy.rules.base_rule import EntrySignal
from engine.regime.regime_types import RegimeResult

logger = logging.getLogger(__name__)


class TradeExecutor:
    def __init__(self):
        self.position_manager = PositionManager()

    async def execute(
        self,
        signal: EntrySignal,
        regime: RegimeResult,
        anomaly_score: float,
        current_price: float | None = None,
    ) -> int | None:
        """Place order and record in DB. Returns trade_id or None."""
        from mt5.adapter import MT5Adapter
        from mt5.account import get_balance
        from data.db import AsyncSessionLocal
        from data.repositories.trade_repo import TradeRepository
        from data.models.trade import Trade

        adapter = MT5Adapter()
        balance = get_balance()

        # Compute SL/TP prices from current tick
        if current_price is None:
            if adapter.connect():
                tick = adapter.get_tick(SYMBOL)
                current_price = tick["ask"] if signal.direction == "buy" else tick["bid"]
                adapter.disconnect()

        if current_price is None:
            logger.error("No current price — cannot execute")
            return None

        if signal.direction == "buy":
            sl_price = current_price - signal.sl_pips * PIP_SIZE
            tp_price = current_price + signal.tp_pips * PIP_SIZE
        else:
            sl_price = current_price + signal.sl_pips * PIP_SIZE
            tp_price = current_price - signal.tp_pips * PIP_SIZE

        # Place order
        result = adapter.place_order(
            symbol=SYMBOL,
            direction=signal.direction,
            lot=signal.lot_size,
            sl_price=sl_price,
            tp_price=tp_price,
            comment=f"sniper|{regime.regime_type.value[:8]}",
        )

        if result is None:
            logger.error("Order placement failed")
            return None

        ticket = result.get("ticket", -1)

        # Record in DB
        trade = Trade(
            ticket=ticket,
            symbol=SYMBOL,
            direction=signal.direction,
            regime_type=regime.regime_type.value,
            regime_confidence=regime.confidence,
            entry_price=current_price,
            sl_price=sl_price,
            tp_price=tp_price,
            lot_size=signal.lot_size,
            open_time=datetime.now(timezone.utc),
            status="open",
            anomaly_score=anomaly_score,
            meta={"reason": signal.reason},
        )

        async with AsyncSessionLocal() as session:
            repo = TradeRepository(session)
            trade = await repo.create(trade)

        # Track in memory
        self.position_manager.add(OpenPosition(
            trade_id=trade.id,
            ticket=ticket,
            symbol=SYMBOL,
            direction=signal.direction,
            entry_price=current_price,
            sl_price=sl_price,
            tp_price=tp_price,
            lot_size=signal.lot_size,
            open_time=trade.open_time,
            expected_sl_loss=signal.sl_pips,
            regime_type=regime.regime_type.value,
        ))

        logger.info(
            "Trade opened: %s %s %.2f lots @%.2f SL=%.2f TP=%.2f ticket=%d",
            signal.direction, SYMBOL, signal.lot_size, current_price, sl_price, tp_price, ticket,
        )
        return trade.id

    async def close_trade(self, trade_id: int, reason: str = "manual"):
        from mt5.adapter import MT5Adapter
        from data.db import AsyncSessionLocal
        from data.repositories.trade_repo import TradeRepository
        from utils.math_utils import r_multiple

        pos = self.position_manager.get(trade_id)
        if not pos:
            return

        adapter = MT5Adapter()
        adapter.connect()
        success = adapter.close_position(pos.ticket)
        tick = adapter.get_tick(SYMBOL)
        close_price = (tick["bid"] if pos.direction == "buy" else tick["ask"]) if tick else pos.entry_price
        adapter.disconnect()

        direction_mult = 1 if pos.direction == "buy" else -1
        pnl = (close_price - pos.entry_price) * 100 * direction_mult
        r = r_multiple(pos.entry_price, close_price, pos.sl_price, direction_mult)

        async with AsyncSessionLocal() as session:
            repo = TradeRepository(session)
            trade = await repo.get(trade_id)
            if trade:
                trade.close_time = datetime.now(timezone.utc)
                trade.close_price = close_price
                trade.pnl = pnl
                trade.r_multiple = r
                trade.status = "closed"
                await repo.update(trade)

        self.position_manager.remove(trade_id)
        logger.info("Trade closed: id=%d pnl=%.1f pips R=%.2f reason=%s", trade_id, pnl, r, reason)
