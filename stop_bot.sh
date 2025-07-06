#!/bin/bash

echo "🛑 停止Binance自动化交易机器人"
echo "==============================="

# 检查PID文件是否存在
if [ ! -f "logs/bot.pid" ]; then
    echo "❌ 未找到PID文件，机器人可能未运行"
    echo "💡 提示: 使用 ./start_bot.sh 启动机器人"
    exit 1
fi

# 读取PID
PID=$(cat logs/bot.pid)

# 检查进程是否存在
if ps -p $PID > /dev/null 2>&1; then
    echo "🔍 找到机器人进程 (PID: $PID)"
    
    # 发送TERM信号尝试优雅停止
    echo "📤 发送停止信号 (SIGTERM)..."
    kill -TERM $PID
    
    # 等待5秒让进程优雅退出
    echo "⏳ 等待进程优雅退出..."
    sleep 5
    
    # 检查进程是否仍然存在
    if ps -p $PID > /dev/null 2>&1; then
        echo "⚠️  进程仍在运行，强制终止 (SIGKILL)..."
        kill -KILL $PID
        sleep 2
    fi
    
    # 再次检查
    if ps -p $PID > /dev/null 2>&1; then
        echo "❌ 无法停止进程，请手动检查"
        echo "💡 尝试: kill -9 $PID"
        exit 1
    else
        echo "✅ 机器人已成功停止"
        rm -f logs/bot.pid
        echo "🧹 已清理PID文件"
    fi
else
    echo "❌ 机器人进程不存在 (PID: $PID)"
    echo "🧹 清理无效的PID文件..."
    rm -f logs/bot.pid
    echo "✅ 清理完成"
fi

echo ""
echo "💡 提示: 使用 ./start_bot.sh 重新启动机器人" 