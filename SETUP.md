# XAUUSD Sniper — Setup Guide

## Prerequisites

- Python 3.11+
- PostgreSQL 14+
- MetaTrader 5 terminal (Windows or Wine on Linux)
- MIFX Ultra Low account

## 1. Python Environment

```bash
# Using uv (recommended)
pip install uv
uv venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

uv pip install -r requirements.txt

# Or standard pip
pip install -r requirements.txt
```

## 2. PostgreSQL

```bash
# Create database
createdb xauusd_sniper

# Set DATABASE_URL in .env
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/xauusd_sniper
```

## 3. Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and fill in:
- `MT5_LOGIN`, `MT5_PASSWORD`, `MT5_SERVER` — your MIFX account
- `FRED_API_KEY` — from fred.stlouisfed.org (free)
- `NASDAQ_API_KEY` — from data.nasdaq.com (free tier)
- `OANDA_API_KEY` + `OANDA_ACCOUNT_ID` — from OANDA practice account
- `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` — optional, for alerts

## 4. Initialize Database

```bash
python scripts/init_db.py
```

## 5. MT5 Setup

1. Open MetaTrader 5
2. Log in to your MIFX Ultra Low account
3. Enable AutoTrading (toolbar button)
4. Run connection test: `python scripts/test_mt5.py`

## 6. Initial Data Load

```bash
# Load all historical data (takes 10–30 min depending on connection)
python -m cli.main ingest --source all

# Or run individual sources:
python -m cli.main ingest --source fred
python -m cli.main ingest --source cot
python -m cli.main ingest --source mt5_ohlcv
```

## 7. Train the Model

```bash
python -m cli.main backtest --train
```

## 8. Preflight Check

```bash
python -m cli.main preflight
```

All checks must pass before the trading engine will start.

## 9. Start Trading Terminal

```bash
python -m cli.main run
```

## Production VPS Deployment

Recommended: Singapore or Hong Kong VPS (10–30ms to MIFX servers)

```bash
# Start in tmux session
tmux new -s xau-sniper
python -m cli.main run

# Detach: Ctrl+B, D
# Reattach: tmux attach -t xau-sniper
```

## OTA Updates

To update strategy parameters without restarting:

```bash
# Edit config/strategy_params.json
# Save the file — OTAWatcher detects the change and hot-swaps automatically
```

## Paper Trading

Set `PAPER_TRADING=true` in `.env` (default).
All orders are logged but NOT sent to MT5.
Set `PAPER_TRADING=false` only after live testing.
