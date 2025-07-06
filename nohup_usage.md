# 🤖 Binance自动化交易机器人 - 后台运行指南

## 问题描述
当通过SSH连接服务器运行交易机器人时，一旦SSH连接断开，程序就会终止。这是因为SSH会话结束时会发送SIGHUP信号给所有子进程。

## 解决方案

### 方案一：使用我们提供的脚本（推荐）

#### 1. 启动机器人
```bash
./start_bot.sh
```

#### 2. 检查状态
```bash
./check_bot.sh
```

#### 3. 停止机器人
```bash
./stop_bot.sh
```

#### 4. 查看日志
```bash
# 查看最新日志
tail -f logs/trading_bot_YYYYMMDD_HHMMSS.log

# 查看历史日志
ls logs/
```

### 方案二：手动使用nohup命令

#### 基本用法
```bash
# 后台运行程序
nohup python3 main.py > trading.log 2>&1 &

# 查看进程
ps aux | grep python

# 停止进程
kill [PID]
```

#### 高级用法
```bash
# 使用环境变量配置参数
TRADE_AMOUNT=20 LEVERAGE=3 nohup python3 -c "
from main import AutoTradingBot
bot = AutoTradingBot()
bot.trade_amount = 20
bot.leverage = 3
bot.start_monitoring()
" > trading.log 2>&1 &
```

### 方案三：使用screen或tmux

#### screen方式
```bash
# 创建新会话
screen -S trading_bot

# 运行程序
python3 main.py

# 分离会话 (Ctrl+A, 然后按D)
# 重新连接: screen -r trading_bot
```

#### tmux方式
```bash
# 创建新会话
tmux new-session -d -s trading_bot

# 在会话中运行程序
tmux send-keys -t trading_bot "python3 main.py" Enter

# 查看会话: tmux list-sessions
# 连接会话: tmux attach-session -t trading_bot
```

## 环境变量配置

在`.env`文件中添加以下配置：

```env
# Binance API 配置
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here

# 自动化交易机器人配置
TRADE_AMOUNT=10          # 每次交易金额 (USDT)
LEVERAGE=2              # 杠杆倍数
FUNDING_THRESHOLD=-0.001 # 负资金费率阈值
MONITOR_INTERVAL=300    # 监控间隔 (秒)
```

## 监控和日志

### 日志文件位置
- 主日志：`trading_bot.log`
- 后台运行日志：`logs/trading_bot_YYYYMMDD_HHMMSS.log`
- 进程ID文件：`logs/bot.pid`

### 常用监控命令
```bash
# 实时查看日志
tail -f logs/trading_bot_*.log

# 查看进程状态
ps aux | grep python

# 查看系统资源使用
top -p [PID]

# 查看网络连接
netstat -an | grep python
```

## 注意事项

1. **确保.env文件配置正确**：包含有效的Binance API密钥
2. **监控日志**：定期检查日志文件确保程序正常运行
3. **资源监控**：注意CPU和内存使用情况
4. **网络稳定性**：确保服务器网络连接稳定
5. **安全性**：保护好API密钥，使用最小权限原则

## 故障排除

### 程序无法启动
```bash
# 检查Python环境
python3 --version

# 检查依赖
pip3 install -r requirements.txt

# 检查.env文件
cat .env
```

### 程序异常停止
```bash
# 查看日志
tail -100 logs/trading_bot_*.log

# 检查系统日志
journalctl -u python3

# 检查磁盘空间
df -h
```

### API连接问题
```bash
# 测试网络连接
ping api.binance.com

# 检查防火墙
iptables -L

# 测试API密钥
python3 -c "from main import BinanceFuturesAPI; api = BinanceFuturesAPI(); print(api.get_account_info())"
```

## 推荐最佳实践

1. **使用提供的脚本**：更安全、更易管理
2. **定期备份日志**：避免日志文件过大
3. **设置告警**：通过邮件或短信监控程序状态
4. **定期更新**：保持程序和依赖库最新
5. **分散部署**：不要把所有鸡蛋放在一个篮子里 