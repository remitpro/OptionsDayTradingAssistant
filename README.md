# Options Day-Trading Assistant

A personal trading tool for identifying high-probability options trades with integrated ThinkorSwim workflow support.

## ⚠️ Important Disclaimers

**This is a decision-support tool, NOT financial advice.**

- All trades carry risk of loss
- This system does NOT execute trades automatically
- Requires manual review and execution in ThinkorSwim
- **Paper trade first** before using with real money
- Past performance does not guarantee future results

## 🎯 Features

- **Market Scanner**: Filters stocks by price, volume, ATR, spread, and VWAP
- **Options Liquidity Filter**: Identifies tradable options with sufficient liquidity
- **Strategy Selection**: Automatically selects optimal strategy based on market conditions
- **Probability Analysis**: Black-Scholes + Monte Carlo simulations
- **Risk Metrics**: Max loss/gain, R/R ratio, break-even points, expected value
- **Trade Scoring**: Weighted scoring (0-100) based on probability, R/R, IV edge, liquidity, trend
- **ThinkorSwim Integration**: ThinkScript alerts and watchlist generation

## 📋 Requirements

### API Access

You need a TD Ameritrade developer account:

1. Go to https://developer.tdameritrade.com/
2. Create a developer account
3. Register an application
4. Get your API key

**Note**: TD Ameritrade is migrating to Schwab. Verify current API availability.

### Python

- Python 3.11 or higher
- See `requirements.txt` for dependencies

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API

Copy the example environment file:

```bash
copy .env.example .env
```

Edit `.env` and add your TD Ameritrade API key:

```
TDA_API_KEY=your_api_key_here
```

### 3. Authenticate

Run the TD Ameritrade authentication (first time only):

```python
from tda import auth

# Follow the prompts to authenticate
# This will create a token file in config/token.json
```

### 4. Run the Scanner

```bash
python main.py
```

## 📊 How It Works

### Pipeline Flow

```
1. Market Scanner
   ↓ Filters stocks by price, volume, ATR, spread, VWAP
   
2. Options Filter
   ↓ Filters options by DTE, OI, volume, spread, Greeks
   
3. Strategy Selection
   ↓ Detects market condition and selects optimal strategy
   
4. Probability & Risk Analysis
   ↓ Calculates probabilities, Greeks, risk metrics
   
5. Trade Scoring
   ↓ Scores trades 0-100 based on multiple factors
   
6. Output Generation
   ↓ Top 3-5 trades + ThinkScript alerts + Watchlists
```

### Strategy Selection Logic

| Market Condition | Strategy | Criteria |
|-----------------|----------|----------|
| Strong Momentum | Long Call/Put | Price trend + volume spike + ATR expansion |
| Breakout + Low IV | Debit Spread | IV < 30%, near support/resistance |
| High IV + Range | Credit Spread | IV > 60%, range-bound price action |
| Choppy Market | Iron Condor | Low directional movement, 0-2 DTE |
| News/IV Spike | Skip | IV > 100%, too risky |

### Scoring Formula

```
Score = 0.30 × Probability of Profit
      + 0.25 × Risk/Reward Ratio
      + 0.20 × IV Edge
      + 0.15 × Liquidity Score
      + 0.10 × Trend Alignment
```

Only trades with **Score ≥ 70** are output.

## 📁 Output Files

After each scan, the system generates:

### 1. Trade JSON
`outputs/trades/trades_YYYY-MM-DD.json`
- Complete trade data with all metrics

### 2. ThinkScript Alerts
`outputs/alerts/alert_SYMBOL_YYYYMMDD.txt`
- Entry, stop loss, and take profit alerts
- Copy/paste into ThinkorSwim charts

### 3. Watchlists
`outputs/watchlists/watchlist_YYYYMMDD.csv`
- Import into ThinkorSwim
- Basic and detailed versions available

## 🔧 Configuration

Edit `.env` to customize:

### Scanner Parameters
```
MIN_STOCK_PRICE=20
MAX_STOCK_PRICE=300
MIN_AVG_VOLUME=1000000
VOLUME_MULTIPLIER=1.3
MIN_ATR=1.5
MAX_STOCK_SPREAD_PCT=0.2
```

