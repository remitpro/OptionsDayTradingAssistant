# Code Structure

The project is structured as follows:

```
OptionsDayTradingAssistant/
├── config/                 # Configuration files
│   ├── settings.py         # Application settings (Pydantic models)
│   └── token.json          # TDA Authentication token (ignored)
├── docs/                   # Documentation (MkDocs)
├── logs/                   # System logs
├── outputs/                # Generated artifacts
│   ├── alerts/             # ThinkScript alerts
│   ├── trades/             # JSON trade snapshots
│   └── watchlists/         # CSV watchlists
├── src/                    # Source code
│   ├── analytics/          # Greeks, Probability, Risk Metrics
│   │   ├── greeks.py       # Greeks calculation logic
│   │   ├── probability.py  # Monte Carlo simulation
│   │   └── risk_metrics.py # Risk/Reward analysis
│   ├── data/               # Data Access Layer
│   │   ├── api_client.py   # TD Ameritrade client wrapper
│   │   ├── cache.py        # Caching mechanisms
│   │   └── database.py     # SQLAlchemy models
│   ├── integration/        # External system integrations
│   │   ├── tos_alerts.py   # ThinkScript generator
│   │   └── watchlist.py    # Watchlist CSV exporter
│   ├── scanner/            # Core scanning logic
│   │   ├── market_scanner.py # Stock screener
│   │   └── options_filter.py # Options chain filter
│   ├── scoring/            # Trade scoring engine
│   │   └── trade_scorer.py # Weighted scoring algorithm
│   ├── strategies/         # Option strategy definitions
│   │   └── strategy_selector.py # Strategy selection logic
│   ├── ui/                 # Streamlit dashboard
│   │   └── dashboard.py    # Main UI application
│   └── utils/              # Helper utilities
│       ├── health.py       # System health checks
│       └── logger.py       # Logging configuration
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules
├── Dockerfile              # Container definition
├── fly.toml                # Fly.io configuration
├── main.py                 # Main entry point (Scanner Loop)
├── mkdocs.yml              # Documentation configuration
├── README.md               # Project overview
├── requirements.txt        # Python dependencies
├── start.sh                # Startup script (Scanner + UI)
├── verify_analytics.py     # Verify analytics calculations
├── verify_health.py        # System health verification
└── verify_setup.py         # Installation verification script
```

## Key Files

-   **`main.py`**: The entry point for the scanning loop. Orchestrates the entire pipeline.
-   **`src/ui/dashboard.py`**: The Streamlit application entry point.
-   **`src/data/api_client.py`**: robust TDA client with circuit breakers and retries.
-   **`config/settings.py`**: Centralized configuration management using `pydantic-settings`.
