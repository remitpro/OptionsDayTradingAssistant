# Architecture Overview

This document describes the high-level architecture of the Options Day-Trading Assistant, built to identify high-probability options trades across the market.

## System Components

The system is composed of several key modules, orchestrated to deliver reliable trade signals.

### 1. Market Scanner
-   **Role**: Continuously scans the market for potential candidates.
-   **Filters**: RSI (< 30, > 70), ATR (> 1.5), Volume (> 1M).
-   **Output**: List of candidate symbols.

### 2. Options Filter
-   **Role**: Selects the best options contracts for each candidate.
-   **Criteria**:
    -   Liquidity: Open Interest (> 1000), Volume (> 300).
    -   Spread: Tight bid-ask spreads (< 5%).
    -   DTE: 0-7 days typically.
-   **Strategies**: Supports Calls, Puts, Iron Condors, Vertical Spreads.

### 3. Analytics Engine
-   **Role**: Calculates Greeks and theoretical values.
-   **Library**: `py_vollib` (Black-Scholes).
-   **Metrics**: Delta, Gamma, Theta, Vega, Implied Volatility (IV).

### 4. Risk Manager
-   **Role**: Validates trades against portfolio risk limits.
-   **Checks**:
    -   Max Position Size
    -   Max Loss per Trade
    -   Correlation checks (prevent over-exposure to a sector).

### 5. Trade Scorer
-   **Role**: Assigns a final score (0-100) to each trade.
-   **Inputs**: Probability of Profit (POP), Risk/Reward Ratio, IV Rank, Technical Score.
-   **Configuration**: Weights are adjustable in `config/settings.py`.

## Data Flow

1.  **Input**: Market Data (TDA API).
2.  **Processing**:
    -   Scanner identifies stocks.
    -   Filter selects options.
    -   Analytics computes Greeks.
    -   Scorer ranks trades.
    -   Risk Manager validates.
3.  **Output**:
    -   Database (`trades.db`).
    -   Alerts (ThinkScript).
    -   Watchlists (CSV).
    -   Dashboard (Streamlit).

## Technology Stack

-   **Language**: Python 3.11+
-   **Web Framework**: Streamlit
-   **Database**: SQLite (Development), PostgreSQL (Production ready)
-   **API**: TD Ameritrade (via `tda-api`), HTTP requests
-   **Containerization**: Docker
-   **Deployment**: Fly.io
