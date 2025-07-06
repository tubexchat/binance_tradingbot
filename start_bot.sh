#!/bin/bash

echo "🚀 启动Binance自动化交易机器人"
echo "================================"

# 检查是否存在.env文件
if [ ! -f ".env" ]; then
    echo "❌ 错误: 未找到.env文件，请确保API密钥已配置"
    exit 1
fi

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到python3"
    exit 1
fi

# 检查 run_auto_trading.py 是否存在
if [ ! -f "run_auto_trading.py" ]; then
    echo "❌ 错误: 未找到run_auto_trading.py文件"
    exit 1
fi

# 检查机器人是否已经在运行
if [ -f "logs/bot.pid" ]; then
    PID=$(cat logs/bot.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "⚠️  机器人已经在运行 (PID: $PID)"
        echo "🛑 如需重启，请先运行: ./stop_bot.sh"
        exit 1
    else
        echo "🧹 清理旧的PID文件..."
        rm -f logs/bot.pid
    fi
fi

# 创建logs目录
mkdir -p logs

# 生成日志文件名
LOG_FILE="logs/trading_bot_$(date +%Y%m%d_%H%M%S).log"

echo "📝 日志文件: $LOG_FILE"
echo "📝 进程ID文件: logs/bot.pid"
echo ""
echo "🤖 程序将在后台运行，即使SSH连接断开也会继续..."

# 使用nohup运行 run_auto_trading.py
nohup python3 run_auto_trading.py > "$LOG_FILE" 2>&1 &

# 保存进程ID
echo $! > logs/bot.pid

# 等待一下确保进程启动
sleep 2

# 检查进程是否成功启动
PID=$(cat logs/bot.pid)
if ps -p $PID > /dev/null 2>&1; then
    echo "✅ 机器人已成功启动!"
    echo "📊 查看实时日志: tail -f $LOG_FILE"
    echo "🛑 停止机器人: ./stop_bot.sh"
    echo "🔍 检查状态: ./check_bot.sh"
    echo ""
    echo "📋 配置说明:"
    echo "   - 交易参数通过.env文件配置"
    echo "   - 支持的环境变量: TRADE_AMOUNT, LEVERAGE, FUNDING_THRESHOLD等"
    echo "   - 详细策略信息请查看日志文件"
else
    echo "❌ 机器人启动失败，请检查日志文件: $LOG_FILE"
    rm -f logs/bot.pid
    exit 1
fi 