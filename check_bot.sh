#!/bin/bash

echo "🔍 检查Binance自动化交易机器人状态"
echo "=================================="

# 检查PID文件是否存在
if [ ! -f "logs/bot.pid" ]; then
    echo "❌ 机器人未运行 (未找到PID文件)"
    exit 1
fi

# 读取PID
PID=$(cat logs/bot.pid)

# 检查进程是否存在
if ps -p $PID > /dev/null; then
    echo "✅ 机器人正在运行"
    echo "📊 进程ID: $PID"
    
    # 显示进程信息
    echo "📈 进程详情:"
    ps -p $PID -o pid,ppid,cmd,etime,pcpu,pmem
    
    # 显示最新日志
    echo ""
    echo "📝 最新日志 (最后10行):"
    echo "------------------------"
    
    # 查找最新的日志文件
    LATEST_LOG=$(ls -t logs/trading_bot_*.log 2>/dev/null | head -1)
    if [ -n "$LATEST_LOG" ]; then
        tail -10 "$LATEST_LOG"
        echo ""
        echo "📁 完整日志文件: $LATEST_LOG"
        echo "📊 实时查看日志: tail -f $LATEST_LOG"
    else
        echo "❌ 未找到日志文件"
    fi
else
    echo "❌ 机器人进程不存在 (PID: $PID)"
    echo "🔧 清理PID文件..."
    rm -f logs/bot.pid
fi 