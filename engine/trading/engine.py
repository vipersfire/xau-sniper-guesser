"""TradingEngine — top-level orchestrator for one trading cycle."""
import logging
from datetime import datetime
from engine.regime.monitor import RegimeMonitor
from engine.strategy.selector import StrategySelector
from engine.trading.executor import TradeExecutor
from engine.trading.guards import TradeGuards
from anomaly.detector import AnomalyDetector
from anomaly.circuit_breaker import BlackSwanCircuitBreaker
from engine.signals.structural import StructuralSignals
from engine.signals.macro import MacroSignals
from engine.signals.sentiment import SentimentSignals
from config.constants import SYMBOL

logger = logging.getLogger(__name__)


class TradingEngine:
    """Coordinates: feature extraction → anomaly check → regime classify → strategy → execute."""

    def __init__(self):
        self.regime_monitor = RegimeMonitor()
        self.strategy_selector = StrategySelector()
        self.executor = TradeExecutor()
        self.guards = TradeGuards()
        self.anomaly_detector = AnomalyDetector()
        self.circuit_breaker = BlackSwanCircuitBreaker()
        self.structural = StructuralSignals()
        self.macro = MacroSignals()
        self.sentiment = SentimentSignals()
        self._bars_cache: list[dict] = []

    async def on_candle_close(self, timeframe: str, bar: dict):
        """Called by CandleWatcherThread on each candle close."""
        if timeframe not in ("M15", "H1"):
            return

        self._bars_cache.append(bar)
        if len(self._bars_cache) > 200:
            self._bars_cache.pop(0)

        if len(self._bars_cache) < 50:
            return

        # Feature extraction
        features = {}
        features.update(self.structural.extract_features(self._bars_cache))
        features.update(await self.macro.extract_features())
        features.update(await self.sentiment.extract_features())
        features.update(self._session_features())

        # Anomaly detection (runs BEFORE regime classifier)
        self.anomaly_detector.update(features)
        anomaly_score, should_abstain, flags = await self.anomaly_detector.score(features)

        if should_abstain:
            logger.info("Anomaly consensus: abstain (flags=%s score=%.3f)", flags, anomaly_score)
            return

        # Regime classification
        regime = await self.regime_monitor.update(features, anomaly_score)

        if regime.should_abstain:
            return

        # Strategy selection
        from mt5.account import get_balance
        balance = get_balance()
        signal = self.strategy_selector.select(regime, features, balance, anomaly_score)

        if signal is None:
            return

        # Pre-trade guards (idempotent state check)
        ok, reason = await self.guards.check_all(
            direction=signal.direction,
            lot=signal.lot_size,
            sl_pips=signal.sl_pips,
            account_balance=balance,
            anomaly_should_abstain=should_abstain,
            circuit_breaker_tripped=self.circuit_breaker.is_tripped(),
        )

        if not ok:
            logger.info("Guards blocked trade: %s", reason)
            return

        await self.executor.execute(signal, regime, anomaly_score)

    def on_tick(self, tick: dict):
        """Called by TickWatcherThread. Execution + circuit breaker only."""
        price = tick.get("bid", 0)
        spread = tick.get("spread", 0)

        # Spread circuit breaker
        self.circuit_breaker.update_spread_baseline(spread)
        trip = self.circuit_breaker.check_spread(spread)
        if trip:
            self._handle_circuit_breaker_trip(trip)
            return

        # Price circuit breaker
        trip = self.circuit_breaker.check_price_move(price)
        if trip:
            self._handle_circuit_breaker_trip(trip)

        # SL trailing for open positions
        for pos in self.executor.position_manager.get_all():
            needs_secondary_exit = self.executor.position_manager.update_pnl(pos.trade_id, price)
            if needs_secondary_exit:
                import asyncio
                asyncio.create_task(self.executor.close_trade(pos.trade_id, reason="secondary_exit"))

    def _handle_circuit_breaker_trip(self, trip):
        logger.critical("Circuit breaker: %s — halting trading", trip.reason)
        # Notify
        try:
            from notifications.telegram_notifier import send_alert
            send_alert(f"⚡ CIRCUIT BREAKER: {trip.reason}")
        except Exception:
            pass

    def emergency_stop(self):
        """Close all positions and halt."""
        import asyncio
        for pos in self.executor.position_manager.get_all():
            asyncio.create_task(self.executor.close_trade(pos.trade_id, reason="emergency_stop"))
        self.circuit_breaker._trip("Emergency stop")
        logger.critical("EMERGENCY STOP executed")

    def current_state(self) -> dict:
        return self.regime_monitor.current_state()

    def open_positions(self):
        return self.executor.position_manager.get_all()

    def _session_features(self) -> dict:
        from utils.time_utils import current_session
        session = current_session()
        return {
            "session_asian":   1.0 if session == "asian" else 0.0,
            "session_london":  1.0 if session == "london" else 0.0,
            "session_ny":      1.0 if session == "ny" else 0.0,
            "session_overlap": 1.0 if session == "overlap" else 0.0,
        }
