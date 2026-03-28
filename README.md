# Binance Funding Rate Arbitrage Bot v3.0 (Quantitative Enhanced)

[中文文档](README-CN.md)

An institutional-grade Binance Futures funding rate arbitrage bot with **multi-factor quantitative filtering**, **cost-aware position sizing**, and **real-time P&L tracking**. Designed for 24/7 unattended operation.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Binance](https://img.shields.io/badge/Exchange-Binance_Futures-yellow.svg)](https://binance.com)

## Table of Contents

- [Overview](#overview)
- [Strategy](#strategy)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Monitoring](#monitoring)
- [Risk Disclaimer](#risk-disclaimer)
- [Troubleshooting](#troubleshooting)

## Overview

This bot captures funding rate payments on Binance Perpetual Futures by opening positions seconds before settlement and closing immediately after. **v3.0** introduces a quantitative pipeline that filters candidates by estimated **net profit** (after fees and spread), ranks them with a **multi-factor scoring model**, and dynamically sizes positions based on opportunity quality.

### Key Features

- **Net Profit Filtering** - Only enters trades where `|funding_rate| - 2×taker_fee - spread > threshold`
- **Multi-Factor Scoring** - Ranks candidates by composite score: net profit rate, rate trend momentum, and liquidity
- **Dynamic Position Sizing** - Kelly-inspired sizing: higher-confidence opportunities get larger allocations (0.5x-2x base)
- **Bid-Ask Spread Check** - Estimates real slippage cost via bookTicker before entry
- **Funding Rate Trend Analysis** - Checks if rate is strengthening or mean-reverting using historical data
- **Volume/Liquidity Gate** - Ensures minimum 24h volume (default 50M USDT) for reliable execution
- **Real-Time P&L Tracking** - Per-round and cumulative estimated P&L logging
- **Multi-Sample Time Sync** - Takes 3 samples and uses the lowest-latency one for microsecond-level accuracy
- **Exponential Backoff Retry** - Failed closes retry 3 times with 0.5s/1s/2s backoff
- **Bidirectional Trading** - Captures both negative rates (go long) and positive rates (go short)

## Strategy

### Core Mechanism

```
Funding Rate Settlement Timeline:

  t-3min          t-2sec        t=0           t+0.5sec
    |               |            |               |
    v               v            v               v
  PRE-SCAN      OPEN POS    SETTLEMENT     CLOSE POS
  (filter &      (parallel    (collect       (parallel
   score)        market       funding        fast close)
                 orders)      fee)
```

### Quantitative Filtering Pipeline

```
All USDT Perpetuals (~300+ pairs)
        |
        v
[1] Rate Gate: |funding_rate| >= 0.05%         --> ~10-30 pass
        |
        v
[2] Volume Gate: 24h volume >= 50M USDT        --> ~10-20 pass
        |
        v
[3] Spread Check: bid-ask spread <= 0.1%       --> ~8-15 pass
        |
        v
[4] Net Profit: rate - 2×fee - spread > 0.01%  --> ~3-8 pass
        |
        v
[5] Multi-Factor Score & Rank                  --> Top N selected
        |
        v
[6] Dynamic Position Sizing                    --> Execute
```

### Multi-Factor Scoring

Each candidate receives a composite score:

```
score = net_profit_rate × (1 + trend_bonus) × liquidity_factor

- net_profit_rate: |funding_rate| - 2×taker_fee - spread_cost
- trend_bonus:     [-20%, +20%] based on recent rate direction
- liquidity_factor: log-scaled 24h volume (0.5x-1.5x)
```

### Entry Conditions (ALL must pass)

| Filter | Threshold | Purpose |
|--------|-----------|---------|
| Funding Rate | \|rate\| >= 0.05% | Minimum gross opportunity |
| 24h Volume | >= 50M USDT | Liquidity / execution quality |
| Bid-Ask Spread | <= 0.1% | Slippage cost control |
| Net Profit Rate | >= 0.01% | Positive expected value after costs |
| No Existing Position | true | Avoid doubling exposure |
| Not Blacklisted | true | Manual exclusion filter |

### Dynamic Position Sizing

```
confidence = net_profit_rate / min_net_profit_rate
factor = clamp(confidence, 0.5, 2.0)
position_size = base_amount × factor

Example: base=200 USDT, net_profit 3x threshold → 400 USDT position
Example: base=200 USDT, net_profit barely above threshold → 100 USDT position
```

## Architecture

```
┌─────────────────────────────────────────────────┐
│           AutoTradingBot v3.0                   │
├─────────────────────────────────────────────────┤
│  Quantitative Pipeline:                         │
│  ┌───────────┐  ┌────────────┐  ┌───────────┐  │
│  │ Rate Gate  │→│ Cost Filter │→│  Scorer    │  │
│  │ + Volume   │  │ spread+fee │  │ multi-    │  │
│  │   Gate     │  │ net profit │  │ factor    │  │
│  └───────────┘  └────────────┘  └───────────┘  │
│                                                 │
│  Execution Engine:                              │
│  ┌───────────┐  ┌────────────┐  ┌───────────┐  │
│  │ Dynamic   │→│  Parallel   │→│  P&L      │  │
│  │ Sizing    │  │  Open/Close │  │  Tracker  │  │
│  └───────────┘  └────────────┘  └───────────┘  │
│                                                 │
│  Infrastructure:                                │
│  ┌───────────┐  ┌────────────┐  ┌───────────┐  │
│  │ Multi-    │  │  Exp.      │  │  Ticker   │  │
│  │ Sample    │  │  Backoff   │  │  Cache    │  │
│  │ TimeSync  │  │  Retry     │  │  (60s)    │  │
│  └───────────┘  └────────────┘  └───────────┘  │
└─────────────────────────────────────────────────┘
                      │
              ┌───────┴───────┐
              │ BinanceFutures│
              │     API       │
              └───────────────┘
```

## Quick Start

### Requirements

- Python 3.8+
- Binance Futures account with API key (trading permission required)

### 1. Clone & Install

```bash
git clone https://github.com/your-username/binance-tradingbot.git
cd binance-tradingbot
pip3 install -r requirements.txt
```

### 2. Configure

Create `.env` file:
```env
# Binance API (required)
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here

# Base trading parameters
TRADE_AMOUNT=200
LEVERAGE=1
MAX_POSITIONS=5

# Timing
OPEN_BEFORE_SECONDS=2
CLOSE_AFTER_SECONDS=0.5
PRE_SCAN_MINUTES=3

# v3.0 Quantitative parameters
MIN_FUNDING_RATE=0.0005
MIN_NET_PROFIT_RATE=0.0001
MAX_SPREAD_RATIO=0.001
MIN_VOLUME_USDT=50000000
DYNAMIC_SIZING=true

# Optional
BLACKLIST_SYMBOLS=
```

### 3. Setup Margin Mode

```bash
python3 setup_margin_modes.py
```

### 4. Launch

```bash
# Interactive mode
python3 auto_trading_bot.py

# Background daemon
./start_bot.sh
```

## Configuration

### Core Parameters

| Variable | Default | Description |
|----------|---------|-------------|
| `TRADE_AMOUNT` | 100 | Base position size (USDT) |
| `LEVERAGE` | 20 | Leverage multiplier |
| `MAX_POSITIONS` | 5 | Max concurrent positions |
| `OPEN_BEFORE_SECONDS` | 2 | Open N seconds before settlement |
| `CLOSE_AFTER_SECONDS` | 0.5 | Close N seconds after settlement |
| `PRE_SCAN_MINUTES` | 3 | Pre-scan window before settlement |

### v3.0 Quantitative Parameters

| Variable | Default | Description |
|----------|---------|-------------|
| `MIN_FUNDING_RATE` | 0.0005 | Minimum \|rate\| for rough filter (0.05%) |
| `MIN_NET_PROFIT_RATE` | 0.0001 | Minimum net profit after fees (0.01%) |
| `MAX_SPREAD_RATIO` | 0.001 | Maximum acceptable bid-ask spread (0.1%) |
| `MIN_VOLUME_USDT` | 50000000 | Minimum 24h volume (50M USDT) |
| `DYNAMIC_SIZING` | true | Enable Kelly-inspired position sizing |
| `BLACKLIST_SYMBOLS` | (empty) | Comma-separated symbols to exclude |

### CLI Parameters

```bash
python3 auto_trading_bot.py --help

Options:
  --amount AMOUNT         Base trade amount (USDT)
  --leverage LEVERAGE     Leverage multiplier
  --min-rate RATE         Minimum funding rate threshold
  --max-positions N       Maximum concurrent positions
  --open-before SEC       Seconds before settlement to open
  --close-after SEC       Seconds after settlement to close
  --testnet               Use testnet
```

## Usage

### Script Management (Recommended)

```bash
./start_bot.sh     # Start background daemon
./check_bot.sh     # Check status
./stop_bot.sh      # Graceful shutdown
```

### Interactive Mode

```bash
python3 auto_trading_bot.py --amount 200 --leverage 2 --max-positions 5
```

### Background Daemon

```bash
nohup python3 run_auto_trading.py > trading.log 2>&1 &
```

### Account Monitor

```bash
python3 main.py    # Interactive account dashboard
```

## Project Structure

```
binance_tradingbot/
├── main.py                    # Core: API client + AutoTradingBot v3.0
├── auto_trading_bot.py        # Interactive launcher with CLI params
├── run_auto_trading.py        # Daemon mode launcher
├── setup_margin_modes.py      # Batch margin mode setup tool
├── debug_position_check.py    # Position check debugger
├── test_new_strategy.py       # Strategy validation tests
├── start_bot.sh               # Background launch script
├── stop_bot.sh                # Process termination script
├── check_bot.sh               # Status monitoring script
├── requirements.txt           # Python dependencies
├── .env                       # Configuration (API keys + parameters)
└── logs/                      # Runtime logs
    ├── bot.pid                # Process ID
    └── trading_bot_*.log      # Timestamped trade logs
```

## Monitoring

### Real-Time Logs

```bash
tail -f logs/trading_bot_*.log
```

### Key Log Events

| Log Pattern | Meaning |
|------------|---------|
| `🔍 粗筛通过: N 个候选` | N pairs passed rate + volume gate |
| `🎯 找到 N 个套利候选` | N pairs passed full quantitative filter |
| `🚀🚀🚀 开仓!` | Parallel market entry executing |
| `🔻🔻🔻 平仓!` | Parallel market exit executing |
| `💰 本轮P&L估算` | Per-round estimated profit breakdown |
| `📊 累计N轮` | Cumulative session P&L |
| `⚡ 开仓耗时: Nms` | Execution latency measurement |

### P&L Tracking

The bot logs estimated P&L for each round:

```
💰 本轮P&L估算: 资金费≈0.1200, 手续费≈0.0800, 净利≈0.0400 USDT
📊 累计12轮: 估算净利≈0.4800 USDT
```

## Risk Disclaimer

### Trading Risks

- **Market Risk**: Price can move adversely during the ~2.5s hold window
- **Leverage Risk**: Amplifies both gains and losses
- **Funding Rate Risk**: Rates can change between scan and settlement
- **Execution Risk**: Network latency or API errors may prevent timely closing
- **Spread Risk**: Illiquid markets may have wider spreads than estimated

### Best Practices

1. Start with small amounts to validate setup
2. Use conservative leverage (1-3x recommended)
3. Monitor logs regularly
4. Keep manual stop-loss procedures ready
5. Never risk more than you can afford to lose

### Disclaimer

This project is for educational and research purposes only. It does not constitute investment advice. Users bear all trading risks. The author is not responsible for any losses.

## Troubleshooting

### Common Issues

1. **API Connection Failed**
   ```bash
   python3 -c "from main import BinanceFuturesAPI; api = BinanceFuturesAPI(); print('OK')"
   ```

2. **Margin Mode Error**
   ```bash
   python3 setup_margin_modes.py
   ```

3. **Bot Won't Start**
   ```bash
   tail -50 logs/trading_bot_*.log
   ./check_bot.sh
   ```

4. **Permission Denied**
   ```bash
   chmod +x *.sh
   ```

### Debug Commands

```bash
# Test API
python3 -c "from main import BinanceFuturesAPI; api = BinanceFuturesAPI(); print('Connected')"

# Check blacklist
python3 -c "from main import AutoTradingBot; bot = AutoTradingBot(); bot.debug_blacklist()"

# View funding rates
python3 -c "from main import BinanceFuturesAPI; api = BinanceFuturesAPI(); api.debug_funding_rates()"
```
