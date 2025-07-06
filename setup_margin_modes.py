#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
保证金模式设置工具
用于在启动交易机器人前批量设置交易对为全仓模式

使用方法：
python3 setup_margin_modes.py

重要说明：
- 此工具只能在没有持仓时设置保证金模式
- 如果某个交易对已有持仓，需要先平仓再设置
- 建议在首次使用交易机器人前运行此工具
"""

import os
import sys
from typing import List
from dotenv import load_dotenv

# 确保能导入main模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import AutoTradingBot

# 加载环境变量
load_dotenv()

def main():
    """设置保证金模式主函数"""
    
    print("🔧 Binance合约保证金模式设置工具")
    print("=" * 60)
    print("⚠️  重要提醒：")
    print("  • 只能在没有持仓时设置保证金模式")
    print("  • 如果有持仓，请先平仓再运行此工具")
    print("  • 建议在首次使用交易机器人前运行")
    print("=" * 60)
    
    # 选择运行模式
    use_testnet = input("\n是否使用测试网？(y/n): ").lower().strip() == 'y'
    
    try:
        # 初始化机器人
        print("\n🔧 初始化API连接...")
        bot = AutoTradingBot(testnet=use_testnet)
        
        # 默认要设置的交易对
        default_symbols = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT', 'XRPUSDT',
            'DOGEUSDT', 'DOTUSDT', 'MATICUSDT', 'AVAXUSDT', 'LINKUSDT', 'LTCUSDT',
            'ATOMUSDT', 'FILUSDT', 'TRXUSDT', 'EOSUSDT', 'XLMUSDT', 'VETUSDT',
            'THETAUSDT', 'ALGOUSDT', 'KSMUSDT', 'WAVESUSDT'
        ]
        
        print(f"\n📋 将为以下 {len(default_symbols)} 个交易对设置全仓模式：")
        for i, symbol in enumerate(default_symbols, 1):
            print(f"  {i:2d}. {symbol}")
        
        # 用户确认
        custom_input = input(f"\n是否使用默认列表？(y/n，n=自定义): ").lower().strip()
        
        symbols_to_set = default_symbols
        if custom_input == 'n':
            custom_symbols = input("请输入交易对列表（用逗号分隔，如 BTCUSDT,ETHUSDT）: ").strip()
            if custom_symbols:
                symbols_to_set = [s.strip().upper() for s in custom_symbols.split(',')]
                # 确保都以USDT结尾
                symbols_to_set = [s if s.endswith('USDT') else s + 'USDT' for s in symbols_to_set]
        
        print(f"\n🚀 开始为 {len(symbols_to_set)} 个交易对设置全仓模式...")
        print("=" * 60)
        
        # 执行批量设置
        results = bot.setup_margin_modes(symbols_to_set)
        
        # 统计结果
        success_symbols = [symbol for symbol, success in results.items() if success]
        failed_symbols = [symbol for symbol, success in results.items() if not success]
        
        print("\n" + "=" * 60)
        print("📊 设置结果统计:")
        print(f"✅ 成功: {len(success_symbols)}/{len(symbols_to_set)} 个交易对")
        print(f"❌ 失败: {len(failed_symbols)}/{len(symbols_to_set)} 个交易对")
        
        if failed_symbols:
            print(f"\n❌ 设置失败的交易对：")
            for symbol in failed_symbols:
                print(f"  • {symbol}")
            print("\n💡 失败原因可能是：")
            print("  • 该交易对存在持仓（需要先平仓）")
            print("  • API权限不足")
            print("  • 交易对不存在或已下线")
        
        print("\n🎯 下一步操作：")
        print("1. 如有失败的交易对，请先平仓后重新运行此工具")
        print("2. 确认所有需要的交易对都设置为全仓模式后")
        print("3. 再启动自动化交易机器人")
        
    except Exception as e:
        print(f"\n❌ 设置过程出错: {e}")
        print("\n🔍 可能的解决方案：")
        print("1. 检查.env文件中的API密钥是否正确")
        print("2. 确认API密钥有合约交易权限")
        print("3. 检查网络连接是否正常")

if __name__ == "__main__":
    main() 