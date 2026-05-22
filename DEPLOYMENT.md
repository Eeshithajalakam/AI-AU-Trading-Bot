# Production Deployment Guide — AI AU Trading Bot

## Security warning

**Never commit MT5 passwords to Git.** Set credentials only in:
- Render/Railway environment variables
- Local `backend/.env` (gitignored)

If credentials were shared in chat, **rotate your MT5 demo password** in MetaQuotes.

---

## Architecture overview

| Component | Platform | Notes |
|-----------|----------|-------|
| Frontend | **Vercel** | Next.js 16, public dashboard URL |
| Backend API | **Render** | FastAPI + WebSocket (Linux) |
| PostgreSQL | **Render** or **Neon** | Persistent signals/trades |
| MT5 execution | **Windows VPS/local** | MetaTrader5 Python API is Windows-only |

**Important:** Render/Railway backends run **Linux** — they cannot run the native MT5 terminal. Options:

1. **Demo showcase (cloud):** `PAPER_TRADING_MODE=true` on Render — full UI, AI, DB, simulated fills.
2. **Real MT5 demo (Windows):** Run backend on a **Windows Server/VPS** with MT5 installed, or use a hybrid (cloud API + Windows execution worker).

---

## Step 1 — PostgreSQL

### Option A: Render PostgreSQL
1. Create PostgreSQL instance on Render.
2. Copy **Internal Database URL** (use `postgresql+asyncpg://` prefix if needed).

### Option B: Neon (free tier)
1. Create project at https://neon.tech
2. Connection string → set as `DATABASE_URL`

---

## Step 2 — Deploy backend (Render)

1. Push repo to GitHub: `https://github.com/Eeshithajalakam/AI-AU-Trading-Bot`
2. Render Dashboard → **New Web Service** → connect repo.
3. Settings:
   - **Root Directory:** `backend`
   - **Runtime:** Docker
   - **Health Check Path:** `/health`
4. Environment variables:

```env
ENVIRONMENT=production
SECRET_KEY=<generate-64-char-secret>
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
AUTO_TRAIN_ON_STARTUP=true
AUTO_TRADE_ENABLED=true
PAPER_TRADING_MODE=true
BACKEND_CORS_ORIGINS=["https://YOUR-APP.vercel.app"]
PUBLIC_FRONTEND_URL=https://YOUR-APP.vercel.app
MARKET_SYMBOL=GC=F
MAX_DAILY_LOSS_USD=300
MAX_OPEN_TRADES=2
TRADE_COOLDOWN_SECONDS=90
```

5. For **MT5 on Windows worker** (separate machine), add:
```env
PAPER_TRADING_MODE=false
MT5_LOGIN=<your_login>
MT5_PASSWORD=<your_password>
MT5_SERVER=MetaQuotes-Demo
```

6. Deploy → note public URL: `https://ai-au-trading-api.onrender.com` (example)

7. Verify:
   - `GET https://YOUR-API.onrender.com/health`
   - `GET https://YOUR-API.onrender.com/docs`

**WebSocket URL:** `wss://YOUR-API.onrender.com/ws/trading`

---

## Step 3 — Deploy frontend (Vercel)

1. https://vercel.com → Import Git repository.
2. Framework: **Next.js** (root directory `.`)
3. Environment variables:

```env
NEXT_PUBLIC_API_URL=https://YOUR-API.onrender.com
NEXT_PUBLIC_WS_URL=wss://YOUR-API.onrender.com
```

4. Deploy → public URL: `https://ai-au-trading-bot.vercel.app` (example)

5. Update Render `BACKEND_CORS_ORIGINS` and `PUBLIC_FRONTEND_URL` with the Vercel URL.

---

## Step 4 — Docker (full stack local/VPS)

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- API: http://localhost:8000
- Postgres: localhost:5432

---

## Step 5 — MT5 demo auto-trading (Windows)

1. Install **MetaTrader 5** and log into demo account.
2. Enable **Algo Trading** in MT5 toolbar.
3. `backend/.env`:

```env
AUTO_TRADE_ENABLED=true
PAPER_TRADING_MODE=false
MT5_LOGIN=your_login
MT5_PASSWORD=your_password
MT5_SERVER=MetaQuotes-Demo
```

4. Run backend on Windows:
```powershell
cd backend
py -3.11 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

5. Confirm: `GET http://localhost:8000/api/mt5/status` → `connected: true`

---

## Public URLs checklist

After deployment, record:

| Item | URL |
|------|-----|
| Public web app | `https://_____.vercel.app` |
| Public API | `https://_____.onrender.com` |
| WebSocket | `wss://_____.onrender.com/ws/trading` |
| API docs | `https://_____.onrender.com/docs` |

---

## Forward-testing before live money

| Phase | Duration | Mode |
|-------|----------|------|
| Paper on cloud | 2–4 weeks | `PAPER_TRADING_MODE=true` |
| MT5 demo Windows | 4–8 weeks | Demo account, real execution |
| Live micro-lot | 4+ weeks | Smallest size, strict limits |
| Scale | After metrics stable | Increase size gradually |

**Minimum metrics before live:** Sharpe > 1.0, max DD < 8%, win rate stable, 200+ demo trades.

---

## Remaining gaps for real-money trading

- Colocated/low-latency execution
- Broker-specific filling modes and symbol specs
- Regulatory compliance and audit trails
- Separate execution and research environments
- Hardware security module / vault for credentials
- Independent risk officer review
