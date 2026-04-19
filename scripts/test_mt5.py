#!/usr/bin/env python3
"""MT5 connection test script."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main():
    from mt5.adapter import MT5Adapter
    from config.constants import SYMBOL

    print("Testing MT5 connection...")
    adapter = MT5Adapter()
    if not adapter.connect():
        print("FAILED: Could not connect to MT5")
        sys.exit(1)

    info = adapter.account_info()
    print(f"Connected: {info.get('company')} | account {info.get('login')}")
    print(f"Balance: {info.get('balance'):.2f} {info.get('currency')}")

    tick = adapter.get_tick(SYMBOL)
    if tick:
        print(f"Tick: bid={tick['bid']:.2f} ask={tick['ask']:.2f} spread={tick['spread']:.1f}")
    else:
        print("WARNING: No tick data")

    bars = adapter.get_ohlcv(SYMBOL, "H1", 10)
    print(f"OHLCV H1: got {len(bars)} bars")

    adapter.disconnect()
    print("MT5 test passed.")


if __name__ == "__main__":
    main()
