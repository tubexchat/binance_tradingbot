# Binance 资金费率套利机器人 v3.0 (量化增强版)

[English](README.md)

一个机构级的币安合约资金费率套利机器人，具备**多因子量化过滤**、**成本感知仓位管理**和**实时P&L追踪**。为24/7无人值守运行而设计。

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Binance](https://img.shields.io/badge/Exchange-Binance_Futures-yellow.svg)](https://binance.com)

## 目录

- [项目介绍](#项目介绍)
- [交易策略](#交易策略)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [使用方法](#使用方法)
- [项目结构](#项目结构)
- [监控管理](#监控管理)
- [风险提示](#风险提示)
- [故障排除](#故障排除)

## 项目介绍

本机器人通过在资金费率结算前数秒开仓、结算后立即平仓来捕获资金费率收益。**v3.0** 引入量化分析管线，通过估算**净利润**（扣除手续费和价差后）过滤候选，使用**多因子评分模型**排序，并根据机会质量动态调整仓位大小。

### 核心特性

- **净利润过滤** - 仅在 `|资金费率| - 2×手续费 - 价差 > 阈值` 时入场
- **多因子评分** - 综合评分: 净利润率 × 费率趋势动量 × 流动性因子
- **动态仓位管理** - Kelly准则启发: 高置信度机会获得更大仓位(0.5x-2x基础仓位)
- **买卖价差检查** - 入场前通过bookTicker估算真实滑点成本
- **费率趋势分析** - 检查费率是在强化还是均值回归
- **成交量门槛** - 确保最低24h成交量(默认5000万USDT)保证执行质量
- **实时P&L追踪** - 每轮和累计预估P&L日志
- **多采样时间同步** - 3次采样取最低延迟，实现微秒级精度
- **指数退避重试** - 平仓失败最多重试3次(0.5s/1s/2s退避)
- **双向交易** - 同时捕获负费率(做多)和正费率(做空)机会

## 交易策略

### 核心机制

```
资金费率结算时间线:

  t-3分钟         t-2秒          t=0            t+0.5秒
    |               |             |               |
    v               v             v               v
  预扫描          开仓          结算            平仓
  (过滤&         (并行         (收取           (并行
   评分)         市价单)       资金费)         极速平仓)
```

### 量化过滤管线

```
所有USDT永续合约 (~300+交易对)
        |
        v
[1] 费率门槛: |资金费率| >= 0.05%           --> 约10-30个通过
        |
        v
[2] 成交量门槛: 24h成交量 >= 5000万USDT     --> 约10-20个通过
        |
        v
[3] 价差检查: 买卖价差 <= 0.1%              --> 约8-15个通过
        |
        v
[4] 净利润: 费率 - 2×手续费 - 价差 > 0.01%  --> 约3-8个通过
        |
        v
[5] 多因子评分 & 排序                       --> 选取Top N
        |
        v
[6] 动态仓位计算                           --> 执行交易
```

### 多因子评分模型

每个候选获得综合评分:

```
score = 净利润率 × (1 + 趋势加成) × 流动性因子

- 净利润率:    |资金费率| - 2×taker手续费 - 价差成本
- 趋势加成:    [-20%, +20%] 基于近期费率方向
- 流动性因子:  对数标度的24h成交量 (0.5x-1.5x)
```

### 入场条件 (全部通过才入场)

| 过滤器 | 阈值 | 目的 |
|--------|------|------|
| 资金费率 | \|费率\| >= 0.05% | 最低毛收益 |
| 24h成交量 | >= 5000万 USDT | 流动性/执行质量 |
| 买卖价差 | <= 0.1% | 滑点成本控制 |
| 净利润率 | >= 0.01% | 扣除成本后正期望值 |
| 无现有持仓 | 是 | 避免重复暴露 |
| 不在黑名单 | 是 | 手动排除过滤 |

### 动态仓位管理

```
置信度 = 净利润率 / 最小净利润率阈值
调整因子 = clamp(置信度, 0.5, 2.0)
仓位大小 = 基础金额 × 调整因子

示例: 基础=200 USDT, 净利润3倍阈值 -> 400 USDT仓位
示例: 基础=200 USDT, 净利润刚过阈值 -> 100 USDT仓位
```

## 系统架构

```
┌─────────────────────────────────────────────────┐
│           AutoTradingBot v3.0                   │
├─────────────────────────────────────────────────┤
│  量化分析管线:                                   │
│  ┌───────────┐  ┌────────────┐  ┌───────────┐  │
│  │ 费率门槛  │→│ 成本过滤器 │→│ 多因子    │  │
│  │ + 成交量  │  │ 价差+手续费│  │ 评分器    │  │
│  │   门槛    │  │ 净利润计算 │  │           │  │
│  └───────────┘  └────────────┘  └───────────┘  │
│                                                 │
│  执行引擎:                                       │
│  ┌───────────┐  ┌────────────┐  ┌───────────┐  │
│  │ 动态仓位  │→│ 并行开/平仓│→│ P&L追踪  │  │
│  └───────────┘  └────────────┘  └───────────┘  │
│                                                 │
│  基础设施:                                       │
│  ┌───────────┐  ┌────────────┐  ┌───────────┐  │
│  │ 多采样    │  │ 指数退避   │  │ Ticker   │  │
│  │ 时间同步  │  │ 重试机制   │  │ 缓存(60s)│  │
│  └───────────┘  └────────────┘  └───────────┘  │
└─────────────────────────────────────────────────┘
                      │
              ┌───────┴───────┐
              │ BinanceFutures│
              │     API       │
              └───────────────┘
```

## 快速开始

### 环境要求

- Python 3.8+
- 币安合约账户
- API密钥(需要合约交易权限)

### 1. 克隆和安装

```bash
git clone https://github.com/your-username/binance-tradingbot.git
cd binance-tradingbot
pip3 install -r requirements.txt
```

### 2. 配置

创建 `.env` 文件:
```env
# 币安API配置(必需)
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here

# 基础交易参数
TRADE_AMOUNT=200
LEVERAGE=1
MAX_POSITIONS=5

# 时机控制
OPEN_BEFORE_SECONDS=2
CLOSE_AFTER_SECONDS=0.5
PRE_SCAN_MINUTES=3

# v3.0 量化增强参数
MIN_FUNDING_RATE=0.0005
MIN_NET_PROFIT_RATE=0.0001
MAX_SPREAD_RATIO=0.001
MIN_VOLUME_USDT=50000000
DYNAMIC_SIZING=true

# 可选
BLACKLIST_SYMBOLS=
```

### 3. 设置保证金模式

```bash
python3 setup_margin_modes.py
```

### 4. 启动

```bash
# 交互式运行
python3 auto_trading_bot.py

# 后台守护进程
./start_bot.sh
```

## 配置说明

### 基础参数

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `TRADE_AMOUNT` | 100 | 基础仓位大小(USDT) |
| `LEVERAGE` | 20 | 杠杆倍数 |
| `MAX_POSITIONS` | 5 | 最大同时持仓数 |
| `OPEN_BEFORE_SECONDS` | 2 | 结算前N秒开仓 |
| `CLOSE_AFTER_SECONDS` | 0.5 | 结算后N秒平仓 |
| `PRE_SCAN_MINUTES` | 3 | 结算前N分钟预扫描 |

### v3.0 量化参数

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `MIN_FUNDING_RATE` | 0.0005 | 最小\|费率\|粗筛阈值(0.05%) |
| `MIN_NET_PROFIT_RATE` | 0.0001 | 扣除费用后最小净利润率(0.01%) |
| `MAX_SPREAD_RATIO` | 0.001 | 最大可接受买卖价差(0.1%) |
| `MIN_VOLUME_USDT` | 50000000 | 最低24h成交量(5000万USDT) |
| `DYNAMIC_SIZING` | true | 开启Kelly启发式动态仓位 |
| `BLACKLIST_SYMBOLS` | (空) | 逗号分隔的排除交易对 |

### 命令行参数

```bash
python3 auto_trading_bot.py --help

可选参数:
  --amount AMOUNT         每次交易金额(USDT)
  --leverage LEVERAGE     杠杆倍数
  --min-rate RATE         最小资金费率阈值
  --max-positions N       最大同时持仓数
  --open-before SEC       结算前N秒开仓
  --close-after SEC       结算后N秒平仓
  --testnet               使用测试网
```

## 使用方法

### 方式一: 脚本管理(推荐)

```bash
./start_bot.sh     # 启动后台守护进程
./check_bot.sh     # 检查运行状态
./stop_bot.sh      # 优雅停止
```

### 方式二: 交互式运行

```bash
python3 auto_trading_bot.py --amount 200 --leverage 2 --max-positions 5
```

### 方式三: 后台运行

```bash
nohup python3 run_auto_trading.py > trading.log 2>&1 &
```

### 方式四: 账户监控

```bash
python3 main.py    # 交互式账户面板
```

## 项目结构

```
binance_tradingbot/
├── main.py                    # 核心: API客户端 + AutoTradingBot v3.0
├── auto_trading_bot.py        # 交互式启动脚本(CLI参数)
├── run_auto_trading.py        # 后台守护模式启动
├── setup_margin_modes.py      # 批量保证金模式设置
├── debug_position_check.py    # 持仓检查调试工具
├── test_new_strategy.py       # 策略验证测试
├── start_bot.sh               # 后台启动脚本
├── stop_bot.sh                # 进程终止脚本
├── check_bot.sh               # 状态监控脚本
├── requirements.txt           # Python依赖
├── .env                       # 配置(API密钥 + 参数)
└── logs/                      # 运行日志
    ├── bot.pid                # 进程ID
    └── trading_bot_*.log      # 带时间戳的交易日志
```

## 监控管理

### 实时日志

```bash
tail -f logs/trading_bot_*.log
```

### 关键日志事件

| 日志模式 | 含义 |
|---------|------|
| `🔍 粗筛通过: N 个候选` | N个交易对通过费率+成交量门槛 |
| `🎯 找到 N 个套利候选` | N个交易对通过完整量化过滤 |
| `🚀🚀🚀 开仓!` | 并行市价开仓执行中 |
| `🔻🔻🔻 平仓!` | 并行极速平仓执行中 |
| `💰 本轮P&L估算` | 每轮预估利润明细 |
| `📊 累计N轮` | 累计会话P&L |
| `⚡ 开仓耗时: Nms` | 执行延迟测量 |

### P&L追踪

机器人记录每轮预估P&L:

```
💰 本轮P&L估算: 资金费≈0.1200, 手续费≈0.0800, 净利≈0.0400 USDT
📊 累计12轮: 估算净利≈0.4800 USDT
```

## 风险提示

### 交易风险

- **市场风险**: 在约2.5秒持仓窗口内价格可能不利变动
- **杠杆风险**: 放大盈亏
- **费率风险**: 费率可能在扫描和结算之间变化
- **执行风险**: 网络延迟或API错误可能阻止及时平仓
- **价差风险**: 流动性不足的市场价差可能大于预估

### 最佳实践

1. 小额起步验证配置
2. 使用保守杠杆(建议1-3倍)
3. 定期监控日志
4. 准备手动止损方案
5. 不要投入超过承受范围的资金

### 免责声明

本项目仅供学习和研究使用，不构成投资建议。使用者需承担所有交易风险，作者不对任何损失负责。

## 故障排除

### 常见问题

1. **API连接失败**
   ```bash
   python3 -c "from main import BinanceFuturesAPI; api = BinanceFuturesAPI(); print('连接成功')"
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

### 调试命令

```bash
# 测试API连接
python3 -c "from main import BinanceFuturesAPI; api = BinanceFuturesAPI(); print('API连接成功')"

# 检查黑名单
python3 -c "from main import AutoTradingBot; bot = AutoTradingBot(); bot.debug_blacklist()"

# 查看资金费率
python3 -c "from main import BinanceFuturesAPI; api = BinanceFuturesAPI(); api.debug_funding_rates()"
```
