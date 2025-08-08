#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化合约交易机器人
功能:
1. 做多策略: 资金费率结算时间为1小时 + 当前没有持仓 + 资金费率小于-0.1%
2. 平仓策略: 独立监控线程每5分钟检查持仓，资金费率大于-0.1%时自动平仓
3. 黑名单功能: 可在.env文件中设置BLACKLIST_SYMBOLS排除特定币种
"""

import os
import argparse
from main import AutoTradingBot, logging
import time

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='自动化合约交易机器人')
    parser.add_argument('--amount', type=float, default=100, help='每次交易金额(USDT，默认100)')
    parser.add_argument('--leverage', type=int, default=20, help='杠杆倍数(默认20)')
    parser.add_argument('--interval', type=int, default=300, help='监控间隔(秒，默认300)')
    parser.add_argument('--position-check-interval', type=int, default=300, help='持仓检查间隔(秒，默认300)')
    parser.add_argument('--testnet', action='store_true', help='使用测试网')
    
    args = parser.parse_args()
    
    print("🚀 自动化合约交易机器人")
    print("==" * 30)
    print(f"交易金额: {args.amount} USDT")
    print(f"杠杆倍数: {args.leverage}x")
    print(f"监控间隔: {args.interval}秒")
    print(f"持仓检查间隔: {args.position_check_interval}秒")
    print(f"测试网模式: {'是' if args.testnet else '否'}")
    
    # 检查黑名单设置
    blacklist = os.getenv('BLACKLIST_SYMBOLS', '')
    if blacklist:
        print(f"🚫 黑名单币种: {blacklist}")
    else:
        print("📝 提示: 可在.env文件中设置BLACKLIST_SYMBOLS来排除特定币种")
    
    print("==" * 30)
    
    print("\n📋 交易策略:")
    print("📊 做多策略:")
    print("🔍 买入条件:")
    print("   • 资金费率结算时间: 1小时")
    print("   • 当前没有持仓")
    print("   • 资金费率: < -0.1%")
    print("🟢 做多信号: 满足以上所有条件")
    print("📈 平仓策略: 独立监控线程每5分钟检查持仓，资金费率大于-0.1%时自动平仓")
    print("⏰ 扫描频率: 每5分钟扫描一次")
    
    print("\n⚠️  风险提示: 自动化交易机器人将使用真实资金进行交易!")
    print("确保您已经:")
    print("1. 在.env文件中设置了具有交易权限的API密钥")
    print("2. 理解交易风险和策略逻辑")
    print("3. 设置了合适的交易金额和杠杆")
    print("4. 🔥 [重要] 已将所有交易对设置为全仓(CROSSED)模式")
    print("")
    print("📋 保证金模式设置:")
    print("  • 如需批量设置全仓模式，请先运行：python3 setup_margin_modes.py")
    print("  • 或在币安网页/APP中手动设置为全仓模式")
    print("  • ⚠️  有持仓时无法更改保证金模式，需先平仓！")
    
    if not args.testnet:
        confirm = input("\n是否确认启动自动化交易机器人? (输入 'YES' 确认): ").strip()
        if confirm != 'YES':
            print("❌ 已取消启动自动化交易机器人")
            return
    
    try:
        # 创建交易机器人实例
        bot = AutoTradingBot(testnet=args.testnet)
        
        # 设置交易参数
        bot.trade_amount = args.amount
        bot.leverage = args.leverage
        bot.monitor_interval = args.interval
        bot.position_check_interval = args.position_check_interval
        
        print("🔧 正在启动交易机器人...")
        
        # 启动监控
        bot.start_monitoring()
        
        print("✅ 交易机器人已启动!")
        print("按 Ctrl+C 停止机器人")
        
        # 保持程序运行
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 收到停止信号，正在关闭交易机器人...")
            bot.stop_monitoring()
            print("✅ 交易机器人已安全停止")
            
    except Exception as e:
        logging.error(f"启动交易机器人失败: {e}")
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    main() 