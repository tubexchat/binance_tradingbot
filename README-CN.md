# Binance 整点做空策略交易机器人

一个基于整点做空策略的币安合约自动化交易机器人。在负资金费率的币种整点结算时开空，利用套利者平仓的抛压获利，收益达到2%时自动平仓。

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Binance](https://img.shields.io/badge/Exchange-Binance_Futures-yellow.svg)](https://binance.com)

[English](README.md)

## 目录

- [项目介绍](#项目介绍)
- [交易策略](#交易策略)
- [核心功能](#核心功能)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [使用方法](#使用方法)
- [项目结构](#项目结构)
- [监控管理](#监控管理)
- [风险提示](#风险提示)
- [故障排除](#故障排除)

## 项目介绍

当某个币种的资金费率为负且结算周期为1小时时，大量套利者会做多以赚取资金费用。在每个整点资金费率结算后，这些套利者会平掉多头仓位，产生抛压导致价格下跌。本机器人在整点时开空，捕捉这一下跌机会，收益达到2%时自动止盈平仓。

### 核心特性

- **整点做空**: 在每个整点资金费率结算时自动开空
- **自动止盈止损**: 收益 >= 2% 止盈，亏损 >= 2% 止损
- **智能筛选**: 筛选负资金费率 < -0.1% 的币种
- **风险控制**: 黑名单过滤、杠杆管理
- **实时监控**: 完整的账户和持仓监控系统
- **后台运行**: 支持nohup后台持续运行

## 交易策略

### 做空开仓条件（需同时满足）

```
✅ 资金费率 < -0.1%（负资金费率，说明有大量套利者做多）
✅ 当前时间为整点（资金费率结算时刻）
✅ 该币种当前没有持仓
✅ 不在黑名单中
```

### 平仓条件

```
🎯 止盈: 空头收益 >= 2%
🛑 止损: 空头亏损 >= 2%
⏰ 持仓监控间隔: 30秒（快速检测）
```

### 策略逻辑

1. **识别套利标的**: 扫描资金费率 < -0.1% 的合约
2. **等待整点**: 机器人等待到每个整点（资金费率结算时刻）
3. **整点开空**: 结算后套利者平掉多头产生抛压，此时开空
4. **止盈止损监控**: 监控线程每30秒检查持仓，收益 >= 2% 止盈，亏损 >= 2% 止损

## 核心功能

### 自动化交易
- ✅ 每小时自动扫描负资金费率合约
- ✅ 整点自动开空
- ✅ 快速止盈止损监控（30秒间隔）
- ✅ 动态杠杆和保证金管理
- ✅ 黑名单过滤功能

### 账户管理
- ✅ 实时账户信息查询
- ✅ 持仓和订单监控
- ✅ 批量保证金模式设置
- ✅ 交易历史记录查看

### 系统监控
- ✅ 详细日志记录
- ✅ 进程状态监控
- ✅ 实时性能数据
- ✅ 异常告警和处理

## 快速开始

### 环境要求

- Python 3.8+
- 币安合约账户
- API密钥（需要合约交易权限）

### 1. 克隆项目

```bash
git clone https://github.com/your-username/binance-ai-bot.git
cd binance-ai-bot
```

### 2. 安装依赖

```bash
pip3 install -r requirements.txt
```

### 3. 配置API密钥

创建 `.env` 文件：
```env
# 币安API配置（必需）
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here

# 交易参数（可选）
TRADE_AMOUNT=100
LEVERAGE=20
POSITION_CHECK_INTERVAL=30

# 黑名单设置（可选）
BLACKLIST_SYMBOLS=LUNAUSDT,USTCUSDT

# 测试环境（可选）
USE_TESTNET=false
```

### 4. 设置保证金模式

```bash
# 首次使用前必须设置为全仓模式
python3 setup_margin_modes.py
```

### 5. 启动机器人

```bash
# 方式一：使用启动脚本（推荐）
./start_bot.sh

# 方式二：直接运行
python3 auto_trading_bot.py
```

## 配置说明

### 环境变量配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `BINANCE_API_KEY` | - | 币安API密钥（必需） |
| `BINANCE_API_SECRET` | - | 币安API密钥（必需） |
| `TRADE_AMOUNT` | 100 | 每次交易金额（USDT） |
| `LEVERAGE` | 20 | 杠杆倍数 |
| `POSITION_CHECK_INTERVAL` | 30 | 持仓检查间隔（秒） |
| `BLACKLIST_SYMBOLS` | - | 黑名单交易对（逗号分隔） |
| `USE_TESTNET` | false | 是否使用测试网 |

## 使用方法

### 方式一：脚本管理（推荐）

```bash
# 启动机器人
./start_bot.sh

# 检查运行状态
./check_bot.sh

# 停止机器人
./stop_bot.sh
```

### 方式二：交互式运行

```bash
python3 auto_trading_bot.py
```

### 方式三：后台运行

```bash
nohup python3 run_auto_trading.py > trading.log 2>&1 &
```

### 方式四：账户监控

```bash
python3 main.py
```

## 项目结构

```
binance_tradingbot/
├── main.py                    # 核心API和交易逻辑
├── auto_trading_bot.py        # 交互式启动脚本
├── run_auto_trading.py        # 后台运行脚本
├── setup_margin_modes.py      # 保证金模式设置工具
├── debug_position_check.py    # 持仓检查调试工具
├── start_bot.sh              # 启动脚本
├── stop_bot.sh               # 停止脚本
├── check_bot.sh              # 状态检查脚本
├── requirements.txt          # 依赖列表
├── .env                      # 环境变量配置
└── logs/                     # 日志目录
    ├── bot.pid              # 进程ID文件
    └── trading_bot_*.log    # 交易日志
```

## 监控管理

### 实时监控

```bash
# 查看实时日志
tail -f logs/trading_bot_*.log

# 检查进程状态
./check_bot.sh
```

### 日志分析

日志文件包含以下信息：
- 做空信号和筛选结果
- 开仓和平仓记录（含收益率）
- 止盈止损事件
- 账户余额变化
- 错误和异常信息

## 风险提示

### 交易风险

- **市场风险**: 合约交易存在价格波动风险
- **杠杆风险**: 杠杆交易会放大盈亏
- **策略风险**: 结算后价格不一定下跌，套利者可能不会按预期平仓
- **技术风险**: 网络问题或API故障可能导致无法及时执行订单

### 使用建议

1. **小额测试**: 首次使用建议小额测试
2. **合理杠杆**: 不要使用过高杠杆倍数
3. **监控止损**: 定期检查持仓和账户状态
4. **备用方案**: 准备手动止损方案
5. **资金管理**: 不要投入全部资金

### 免责声明

本项目仅供学习和研究使用，不构成投资建议。使用者需要承担所有交易风险，作者不对任何损失负责。

## 故障排除

### 常见问题

1. **API连接失败**
   ```bash
   python3 -c "from main import BinanceFuturesAPI; api = BinanceFuturesAPI(); print(api.get_account_info())"
   ```

2. **保证金模式错误**
   ```bash
   python3 setup_margin_modes.py
   ```

3. **机器人启动失败**
   ```bash
   tail -50 logs/trading_bot_*.log
   ./check_bot.sh
   ```

4. **权限问题**
   ```bash
   chmod +x *.sh
   ```
