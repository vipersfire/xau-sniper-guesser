"""MT5 adapter — isolated connection and order management."""
import logging
from config.settings import settings
from config.constants import SYMBOL

logger = logging.getLogger(__name__)


class MT5Adapter:
    def __init__(self):
        self._connected = False

    def connect(self) -> bool:
        try:
            import MetaTrader5 as mt5
            path = settings.mt5_path or None
            if not mt5.initialize(path=path):
                logger.error("MT5 initialize failed: %s", mt5.last_error())
                return False
            if settings.mt5_login:
                authorized = mt5.login(
                    login=settings.mt5_login,
                    password=settings.mt5_password,
                    server=settings.mt5_server,
                )
                if not authorized:
                    logger.error("MT5 login failed: %s", mt5.last_error())
                    mt5.shutdown()
                    return False
            self._connected = True
            logger.info("MT5 connected: %s", mt5.account_info())
            return True
        except ImportError:
            logger.error("MetaTrader5 package not installed")
            return False
        except Exception as e:
            logger.error("MT5 connect error: %s", e)
            return False

    def disconnect(self):
        try:
            import MetaTrader5 as mt5
            mt5.shutdown()
        except Exception:
            pass
        self._connected = False

    def is_connected(self) -> bool:
        try:
            import MetaTrader5 as mt5
            return mt5.terminal_info() is not None
        except Exception:
            return False

    def account_info(self) -> dict:
        try:
            import MetaTrader5 as mt5
            info = mt5.account_info()
            if info:
                return info._asdict()
        except Exception:
            pass
        return {}

    def get_ohlcv(self, symbol: str, timeframe: str, bars: int = 1000) -> list[dict]:
        try:
            import MetaTrader5 as mt5
            tf_map = {
                "M1": mt5.TIMEFRAME_M1, "M5": mt5.TIMEFRAME_M5,
                "M15": mt5.TIMEFRAME_M15, "M30": mt5.TIMEFRAME_M30,
                "H1": mt5.TIMEFRAME_H1, "H4": mt5.TIMEFRAME_H4,
                "D1": mt5.TIMEFRAME_D1,
            }
            tf = tf_map.get(timeframe, mt5.TIMEFRAME_H1)
            rates = mt5.copy_rates_from_pos(symbol, tf, 0, bars)
            if rates is None:
                return []
            return [
                {
                    "time": int(r[0]),
                    "open": float(r[1]),
                    "high": float(r[2]),
                    "low": float(r[3]),
                    "close": float(r[4]),
                    "tick_volume": int(r[5]),
                    "spread": int(r[6]),
                }
                for r in rates
            ]
        except Exception as e:
            logger.error("get_ohlcv failed: %s", e)
            return []

    def get_tick(self, symbol: str) -> dict | None:
        try:
            import MetaTrader5 as mt5
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                return {
                    "bid": tick.bid,
                    "ask": tick.ask,
                    "spread": round((tick.ask - tick.bid) * 100, 2),
                    "time": tick.time,
                }
        except Exception as e:
            logger.error("get_tick failed: %s", e)
        return None

    def place_order(
        self,
        symbol: str,
        direction: str,
        lot: float,
        sl_price: float,
        tp_price: float,
        comment: str = "xau-sniper",
    ) -> dict | None:
        if settings.paper_trading:
            logger.info("[PAPER] Would place %s %s %.2f lots SL=%.2f TP=%.2f", direction, symbol, lot, sl_price, tp_price)
            return {"ticket": -1, "paper": True}
        try:
            import MetaTrader5 as mt5
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                logger.error("No tick data for %s", symbol)
                return None
            price = tick.ask if direction == "buy" else tick.bid
            order_type = mt5.ORDER_TYPE_BUY if direction == "buy" else mt5.ORDER_TYPE_SELL
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot,
                "type": order_type,
                "price": price,
                "sl": sl_price,
                "tp": tp_price,
                "deviation": 10,
                "magic": 20260000,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error("Order failed: %s", result)
                return None
            return {"ticket": result.order, "price": result.price}
        except Exception as e:
            logger.error("place_order error: %s", e)
            return None

    def close_position(self, ticket: int) -> bool:
        if settings.paper_trading:
            logger.info("[PAPER] Would close ticket %d", ticket)
            return True
        try:
            import MetaTrader5 as mt5
            position = mt5.positions_get(ticket=ticket)
            if not position:
                return False
            pos = position[0]
            direction = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
            tick = mt5.symbol_info_tick(pos.symbol)
            price = tick.bid if direction == mt5.ORDER_TYPE_SELL else tick.ask
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": direction,
                "position": ticket,
                "price": price,
                "deviation": 20,
                "magic": 20260000,
                "comment": "xau-sniper close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            result = mt5.order_send(request)
            return result.retcode == mt5.TRADE_RETCODE_DONE
        except Exception as e:
            logger.error("close_position error: %s", e)
            return False

    def get_open_positions(self, symbol: str | None = None) -> list[dict]:
        try:
            import MetaTrader5 as mt5
            positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
            if not positions:
                return []
            return [p._asdict() for p in positions]
        except Exception:
            return []
