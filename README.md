# XAUUSD Sniper

A deterministic, evidence-backed XAUUSD trading system for MIFX (MetaTrader 5).

## Core Architecture

```
Data Ingestion → Feature Engineering → Anomaly Detection → Regime Classifier → Strategy Selector → MT5 Execution
```

**Key principles:**
- No AI/LLM in the runtime critical path
- Abstain over guess — if confidence < threshold, no trade
- Every parameter justified by historical statistics
- Deterministic: same input always produces same output

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys and MT5 credentials

# 3. Initialize database
python scripts/init_db.py

# 4. Ingest historical data
python -m cli.main ingest --source all

# 5. Run backtest and train model
python -m cli.main backtest --train

# 6. Run preflight checks
python -m cli.main preflight

# 7. Start interactive terminal
python -m cli.main run
```

## Project Structure

```
cli/          Interactive terminal (Typer + Rich)
engine/       Trading domain (regime, strategy, execution)
ingestion/    Data ingestion (FRED, COT, OANDA, ForexFactory, MT5)
backtest/     Walk-forward backtesting + metrics
models/       XGBoost regime classifier + drift monitoring
anomaly/      3-detector consensus anomaly system
ota/          Hot-reload strategy params and rules
data/         SQLAlchemy ORM + async repositories
threads/      Background thread management
mt5/          MetaTrader 5 adapter (isolated)
config/       Pydantic settings + OTA-reloadable params
utils/        Math, time, hashing, data quality utilities
```

## Broker

- **Broker:** MIFX (Monex Investindo Futures)
- **Account:** Ultra Low (ECN-style spreads)
- **Platform:** MetaTrader 5
- **Regulation:** BAPPEBTI

See `SETUP.md` for full setup walkthrough.
