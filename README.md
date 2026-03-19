# Binance AI Trading Bot

An automated Binance Futures trading bot based on negative funding rate arbitrage strategy, featuring multi-indicator analysis and 24/7 unattended trading.

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

A smart trading bot designed for the Binance Futures market, primarily leveraging negative funding rate arbitrage. The bot uses comprehensive multi-indicator analysis — including funding rate, MACD, long/short ratio, and volume — to execute fully automated position opening and closing.

### Key Features

- **Negative Funding Rate Arbitrage**: Captures funding fee income from negative funding rates
- **Fully Automated**: Auto-scanning, position opening/closing with zero manual intervention
- **Multi-Indicator Analysis**: Combines MACD, long/short ratio, volume and more
- **Risk Control**: Smart stop-loss, blacklist filtering, leverage management
- **Real-time Monitoring**: Complete account and position monitoring system
- **Flexible Configuration**: Supports environment variables and command-line arguments
- **Background Execution**: Supports nohup for persistent background operation

## Trading Strategy

### Long Entry Conditions (All Must Be Met)

```
- Funding rate < -0.1% (negative funding rate)
- 24h trading volume > 60M USDT
- MACD daily slow line > 0 (daily uptrend)
- Long/short ratio < 1 (shorts dominant)
- 24h price change > 0 (positive daily movement)
- Funding rate settlement interval = 1 hour (high-frequency settlement)
- Excludes contracts with 0 funding rate
```

### Exit Conditions

```
Automatically closes positions when entry conditions are no longer met:
  - Funding rate >= -0.1% (negative rate weakening or turning positive)
  - 24h price change <= 0 (turning bearish)
  - Funding rate settlement interval no longer 1 hour
Independent monitoring thread checks positions every 5 minutes
Fully automated — no manual intervention required
```

### Strategy Logic

1. **Negative Funding Rate Arbitrage**: Going long during negative funding rates earns funding fee income
2. **Multi-Indicator Screening**: Ensures selected assets have solid technicals and market structure
3. **Risk Management**: Controls risk through leverage limits, blacklists, and other mechanisms
4. **Dynamic Monitoring**: Real-time funding rate monitoring with timely position exits

## Features

### Automated Trading
- Negative funding rate scanning and filtering
- Multi-indicator technical analysis (MACD, long/short ratio, volume)
- Automatic position opening and closing
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
LEVERAGE=2
MONITOR_INTERVAL=300
POSITION_CHECK_INTERVAL=300

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
| `LEVERAGE` | 2 | Leverage multiplier |
| `MONITOR_INTERVAL` | 300 | Monitoring interval (seconds) |
| `POSITION_CHECK_INTERVAL` | 300 | Position check interval (seconds) |
| `BLACKLIST_SYMBOLS` | - | Blacklisted trading pairs (comma-separated) |
| `USE_TESTNET` | false | Use testnet environment |

### Command-Line Arguments

```bash
python3 auto_trading_bot.py --help

Options:
  --amount AMOUNT       Trade amount in USDT (default: 100)
  --leverage LEVERAGE   Leverage multiplier (default: 2)
  --interval INTERVAL   Monitoring interval in seconds (default: 300)
  --position-check-interval INTERVAL
                        Position check interval in seconds (default: 300)
  --testnet             Use testnet
```

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
# Default parameters
python3 auto_trading_bot.py

# Custom parameters
python3 auto_trading_bot.py --amount 50 --leverage 5
```

### Option 3: Background Mode

```bash
# Run in background with nohup
nohup python3 run_auto_trading.py > trading.log 2>&1 &
```

### Option 4: Account Monitoring

```bash
# View account info
python3 main.py

# Debug position check
python3 debug_position_check.py
```

## Project Structure

```
binancebot-long-lewis/
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

# View system processes
ps aux | grep python3
```

### Log Analysis

Log files contain:
- Trading signals and decision processes
- Position open/close records
- Account balance changes
- Errors and exceptions
- Performance statistics

### Performance Monitoring

```bash
# View account summary
python3 main.py

# Get position info
python3 -c "from main import BinanceAccountMonitor; m = BinanceAccountMonitor(); m.print_positions()"
```

## API Reference

### BinanceFuturesAPI

```python
from main import BinanceFuturesAPI

# Initialize API
api = BinanceFuturesAPI()

# Account information
account = api.get_account_info()
positions = api.get_positions()
balance = api.get_balance()

# Trading operations
api.place_order(symbol='BTCUSDT', side='BUY', order_type='MARKET', quoteOrderQty=100)
api.close_position('BTCUSDT')
api.set_leverage('BTCUSDT', 5)

# Market data
funding_rates = api.get_funding_rates()
klines = api.get_klines('BTCUSDT', '1d')
```

### AutoTradingBot

```python
from main import AutoTradingBot

# Initialize trading bot
bot = AutoTradingBot()

# Set trading parameters
bot.trade_amount = 100
bot.leverage = 5

# Start monitoring
bot.start_monitoring()
```

## Risk Disclaimer

### Trading Risks

- **Market Risk**: Futures trading involves significant price volatility
- **Leverage Risk**: Leveraged trading amplifies both gains and losses
- **Funding Rate Risk**: Funding rates can change rapidly
- **Technical Risk**: Indicator failures or network issues may occur

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
   # Check API key configuration
   cat .env | grep BINANCE_API

   # Test API connection
   python3 -c "from main import BinanceFuturesAPI; api = BinanceFuturesAPI(); print(api.get_account_info())"
   ```

2. **Margin Mode Error**
   ```bash
   # Re-run margin mode setup
   python3 setup_margin_modes.py
   ```

3. **Bot Startup Failed**
   ```bash
   # View detailed logs
   tail -50 logs/trading_bot_*.log

   # Check process status
   ./check_bot.sh
   ```

4. **Permission Issues**
   ```bash
   # Add execute permissions
   chmod +x *.sh
   ```

### Debug Commands

```bash
# Test API connection
python3 -c "from main import BinanceFuturesAPI; api = BinanceFuturesAPI(); print('API connection successful')"

# Check blacklist configuration
python3 -c "from main import AutoTradingBot; bot = AutoTradingBot(); bot.debug_blacklist()"

# View funding rates
python3 -c "from main import BinanceFuturesAPI; api = BinanceFuturesAPI(); api.debug_funding_rates()"
```
