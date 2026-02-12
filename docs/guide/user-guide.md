# User Guide

This section explains how to use the dashboard and scanner.

## Dashboard Overview

The dashboard is built with [Streamlit](https://streamlit.io) and provides real-time monitoring of your options trading system.

### Running the Dashboard

```bash
streamlit run src/ui/dashboard.py
```

### Key Sections

1.  **Dashboard**:
    -   **Portfolio Overview**: Shows total trades, trades today, and other key metrics.
    -   **Recent Activity**: Displays the most recent trades found by the scanner.
    -   **Risk Distribution**: Visualizes the risk distribution across your portfolio.

2.  **Scanner Results**:
    -   Displays the raw output from the scanner.
    -   (Integration pending: connect to live scanner output)

3.  **Trade Journal**:
    -   **Search**: Filter trades by symbol.
    -   **Table**: View all historical trades with details like strategy, bias, strikes, DTE, score, and more.

4.  **System Health**:
    -   **Status Check**: Run a health check on the API, database, and disk.
    -   **Metrics**: View API latency and connection status.

## Scanner Workflow

The scanner is the core engine of the system. It runs in the background and continuously scans for opportunities.

### Manual Scanner Execution

To run the scanner manually (useful for testing or one-off scans):

```bash
python main.py
```

This will run a single scan cycle and output the results to the console.

### Automated Scanner

To run the scanner continuously in the background, use the `start.sh` script (or `bat` file on Windows):

```bash
./start.sh
```

This script loops the scanner every 15 minutes.

## Interpreting Trade Alerts

The system generates alerts based on its analysis.

-   **Score**: Each trade is assigned a score (0-100) based on probability, risk/reward, and technical indicators.
    -   **> 80**: High probability setup.
    -   **60-80**: Moderate setups.
    -   **< 60**: Generally ignored.

-   **Risk/Reward (R/R)**: Ratio of Max Gain to Max Loss. Higher is better.
-   **Greeks**: Delta, Gamma, Theta, Vega are calculated for each option leg.

## Exporting Data

-   **Watchlists**: Generated CSV files in `outputs/watchlists/` can be imported into ThinkorSwim.
-   **Alerts**: ThinkScript alert code in `outputs/alerts/` can be pasted into ThinkorSwim studies.
