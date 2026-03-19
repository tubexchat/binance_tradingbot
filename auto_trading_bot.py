#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资金费率套利机器人
策略: 结算前2秒开仓 → 吃资金费 → 结算后0.5秒极速平仓
"""

import os
import argparse
from main import AutoTradingBot, logging
import time

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='资金费率套利机器人')
    parser.add_argument('--amount', type=float, default=None, help='每笔交易金额(USDT)')
    parser.add_argument('--leverage', type=int, default=None, help='杠杆倍数')
    parser.add_argument('--min-rate', type=float, default=None, help='最小资金费率绝对值(如0.0005=0.05%%)')
    parser.add_argument('--open-before', type=float, default=None, help='结算前N秒开仓(默认2)')
    parser.add_argument('--close-after', type=float, default=None, help='结算后N秒平仓(默认0.5)')
    parser.add_argument('--max-positions', type=int, default=None, help='最大同时持仓数(默认5)')
    parser.add_argument('--testnet', action='store_true', help='使用测试网')

    args = parser.parse_args()

    print("🚀 资金费率套利机器人")
    print("=" * 50)
    print("📋 策略: 结算前开仓 → 吃资金费 → 结算后极速平仓")
    print()

    # 检查黑名单设置
    blacklist = os.getenv('BLACKLIST_SYMBOLS', '')
    if blacklist:
        print(f"🚫 黑名单币种: {blacklist}")

    print()
    print("⚠️  风险提示: 将使用真实资金进行交易!")
    print("确保您已经:")
    print("1. 在.env文件中设置了具有交易权限的API密钥")
    print("2. 理解资金费率套利策略和风险")
    print("3. 已将交易对设置为全仓(CROSSED)模式")
    print("   (运行 python3 setup_margin_modes.py 批量设置)")

    if not args.testnet:
        confirm = input("\n是否确认启动? (输入 'YES' 确认): ").strip()
        if confirm != 'YES':
            print("❌ 已取消启动")
            return

    try:
        bot = AutoTradingBot(testnet=args.testnet)

        # 覆盖参数（命令行 > 环境变量 > 默认值）
        if args.amount is not None:
            bot.trade_amount = args.amount
        if args.leverage is not None:
            bot.leverage = args.leverage
        if args.min_rate is not None:
            bot.min_funding_rate = args.min_rate
        if args.open_before is not None:
            bot.open_before_seconds = args.open_before
        if args.close_after is not None:
            bot.close_after_seconds = args.close_after
        if args.max_positions is not None:
            bot.max_positions = args.max_positions

        print()
        print(f"💰 每笔金额: {bot.trade_amount} USDT")
        print(f"⚡ 杠杆倍数: {bot.leverage}x")
        print(f"📊 最小费率: {bot.min_funding_rate*100:.3f}%")
        print(f"🕐 开仓时机: 结算前 {bot.open_before_seconds}秒")
        print(f"🕐 平仓时机: 结算后 {bot.close_after_seconds}秒")
        print(f"📦 最大持仓: {bot.max_positions}个")
        print(f"🌐 测试网: {'是' if args.testnet else '否'}")
        print("=" * 50)
        print("按 Ctrl+C 停止机器人\n")

        bot.start_monitoring()

    except KeyboardInterrupt:
        print("\n🛑 收到停止信号，正在关闭...")
        bot.stop_monitoring()
        print("✅ 机器人已安全停止")
    except Exception as e:
        logging.error(f"启动失败: {e}")
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    main()
