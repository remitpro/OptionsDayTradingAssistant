# Options Day-Trading Assistant (Robust Edition)

An enterprise-grade, robust trading assistant for identifying high-probability options trades. Now featuring a web dashboard, portfolio risk management, and rigorous data validation.

## ⚠️ Important Disclaimers

**This is a decision-support tool, NOT financial advice.**

- All trades carry risk of loss.
- This system does NOT execute trades automatically.
- Requires manual review and execution in ThinkorSwim.
- **Paper trade first** before using with real money.

## 🚀 Key Features

### 🛡️ Robust Foundation
- **Circuit Breakers**: Protects against API failures.
- **Strict Validation**: All data is validated using Pydantic models.
- **Stale Data Protection**: Rejects market data older than 60 seconds.
- **Health Monitoring**: Self-checks disk, DB, and API connectivity.

### 🧠 Advanced Analytics
- **Real-Time Greeks**: Calculated using `py_vollib` (Black-Scholes).
- **Portfolio Risk Manager**: Aggregates risk (Delta, Theta) across all positions.
- **Technical Indicators**: RSI, MACD, Bollinger Bands, ATR.
- **Anomaly Detection**: Filters out "bad ticks" and flash crashes.

### 🖥️ Modern Dashboard
- **Web UI**: Built with Streamlit for real-time monitoring.
- **Trade Journal**: Searchable database of all historical trades.
- **Live Scanner**: Real-time view of potential opportunities.

## 📋 Requirements

- Python 3.11+
- TD Ameritrade Developer Account (or Schwab API access)
- `streamlit`, `pandas`, `sqlalchemy`, `tenacity`, `py_vollib`

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API
Copy `.env.example` to `.env` and add your keys:
```
TDA_API_KEY=your_api_key_here
TDA_REDIRECT_URI=http://localhost
```

### 3. Launch Dashboard
This is the new primary interface.
```bash
run_dashboard.bat
```
(Or `streamlit run src/ui/dashboard.py` on Mac/Linux)

### 4. Run Scanner Logic (Headless)
To just run the scanner engine and save to DB:
```bash
python main.py
```

## 📊 Workflow

1.  **Scan**: `MarketScanner` finds stocks passing RSI/ATR/Volume filters.
2.  **Filter**: `OptionsFilter` finds liquid options contracts.
3.  **Analyze**: `GreeksCalculator` computes real Delta/Theta.
4.  **Validate**: `DataValidator` ensures data is fresh and valid.
5.  **Risk Check**: `PortfolioManager` ensures new trade doesn't exceed portfolio limits.
6.  **Store**: Trade is saved to `trades.db` (SQLite).
7.  **Visualize**: Trade appears on the Dashboard.

## ☁️ Production Deployment (Fly.io)

The application is configured for deployment on Fly.io as a single-container application running both the scanner loop and the Streamlit dashboard.

### 1. Prerequisites
- [flyctl](https://fly.io/docs/hands-on/install-flyctl/) installed
- A valid `token.json` generated locally via `tda-api` authentication flow

### 2. Initial Setup
```bash
# Initialize the app (if not already done)
fly launch --no-deploy
```

### 3. Configure Persistence
Create a persistent volume to store the TDA token and trade database:
```bash
fly volumes create options_data --region iad --size 1
```

### 4. Set Secrets
```bash
fly secrets set \
    TDA_API_KEY=your_api_key_here \
    DATABASE_URL="sqlite:////data/trades.db"
```

### 5. Deploy
```bash
fly deploy
```

### 6. Upload Token (CRITICAL)
The TDA API requires a valid token file to refresh the session. Since the container filesystem is ephemeral, you **MUST** upload your local `token.json` to the persistent volume.

```bash
# Open an SFTP shell to the running VM
fly sftp shell

# Inside sftp shell:
put config/token.json /data/token.json
```

Once uploaded, the app will automatically pick up the token from `/data/token.json` (configured via `fly.toml` environment variables).

## 📂 Data & Persistence

- **Database**: By default, trades are saved to a SQLite database. In production, this is located on the persistent volume at `/data/trades.db`.
- **Output Files**: Generated alerts and watchlists are saved to `/data/outputs/` (mapped via `OUTPUT_DIR` environment variable).
- **Logs**: Logs are stored in `/data/logs/`.

## 🧪 Verification

To ensure the system is healthy:
```bash
python verify_health.py
```

To verify analytics calculation:
```bash
python verify_analytics.py
```

## 🤝 Contributing
Personal project. Use issues for bugs.

## ⚠️ Known Issues
- Requires valid `token.json` manually uploaded to the persistent volume.
- Historical backtests currently use simulated logic until a historical data feed is connected.
