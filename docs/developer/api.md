# API Reference

This section documents the key classes and methods used in the Options Day-Trading Assistant.

## Core Modules

### `src.scanner.MarketScanner`

The `MarketScanner` class is responsible for identifying potential stock candidates based on technical indicators.

#### `scan_market(symbols: List[str]) -> List[Dict]`

Scans a list of symbols and returns those matching the criteria.

-   **symbols**: List of stock tickers to scan.
-   **Returns**: A list of dictionaries containing symbol data (price, volume, RSI, ATR).

### `src.scanner.OptionsFilter`

The `OptionsFilter` class selects optimal options contracts for a given stock.

#### `filter_options(symbol: str) -> List[Dict]`

Retrieves the option chain and filters for liquid contracts.

-   **symbol**: Stock ticker.
-   **Returns**: a list of valid option contracts (calls/puts).

### `src.analytics.ProbabilityCalculator`

Calculates probability of profit using Monte Carlo simulations and Black-Scholes model.

#### `calculate_probabilities(trade: Dict) -> Dict`

-   **trade**: Trade dictionary containing entry price, strike price, DTE, and IV.
-   **Returns**: Dictionary with `probability_itm`, `probability_otm`, and `expected_value`.

### `src.scoring.TradeScorer`

Assigns a score to each potential trade based on weighted factors.

#### `score_trade(trade: Dict) -> float`

-   **trade**: The trade object to score.
-   **Returns**: A float between 0 and 100 representing the trade quality.

## Configuration

Settings are managed via `pydantic-settings` in `config/settings.py`.

### `Settings` Class

-   `TDA_API_KEY`: TD Ameritrade API Key.
-   `DATABASE_URL`: Database connection string.
-   `MIN_STOCK_PRICE`: Minimum stock price for scanning (default: $20).
-   `MAX_STOCK_PRICE`: Maximum stock price for scanning (default: $300).
-   `MIN_TRADE_SCORE`: Minimum score required to alert a trade (default: 70).
