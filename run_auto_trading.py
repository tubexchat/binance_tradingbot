#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资金费率套利机器人 - 后台运行模式
使用方法: nohup python3 run_auto_trading.py > trading.log 2>&1 &
"""

import os
import sys
import logging
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import AutoTradingBot

load_dotenv()

def main():
    """直接启动资金费率套利机器人"""

    print("🤖 资金费率套利机器人 - 后台运行模式")
    print("=" * 50)

    try:
        use_testnet = os.getenv('USE_TESTNET', 'false').lower() == 'true'

        bot = AutoTradingBot(testnet=use_testnet)

        # 参数从环境变量读取（已在AutoTradingBot.__init__中处理）
        print(f"💰 每笔金额: {bot.trade_amount} USDT")
        print(f"⚡ 杠杆倍数: {bot.leverage}x")
        print(f"📊 最小费率: {bot.min_funding_rate*100:.3f}%")
        print(f"🕐 开仓时机: 结算前 {bot.open_before_seconds}秒")
        print(f"🕐 平仓时机: 结算后 {bot.close_after_seconds}秒")
        print(f"📦 最大持仓: {bot.max_positions}个")
        print(f"🌐 测试网: {'是' if use_testnet else '否'}")
        print("=" * 50)

        print(f"\n🚀 启动时间: {os.popen('date').read().strip()}")
        print("📋 策略: 结算前开仓 → 吃资金费 → 结算后极速平仓")
        print("按 Ctrl+C 或发送SIGTERM停止机器人\n")

        bot.start_monitoring()

    except KeyboardInterrupt:
        print("\n🛑 收到停止信号，机器人已停止")
    except Exception as e:
        print(f"❌ 机器人出错: {e}")
        logging.error(f"机器人出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
