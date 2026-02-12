# Options Day-Trading Assistant (Robust Edition)

An enterprise-grade, robust trading assistant for identifying high-probability options trades. Now featuring a web dashboard, portfolio risk management, and rigorous data validation.

## ⚠️ Important Disclaimers

!!! warning "Disclaimer"
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

For detailed instructions, see the [Installation Guide](guide/installation.md).

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API
Copy `.env.example` to `.env` and add your keys.

### 3. Launch Dashboard
```bash
run_dashboard.bat
```
(Or `streamlit run src/ui/dashboard.py` on Mac/Linux)

## 📊 Workflow

1.  **Scan**: `MarketScanner` finds stocks passing RSI/ATR/Volume filters.
2.  **Filter**: `OptionsFilter` finds liquid options contracts.
3.  **Analyze**: `GreeksCalculator` computes real Delta/Theta.
4.  **Validate**: `DataValidator` ensures data is fresh and valid.
5.  **Risk Check**: `PortfolioManager` ensures new trade doesn't exceed portfolio limits.
6.  **Store**: Trade is saved to `trades.db` (SQLite).
7.  **Visualize**: Trade appears on the Dashboard.

## 📂 Data & Persistence

- **Database**: All trades are saved to `outputs/trades.db`.
- **Artifacts**: Alerts and Watchlists are still generated in `outputs/`.

## 🧪 Verification

To ensure the system is healthy:
```bash
python verify_health.py
```

## ☁️ Production Deployment (Fly.io)

For deployment instructions, see the [Deployment Guide](guide/deployment.md).
