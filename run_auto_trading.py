#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整点做空策略 - 后台运行脚本
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
    """直接启动整点做空策略机器人"""

    print("🤖 整点做空策略机器人 - 后台运行模式")
    print("=" * 50)

    try:
        trade_amount = float(os.getenv('TRADE_AMOUNT', '100'))
        leverage = int(os.getenv('LEVERAGE', '20'))
        take_profit_pct = float(os.getenv('TAKE_PROFIT_PCT', '2.0')) / 100.0
        position_check_interval = int(os.getenv('POSITION_CHECK_INTERVAL', '30'))
        use_testnet = os.getenv('USE_TESTNET', 'false').lower() == 'true'

        print(f"交易金额: {trade_amount} USDT")
        print(f"杠杆倍数: {leverage}x")
        print(f"止盈比例: {take_profit_pct*100:.0f}%")
        print(f"持仓检查间隔: {position_check_interval}秒")
        print(f"测试网模式: {'是' if use_testnet else '否'}")
        print("=" * 50)

        print("\n📋 交易策略:")
        print("🔴 做空: 整点时开空（资金费率 < -0.1% + 无持仓）")
        print("🟢 止盈: 收益 >= 2% | 🛑 止损: 亏损 >= 2%")

        print("\n🔥 重要提醒: 保证金模式设置")
        print("⚠️  机器人假设所有交易对已设置为全仓(CROSSED)模式")
        print("📋 如需设置，请运行: python3 setup_margin_modes.py")

        print(f"\n🚀 启动时间: {os.popen('date').read().strip()}")
        print("🤖 机器人正在启动...")

        bot = AutoTradingBot(testnet=use_testnet)
        bot.trade_amount = trade_amount
        bot.leverage = leverage
        bot.take_profit_pct = take_profit_pct
        bot.position_check_interval = position_check_interval

        print("✅ 机器人初始化完成，开始监控...")
        print("按 Ctrl+C 或发送SIGTERM信号停止机器人\n")

        bot.start_monitoring()

    except KeyboardInterrupt:
        print("\n🛑 收到停止信号，机器人已停止")
    except Exception as e:
        print(f"❌ 机器人出错: {e}")
        logging.error(f"机器人出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
