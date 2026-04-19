"""Shared pytest fixtures."""
import os
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Use test database URL by default so tests never touch production DB
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5433/xauusd_sniper_test",
)
os.environ.setdefault("PAPER_TRADING", "true")
os.environ.setdefault("MT5_LOGIN", "0")
os.environ.setdefault("MT5_PASSWORD", "test")
os.environ.setdefault("MT5_SERVER", "test")
os.environ.setdefault("FRED_API_KEY", "test")
os.environ.setdefault("NASDAQ_API_KEY", "test")
os.environ.setdefault("OANDA_API_KEY", "test")
