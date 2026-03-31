# Binance Short Strategy Trading Bot

An automated Binance Futures trading bot that opens short positions at the top of each hour on coins with negative funding rates, and takes profit when returns reach 2% or more.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Binance](https://img.shields.io/badge/Exchange-Binance_Futures-yellow.svg)](https://binance.com)

[中文文档](README-CN.md)

## Table of Contents

- [Overview](#overview)
- [Trading Strategy](#trading-strategy)
- [Features](#features)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Monitoring](#monitoring)
- [Risk Disclaimer](#risk-disclaimer)
- [Troubleshooting](#troubleshooting)

## Overview

This bot exploits the price drop that occurs after funding rate settlement on coins with negative funding rates. When a coin has a significantly negative funding rate with hourly settlement, arbitrageurs go long to collect funding fees. At each hour mark when the funding rate settles, these arbitrageurs close their long positions, creating selling pressure. This bot opens a short position at that moment and closes it when the profit reaches 2%.

### Key Features

- **Hourly Short Strategy**: Opens short positions at each hour mark to capture post-settlement price drops
- **Automatic Take Profit**: Closes positions when profit reaches >= 2%
- **Smart Screening**: Filters for coins with negative funding rates < -0.1%
- **Risk Control**: Blacklist filtering, leverage management
- **Real-time Monitoring**: Complete account and position monitoring system
- **Background Execution**: Supports nohup for persistent background operation

## Trading Strategy

### Short Entry Conditions (All Must Be Met)

```
- Funding rate < -0.1% (negative funding rate, indicating active arbitrage)
- Current time is at the hour mark (top of the hour)
- No existing position for the symbol
- Not on the blacklist
```

### Exit Conditions

```
- Take profit: Short position profit >= 2%
- Stop loss: Short position loss >= 2%
- Position check interval: 30 seconds (fast detection)
```

### Strategy Logic

1. **Identify Arbitrage Targets**: Scan for coins with funding rate < -0.1%
2. **Wait for Settlement**: The bot waits until the top of each hour (when funding settles)
3. **Open Short**: At the hour mark, arbitrageurs close their longs, creating selling pressure — the bot shorts at this moment
4. **Take Profit / Stop Loss**: A monitoring thread checks positions every 30 seconds, closes when profit >= 2% or loss >= 2%

## Features

### Automated Trading
- Negative funding rate scanning and filtering
- Automatic short position opening at hour marks
- Fast take-profit monitoring (30-second intervals)
- Dynamic leverage and margin management
- Blacklist filtering

### Account Management
- Real-time account information queries
- Position and order monitoring
- Batch margin mode configuration
- Trade history viewing

### System Monitoring
- Detailed logging
- Process status monitoring
- Real-time performance data
- Exception alerts and handling

## Quick Start

### Requirements

- Python 3.8+
- Binance Futures account
- API key (with Futures trading permission)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/binance-ai-bot.git
cd binance-ai-bot
```

### 2. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 3. Configure API Keys

Create a `.env` file:
```env
# Binance API Configuration (Required)
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here

# Trading Parameters (Optional)
TRADE_AMOUNT=100
LEVERAGE=20
POSITION_CHECK_INTERVAL=30

# Blacklist Settings (Optional)
BLACKLIST_SYMBOLS=LUNAUSDT,USTCUSDT

# Testnet (Optional)
USE_TESTNET=false
```

### 4. Set Margin Mode

```bash
# Must be run before first use — sets cross margin mode
python3 setup_margin_modes.py
```

### 5. Start the Bot

```bash
# Option 1: Use the startup script (Recommended)
./start_bot.sh

# Option 2: Run directly
python3 auto_trading_bot.py
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BINANCE_API_KEY` | - | Binance API key (required) |
| `BINANCE_API_SECRET` | - | Binance API secret (required) |
| `TRADE_AMOUNT` | 100 | Trade amount per order (USDT) |
| `LEVERAGE` | 20 | Leverage multiplier |
| `POSITION_CHECK_INTERVAL` | 30 | Position check interval in seconds |
| `BLACKLIST_SYMBOLS` | - | Blacklisted trading pairs (comma-separated) |
| `USE_TESTNET` | false | Use testnet environment |

## Usage

### Option 1: Script Management (Recommended)

```bash
# Start the bot
./start_bot.sh

# Check status
./check_bot.sh

# Stop the bot
./stop_bot.sh
```

### Option 2: Interactive Mode

```bash
python3 auto_trading_bot.py
```

### Option 3: Background Mode

```bash
nohup python3 run_auto_trading.py > trading.log 2>&1 &
```

### Option 4: Account Monitoring

```bash
python3 main.py
```

## Project Structure

```
binance_tradingbot/
├── main.py                    # Core API and trading logic
├── auto_trading_bot.py        # Interactive startup script
├── run_auto_trading.py        # Background execution script
├── setup_margin_modes.py      # Margin mode setup tool
├── debug_position_check.py    # Position check debug tool
├── start_bot.sh              # Start script
├── stop_bot.sh               # Stop script
├── check_bot.sh              # Status check script
├── requirements.txt          # Dependencies
├── .env                      # Environment configuration
└── logs/                     # Log directory
    ├── bot.pid              # Process ID file
    └── trading_bot_*.log    # Trading logs
```

## Monitoring

### Real-time Monitoring

```bash
# View live logs
tail -f logs/trading_bot_*.log

# Check process status
./check_bot.sh
```

### Log Analysis

Log files contain:
- Short entry signals and screening results
- Position open/close records with profit percentages
- Take-profit and stop-loss events
- Account balance changes
- Errors and exceptions

## Risk Disclaimer

### Trading Risks

- **Market Risk**: Futures trading involves significant price volatility
- **Leverage Risk**: Leveraged trading amplifies both gains and losses
- **Strategy Risk**: The price may not drop after settlement; arbitrageurs may not close positions as expected
- **Technical Risk**: Network issues or API failures may prevent timely order execution

### Recommendations

1. **Start Small**: Test with small amounts first
2. **Reasonable Leverage**: Avoid excessive leverage
3. **Monitor Positions**: Regularly check positions and account status
4. **Have a Backup Plan**: Prepare manual stop-loss procedures
5. **Money Management**: Never invest more than you can afford to lose

### Disclaimer

This project is for educational and research purposes only and does not constitute investment advice. Users assume all trading risks. The author is not responsible for any losses.

## Troubleshooting

### Common Issues

1. **API Connection Failed**
   ```bash
   python3 -c "from main import BinanceFuturesAPI; api = BinanceFuturesAPI(); print(api.get_account_info())"
   ```

2. **Margin Mode Error**
   ```bash
   python3 setup_margin_modes.py
   ```

3. **Bot Startup Failed**
   ```bash
   tail -50 logs/trading_bot_*.log
   ./check_bot.sh
   ```

4. **Permission Issues**
   ```bash
   chmod +x *.sh
   ```