### Options Filters
```
MIN_DTE=0
MAX_DTE=7
MIN_OPEN_INTEREST=1000
MIN_OPTION_VOLUME=300
MAX_OPTION_SPREAD_PCT=5.0
```

### Scoring Weights
```
WEIGHT_PROBABILITY=0.30
WEIGHT_RISK_REWARD=0.25
WEIGHT_IV_EDGE=0.20
WEIGHT_LIQUIDITY=0.15
WEIGHT_TREND=0.10
```

### Output Settings
```
MIN_TRADE_SCORE=70
MAX_TRADES_OUTPUT=5
```

## 📖 Usage Examples

### Basic Scan
```bash
python main.py
```

### Custom Symbol List
```python
from main import TradingSystem

system = TradingSystem()
symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
system.run(symbols)
```

## 🔌 ThinkorSwim Integration

### Import Watchlist

1. Open ThinkorSwim
2. Go to **Setup → Open Shared Item → Import**
3. Select the generated watchlist CSV
4. Choose "Watchlist" as item type
5. Click "Import"

### Add ThinkScript Alerts

1. Open a chart for the symbol
2. Go to **Studies → Edit Studies → New**
3. Copy/paste the ThinkScript code from alert file
4. Click **OK**
5. Alerts will trigger based on price levels

## 🧪 Testing

Run unit tests:

```bash
pytest tests/ -v
```

Run with coverage:

```bash
pytest tests/ --cov=src --cov-report=html
```

## 📂 Project Structure

```
tosOptionTerminal/
├── config/                 # Configuration management
├── src/
│   ├── scanner/           # Market and options scanning
│   ├── strategies/        # Strategy selection engine
│   ├── analytics/         # Probability, Greeks, risk metrics
│   ├── scoring/           # Trade scoring algorithm
│   ├── integration/       # ThinkorSwim integration
│   ├── data/              # API client and caching
│   └── utils/             # Logging and validation
├── outputs/               # Generated outputs
│   ├── trades/           # Trade JSON files
│   ├── alerts/           # ThinkScript alerts
│   └── watchlists/       # TOS watchlists
├── logs/                  # System logs
├── tests/                 # Unit tests
├── main.py               # Entry point
├── requirements.txt      # Dependencies
└── README.md            # This file
```

## ⚙️ Advanced Configuration

### Custom Filters

Edit `src/scanner/market_scanner.py` to add custom filters:

```python
def custom_filter(self, quote):
    # Add your logic here
    return True  # or False
```

### Custom Strategies

Add new strategies in `src/strategies/strategy_configs.py`:

```python
MarketCondition.CUSTOM: StrategyConfig(
    strategy_type=StrategyType.CUSTOM,
    delta_target=0.50,
    spread_width=5,
    max_dte=7,
    description="Your custom strategy"
)
```

## 🐛 Troubleshooting

### API Authentication Errors

```
Error: TDA client not initialized
```

**Solution**: Run authentication flow to generate token file.

### No Candidates Found

```
No candidates found. Try adjusting filters...
```

**Solutions**:
- Lower `MIN_TRADE_SCORE` in `.env`
- Expand price range (`MIN_STOCK_PRICE`, `MAX_STOCK_PRICE`)
- Reduce `MIN_AVG_VOLUME`
- Scan during market hours for real-time data

### Market Closed Warning

```
Market is currently closed
```

**Note**: System will use cached data. For best results, run during market hours (9:30 AM - 4:00 PM ET).

## 📊 Performance Tips

1. **Cache Management**: Clear expired cache periodically
   ```python
   from src.data import get_cache
   cache = get_cache()
   cache.clear_expired()
   ```

2. **Scan Smaller Universe**: Start with 20-30 liquid symbols

3. **Adjust DTE Range**: Shorter DTE (0-3) for faster scans

## 🔒 Security

- Never commit `.env` file or `config/token.json`
- Keep API credentials secure
- Use environment variables for sensitive data

## 📝 License

This is personal trading software. Use at your own risk.

## 🤝 Contributing

This is a personal tool, but suggestions are welcome via issues.

## 📞 Support

For TD Ameritrade API issues:
- https://developer.tdameritrade.com/

For ThinkorSwim help:
- https://www.tdameritrade.com/tools-and-platforms/thinkorswim.html

---

**Remember**: This tool provides analysis, not guarantees. Always do your own research and manage risk appropriately.
