# 🌟 Halol Crypto AI

**A production-ready Telegram Bot + Mini App for halal spot crypto investing.**

> ☪️ Halal only — Spot trading · No futures · No leverage · No short selling

---

## ✨ Features

| Feature | Details |
|---|---|
| 📈 **Signal Engine** | 0–100 score from 8+ indicators + Smart Money Concepts |
| 🏦 **SMC Analysis** | Order Blocks, FVG, BOS, CHoCH, Liquidity Sweep |
| 📋 **Trade Plans** | Entry, Stop Loss, TP1/TP2/TP3, Risk/Reward |
| ⭐ **Watchlist** | Save coins, receive Strong Buy alerts |
| 🎓 **Academy** | 20+ offline lessons — no AI API needed |
| 📊 **Market Overview** | Prices, trends, top movers |
| 🚀 **Mini App** | Full responsive dashboard in Telegram |
| 🔔 **Alerts** | Background scanner sends notifications |

---

## 🚀 Quick Start (Local)

### 1. Clone & Install

```bash
git clone https://github.com/your-username/halol-crypto-ai.git
cd halol-crypto-ai
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and set your BOT_TOKEN
```

### 3. Get a Bot Token

1. Open Telegram → search `@BotFather`
2. Send `/newbot`
3. Follow instructions to get your token
4. Paste into `.env` as `BOT_TOKEN`

### 4. Run

```bash
python main.py
```

Your bot is now running in polling mode. Send `/start` to your bot.

---

## 🐳 Docker (Recommended)

```bash
cp .env.example .env
# Edit .env with your BOT_TOKEN

docker-compose up -d
```

Access logs:
```bash
docker-compose logs -f halol
```

---

## 🚂 Railway Deployment

Railway gives you a free public HTTPS URL — perfect for webhook mode.

### Steps

1. Push code to GitHub
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub**
3. Select your repository
4. Add environment variables:
   ```
   BOT_TOKEN=your_token
   WEBAPP_URL=https://your-app.up.railway.app
   WEBHOOK_URL=https://your-app.up.railway.app
   ```
5. Railway auto-detects `railway.toml` and deploys

### After Deploy

The bot starts in webhook mode automatically. Visit `https://your-app.up.railway.app` to see the Mini App.

---

## 🎨 Render Deployment

1. Push code to GitHub
2. Go to [render.com](https://render.com) → **New** → **Web Service**
3. Connect your GitHub repo
4. Render detects `render.yaml` automatically
5. Set environment variables in the Render dashboard:
   ```
   BOT_TOKEN=your_token
   WEBAPP_URL=https://your-app.onrender.com
   WEBHOOK_URL=https://your-app.onrender.com
   ```
6. Click **Deploy**

> ⚠️ Render free tier spins down after inactivity. Use Railway or a VPS for always-on operation.

---

## 🖥️ VPS Deployment (Ubuntu)

```bash
# Install Python 3.11
sudo apt update && sudo apt install python3.11 python3.11-pip -y

# Clone repo
git clone https://github.com/your-username/halol-crypto-ai.git
cd halol-crypto-ai
pip3.11 install -r requirements.txt

# Configure
cp .env.example .env
nano .env   # Set BOT_TOKEN, WEBAPP_URL, WEBHOOK_URL

# Run with systemd (auto-restart)
sudo nano /etc/systemd/system/halol.service
```

Paste:
```ini
[Unit]
Description=Halol Crypto AI
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/halol-crypto-ai
ExecStart=/usr/bin/python3.11 main.py --webhook
Restart=always
RestartSec=10
EnvironmentFile=/home/ubuntu/halol-crypto-ai/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable halol
sudo systemctl start halol
sudo systemctl status halol
```

---

## 📱 Setting Up the Telegram Mini App

Once your bot and web server are running with a public HTTPS URL:

1. Open `@BotFather` on Telegram
2. Send `/newapp`
3. Select your bot
4. Set the Web App URL to your WEBAPP_URL
5. Done! The "🚀 Open Dashboard" button will appear in `/start`

---

## 📁 Project Structure

```
halol-crypto-ai/
├── main.py              # Entry point — runs bot + web server
├── bot.py               # Telegram bot handlers & UI
├── scanner.py           # Market data fetcher (Binance + CoinGecko)
├── signals.py           # Signal scoring engine
├── indicators.py        # Technical indicators (EMA, RSI, MACD, etc.)
├── smc.py               # Smart Money Concepts detection
├── education.py         # Offline lesson content
├── database.py          # SQLite/PostgreSQL data layer
├── utils.py             # Formatters & keyboard builders
├── webapp_server.py     # aiohttp web server for Mini App
├── config.py            # All configuration
├── webapp/
│   └── index.html       # Telegram Mini App (single file)
├── data/                # SQLite database (auto-created)
├── logs/                # Log files (auto-created)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── railway.toml
├── render.yaml
└── .env.example
```

---

## 🤖 Bot Commands

| Command | Description |
|---|---|
| `/start` | Open main menu |
| `/home`  | Return to home |

Everything else is button-driven — no typing required.

---

## 📊 Signal Engine

The signal score (0–100) is calculated from:

| Component | Weight | Details |
|---|---|---|
| EMA Alignment | 35 pts | Price vs EMA20/50/200 |
| RSI | 15 pts | Optimal zone 40–65 |
| MACD | 20 pts | Crossover + histogram |
| Bollinger Bands | 10 pts | %B position |
| ADX/Trend | 10 pts | Trend strength |
| Volume | 10 pts | Relative volume |
| Smart Money | 25 pts | OB, FVG, BOS, CHoCH |

**Signal Types:**
- 🟢 **Strong Buy** — Score ≥ 75
- 🟢 **Buy** — Score ≥ 55
- 🟡 **Wait** — Score ≥ 40
- 💰 **Profit Taking Zone** — Score < 40

> ⚠️ No Sell / Short / Leverage signals — ever.

---

## 🏦 Smart Money Concepts

| Concept | Detection Method |
|---|---|
| Order Block | Last opposing candle before impulsive move |
| Fair Value Gap | Price imbalance between candle wicks |
| Break of Structure | Close beyond previous swing high/low |
| Change of Character | First reversal signal against trend |
| Liquidity Sweep | Wick beyond key level, close back inside |
| Breakout Retest | Resistance broken → returns to test as support |
| Premium/Discount | Equilibrium of 50-candle range |

---

## 🌐 API Sources

All free, no API keys required:

- **Binance** — OHLCV candles, 24h ticker (public endpoints)
- **CoinGecko** — Market overview, sentiment (free tier)

---

## ☪️ Halal Compliance

This system enforces halal investing by design:

- ✅ Spot analysis only
- ✅ Buy signals only (Strong Buy, Buy, Wait, Profit Taking)
- ✅ No futures, derivatives, or perpetuals
- ✅ No leverage or margin
- ✅ No short selling
- ✅ No interest-bearing products

---

## 📜 Disclaimer

Halol Crypto AI is an **educational and analytical tool**. It does not provide financial advice. Always consult a qualified Islamic scholar for personal halal rulings and a licensed financial advisor for investment decisions. Never invest more than you can afford to lose.

---

## 🤝 Contributing

Pull requests welcome! Please ensure all contributions maintain the halal-only principle.

---

*Built with ❤️ for the Muslim investing community*
