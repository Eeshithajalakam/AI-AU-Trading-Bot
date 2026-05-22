# AI AU Trading Bot

Production-oriented AI XAU/USD (Gold) trading platform: LSTM predictions, PostgreSQL persistence, MT5 integration (with paper mode), live WebSockets, and backtesting.

## Features

- **LSTM training** — GC=F historical data, train/val split, MAE / RMSE / directional accuracy
- **Auto-train on startup** — trains if `backend/models/xau_lstm.pt` is missing
- **PostgreSQL** — signals, trades, backtests, settings, analytics, training jobs (Alembic migrations)
- **MT5 + paper trading** — real execution on Windows; paper mode everywhere else
- **Safeguards** — spread filter, cooldown, max open trades, daily loss cap, emergency shutdown
- **Live WebSocket** — candles, signals, training progress, risk metrics, trade updates

## Quick Start (Local)

### 1. PostgreSQL

```bash
docker compose up db -d
# Or use local Postgres on port 5432
```

### 2. Backend (Python 3.11)

```bash
cd backend
copy .env.example .env
py -3.11 -m pip install -r requirements.txt
py -3.11 -m alembic upgrade head
py -3.11 -m uvicorn main:app --reload --port 8000
```

Training runs automatically on first start if no model exists (`AUTO_TRAIN_ON_STARTUP=true`).

Manual training:

```bash
py -3.11 scripts/train_model.py
# POST http://localhost:8000/api/training/train?epochs=30
```

### 3. Frontend

```bash
npm install
copy .env.example .env.local
npm run dev
```

Open http://localhost:3000

### Full stack with Docker

```bash
docker compose up --build
```

## Environment (backend/.env)

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL async URL |
| `AUTO_TRAIN_ON_STARTUP` | Train LSTM if no model file |
| `AUTO_TRADE_ENABLED` | Execute signals via MT5/paper |
| `PAPER_TRADING_MODE` | `true` = simulated fills (default) |
| `MT5_LOGIN` / `MT5_PASSWORD` / `MT5_SERVER` | Broker credentials |
| `MAX_SPREAD_POINTS` | Reject trades if spread too wide |
| `TRADE_COOLDOWN_SECONDS` | Min seconds between trades |
| `MAX_OPEN_TRADES` | Position cap |

## API Highlights

| Endpoint | Description |
|----------|-------------|
| `GET /health` | DB, model, market status |
| `WS /ws/trading` | Live stream (ping every 25s) |
| `POST /api/training/train` | Background LSTM training |
| `GET /api/training/status` | Progress + validation metrics |
| `GET /api/mt5/account` | Balance, positions, paper flag |
| `POST /api/mt5/close-position` | Close by ticket |
| `GET /api/trades/history` | DB-backed trade journal |
| `GET /api/trades/pnl` | Daily P&L |
| `GET /api/backtest/history` | Saved backtest runs |

## MT5 Notes

- Install MetaTrader5 terminal on **Windows** for live execution.
- Linux/Docker: use `PAPER_TRADING_MODE=true` (default).
- Set `AUTO_TRADE_ENABLED=true` only when credentials and risk limits are configured.

## Project Structure

```
backend/
  ai/           # LSTM, indicators, signals, trainer
  api/          # FastAPI routers
  db/           # SQLAlchemy models + repositories
  alembic/      # Migrations
  trading/      # MT5, risk, execution
  services/     # Market data, training runner
src/            # Next.js dashboard
```
