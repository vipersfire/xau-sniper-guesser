"""Pre-trade safety checks."""
import logging
from config.constants import MAX_ACCOUNT_DD_24H_PCT, MAX_LOSS_MULTIPLIER
from config.settings import settings

logger = logging.getLogger(__name__)


class TradeGuards:
    def __init__(self):
        pass

    async def check_all(
        self,
        direction: str,
        lot: float,
        sl_pips: float,
        account_balance: float,
        anomaly_should_abstain: bool,
        circuit_breaker_tripped: bool,
    ) -> tuple[bool, str]:
        """Returns (ok_to_trade, reason)."""

        if circuit_breaker_tripped:
            return False, "Circuit breaker tripped"

        if anomaly_should_abstain:
            return False, "Anomaly consensus: abstain"

        if lot <= 0:
            return False, "Zero lot size"

        if sl_pips <= 0:
            return False, "Invalid SL"

        # 24h drawdown check
        dd_ok, dd_reason = await self._check_drawdown(account_balance)
        if not dd_ok:
            return False, dd_reason

        # Max concurrent positions
        open_count = await self._open_position_count()
        if open_count >= settings.max_concurrent_positions:
            return False, f"Max concurrent positions reached ({open_count})"

        return True, ""

    async def _check_drawdown(self, account_balance: float) -> tuple[bool, str]:
        try:
            from data.db import AsyncSessionLocal
            from data.repositories.trade_repo import TradeRepository
            async with AsyncSessionLocal() as session:
                repo = TradeRepository(session)
                dd = await repo.account_drawdown_24h()
            dd_pct = dd / account_balance * 100 if account_balance > 0 else 0
            if dd_pct > MAX_ACCOUNT_DD_24H_PCT:
                return False, f"24h drawdown {dd_pct:.1f}% > {MAX_ACCOUNT_DD_24H_PCT}%"
        except Exception as e:
            logger.warning("Drawdown check failed: %s", e)
        return True, ""

    async def _open_position_count(self) -> int:
        try:
            from data.db import AsyncSessionLocal
            from data.repositories.trade_repo import TradeRepository
            async with AsyncSessionLocal() as session:
                repo = TradeRepository(session)
                positions = await repo.get_open()
                return len(positions)
        except Exception:
            return 0
