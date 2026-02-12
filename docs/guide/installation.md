# Installation Guide

This guide will help you install and configure the Options Day-Trading Assistant on your local machine.

## Prerequisites

- **Python 3.11** or newer.
- **Git** for version control.
- **TD Ameritrade Developer Account** (or Schwab API access) for API keys.
    - [TD Ameritrade Developers](https://developer.tdameritrade.com/)

## Step 1: Clone the Repository

Clone the project to your local machine:

```bash
git clone https://github.com/yourusername/OptionsDayTradingAssistant.git
cd OptionsDayTradingAssistant
```

## Step 2: Create a Virtual Environment

It is recommended to use a virtual environment to manage dependencies.

```bash
python -m venv venv
# Activate the virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

## Step 3: Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

## Step 4: Environment Configuration

Create a `.env` file in the root directory by copying the `.env.example` file:

```bash
cp .env.example .env
```

Open `.env` and fill in your details:

```ini
# .env file content
TDA_API_KEY=your_api_key_here
TDA_REDIRECT_URI=http://localhost

# Optional: Adjust scanner parameters
# MIN_STOCK_PRICE=20.0
# MAX_STOCK_PRICE=300.0
```

## Step 5: Verify Installation

Run the verification script to ensure everything is set up correctly:

```bash
python verify_setup.py
```

If checks pass, you are ready to use the application!
