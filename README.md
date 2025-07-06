# 🤖 Binance AI Trading Bot

一个基于负资金费率套利策略的币安合约自动化交易机器人，采用多指标融合分析，支持24/7不间断自动交易。

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Binance](https://img.shields.io/badge/Exchange-Binance_Futures-yellow.svg)](https://binance.com)

## 📋 目录

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

## 🎯 项目介绍

这是一个专为币安合约市场设计的智能交易机器人，主要利用负资金费率进行套利交易。机器人采用多指标综合分析，包括资金费率、MACD、多空比和成交量等，实现全自动化的开仓和平仓操作。

### 核心特性

- 🎯 **负资金费率套利**: 专注于负资金费率机会，获取资金费用收益
- 🔄 **全自动交易**: 自动扫描、开仓、平仓，无需人工干预
- 📊 **多指标分析**: 结合MACD、多空比、成交量等多个指标
- 🛡️ **风险控制**: 智能止损、黑名单、杠杆控制等安全机制
- 📈 **实时监控**: 完整的账户和持仓监控系统
- 🔧 **灵活配置**: 支持环境变量和命令行参数配置
- 🚀 **后台运行**: 支持nohup后台运行，SSH断开后继续工作

## 📊 交易策略

### 做多开仓条件（需同时满足）

```
✅ 资金费率 < -0.1%（负资金费率）
✅ 24小时交易量 > 6000万 USDT
✅ MACD日级慢线 > 0（日线趋势向上）
✅ 多空比 < 1（空头占优势）
✅ 剔除资金费率为0的合约
✅ 24小时涨跌幅大于0
```

### 平仓条件

```
📈 资金费率 ≥ -0.1%（负资金费率减弱或转正）
⏰ 独立监控线程每5分钟检查一次持仓
🔄 自动平仓，无需人工干预
```

### 策略逻辑

1. **负资金费率套利**: 当资金费率为负时，做多可以获得资金费用收益
2. **多指标筛选**: 确保选择的标的具有良好的技术面和市场结构
3. **风险控制**: 通过杠杆限制、黑名单等机制控制风险
4. **动态监控**: 实时监控资金费率变化，及时平仓

## 🚀 核心功能

### 自动化交易
- ✅ 负资金费率扫描和筛选
- ✅ 多指标技术分析（MACD、多空比、成交量）
- ✅ 自动开仓和平仓
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

## 🛠 快速开始

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
LEVERAGE=2
MONITOR_INTERVAL=300
POSITION_CHECK_INTERVAL=300

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

## ⚙️ 配置说明

### 环境变量配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `BINANCE_API_KEY` | - | 币安API密钥（必需） |
| `BINANCE_API_SECRET` | - | 币安API密钥（必需） |
| `TRADE_AMOUNT` | 100 | 每次交易金额（USDT） |
| `LEVERAGE` | 2 | 杠杆倍数 |
| `MONITOR_INTERVAL` | 300 | 监控间隔（秒） |
| `POSITION_CHECK_INTERVAL` | 300 | 持仓检查间隔（秒） |
| `BLACKLIST_SYMBOLS` | - | 黑名单交易对（逗号分隔） |
| `USE_TESTNET` | false | 是否使用测试网 |

### 命令行参数

```bash
python3 auto_trading_bot.py --help

可选参数:
  --amount AMOUNT       每次交易金额(USDT，默认100)
  --leverage LEVERAGE   杠杆倍数(默认2)
  --interval INTERVAL   监控间隔(秒，默认300)
  --position-check-interval INTERVAL
                        持仓检查间隔(秒，默认300)
  --testnet             使用测试网
```

## 💻 使用方法

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
# 使用默认参数
python3 auto_trading_bot.py

# 自定义参数
python3 auto_trading_bot.py --amount 50 --leverage 5
```

### 方式三：后台运行

```bash
# 使用nohup后台运行
nohup python3 run_auto_trading.py > trading.log 2>&1 &
```

### 方式四：账户监控

```bash
# 查看账户信息
python3 main.py

# 调试持仓检查
python3 debug_position_check.py
```

## 📁 项目结构

```
binancebot-long-lewis/
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

## 📈 监控管理

### 实时监控

```bash
# 查看实时日志
tail -f logs/trading_bot_*.log

# 检查进程状态
./check_bot.sh

# 查看系统进程
ps aux | grep python3
```

### 日志分析

日志文件包含以下信息：
- 交易信号和决策过程
- 开仓和平仓记录
- 账户余额变化
- 错误和异常信息
- 性能统计数据

### 性能监控

```bash
# 查看账户摘要
python3 main.py

# 获取持仓信息
python3 -c "from main import BinanceAccountMonitor; m = BinanceAccountMonitor(); m.print_positions()"
```

## 🔧 API功能

### BinanceFuturesAPI类

```python
from main import BinanceFuturesAPI

# 初始化API
api = BinanceFuturesAPI()

# 获取账户信息
account = api.get_account_info()
positions = api.get_positions()
balance = api.get_balance()

# 交易操作
api.place_order(symbol='BTCUSDT', side='BUY', order_type='MARKET', quoteOrderQty=100)
api.close_position('BTCUSDT')
api.set_leverage('BTCUSDT', 5)

# 市场数据
funding_rates = api.get_funding_rates()
klines = api.get_klines('BTCUSDT', '1d')
```

### AutoTradingBot类

```python
from main import AutoTradingBot

# 初始化交易机器人
bot = AutoTradingBot()

# 设置交易参数
bot.trade_amount = 100
bot.leverage = 5

# 启动监控
bot.start_monitoring()
```

## ⚠️ 风险提示

### 交易风险

- 📊 **市场风险**: 合约交易存在价格波动风险
- 💰 **杠杆风险**: 杠杆交易会放大盈亏
- 🔄 **资金费率风险**: 资金费率可能快速变化
- 📉 **技术风险**: 指标失效或网络问题

### 使用建议

1. **小额测试**: 首次使用建议小额测试
2. **合理杠杆**: 不要使用过高杠杆倍数
3. **监控止损**: 定期检查持仓和账户状态
4. **备用方案**: 准备手动止损方案
5. **资金管理**: 不要投入全部资金

### 免责声明

本项目仅供学习和研究使用，不构成投资建议。使用者需要承担所有交易风险，作者不对任何损失负责。

## 🔍 故障排除

### 常见问题

1. **API连接失败**
   ```bash
   # 检查API密钥配置
   cat .env | grep BINANCE_API
   
   # 测试API连接
   python3 -c "from main import BinanceFuturesAPI; api = BinanceFuturesAPI(); print(api.get_account_info())"
   ```

2. **保证金模式错误**
   ```bash
   # 重新设置保证金模式
   python3 setup_margin_modes.py
   ```

3. **机器人启动失败**
   ```bash
   # 查看详细日志
   tail -50 logs/trading_bot_*.log
   
   # 检查进程状态
   ./check_bot.sh
   ```

4. **权限问题**
   ```bash
   # 添加执行权限
   chmod +x *.sh
   ```

### 调试命令

```bash
# 测试API连接
python3 -c "from main import BinanceFuturesAPI; api = BinanceFuturesAPI(); print('API连接成功')"

# 检查黑名单配置
python3 -c "from main import AutoTradingBot; bot = AutoTradingBot(); bot.debug_blacklist()"

# 查看资金费率
python3 -c "from main import BinanceFuturesAPI; api = BinanceFuturesAPI(); api.debug_funding_rates()"
```

## 📄 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 📞 支持

如果您在使用过程中遇到问题，请：

1. 查看本README的故障排除部分
2. 检查日志文件中的错误信息
3. 提交Issue描述具体问题

---

⚡ **记住：投资有风险，入市需谨慎！**
