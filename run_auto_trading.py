#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门用于后台运行的自动化交易脚本
使用方法: nohup python3 run_auto_trading.py > trading.log 2>&1 &
"""

import os
import sys
import logging
from dotenv import load_dotenv

# 确保能导入main模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import AutoTradingBot

# 加载环境变量
load_dotenv()

def main():
    """直接启动自动化交易机器人"""
    
    print("🤖 Binance自动化交易机器人 - 后台运行模式")
    print("=" * 50)
    
    try:
        # 从环境变量获取配置，如果没有则使用默认值
        trade_amount = float(os.getenv('TRADE_AMOUNT', '100'))
        leverage = int(os.getenv('LEVERAGE', '2'))
        funding_threshold = float(os.getenv('FUNDING_THRESHOLD', '-0.001'))
        close_threshold = float(os.getenv('CLOSE_THRESHOLD', '0'))
        monitor_interval = int(os.getenv('MONITOR_INTERVAL', '300'))
        position_check_interval = int(os.getenv('POSITION_CHECK_INTERVAL', '300'))
        use_testnet = os.getenv('USE_TESTNET', 'false').lower() == 'true'
        
        print(f"交易金额: {trade_amount} USDT")
        print(f"杠杆倍数: {leverage}x")
        print(f"监控间隔: {monitor_interval}秒")
        print(f"持仓检查间隔: {position_check_interval}秒")
        print(f"测试网模式: {'是' if use_testnet else '否'}")
        print("=" * 50)
        
        print("\n📋 交易策略:")
        print("📊 基于负资金费率+MACD+多空比的做多策略:")
        print("🔍 筛选条件:")
        print("   • 资金费率: < -0.1%")
        print("   • 24小时交易量: > 6000万USDT")
        print("   • MACD日级慢线: > 0")
        print("   • 多空比: < 1")
        print("   • 24小时涨幅: > 0")
        print("   • 资金费率结算时间: 1小时")
        print("   • 剔除资金费率为0的合约")
        print("🟢 做多信号: 满足以上所有条件")
        print("📈 平仓策略: 独立监控线程每5分钟检查持仓，当持仓合约不符合条件时自动平仓")
        
        print("\n🔥 重要提醒: 保证金模式设置")
        print("⚠️  机器人假设所有交易对已设置为全仓(CROSSED)模式")
        print("📋 如需设置，请运行: python3 setup_margin_modes.py")
        print("💡 或在币安网页/APP中手动设置为全仓模式")
        
        print(f"\n🚀 启动时间: {os.popen('date').read().strip()}")
        print("🤖 机器人正在启动...")
        
        # 初始化自动化交易机器人
        bot = AutoTradingBot(testnet=use_testnet)
        bot.trade_amount = trade_amount
        bot.leverage = leverage
        # 注意：新策略不再需要funding_rate_threshold，直接使用负资金费率
        bot.monitor_interval = monitor_interval
        bot.position_check_interval = position_check_interval
        
        print("✅ 机器人初始化完成，开始监控...")
        print("按 Ctrl+C 或发送SIGTERM信号停止机器人\n")
        
        # 开始监控
        bot.start_monitoring()
        
    except KeyboardInterrupt:
        print("\n🛑 收到停止信号，自动化交易机器人已停止")
    except Exception as e:
        print(f"❌ 自动化交易机器人出错: {e}")
        logging.error(f"自动化交易机器人出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 