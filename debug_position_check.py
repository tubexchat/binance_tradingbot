#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试持仓检查功能的脚本
"""

import os
from main import AutoTradingBot, logging

def debug_position_check():
    """调试持仓检查功能"""
    print("🔍 开始调试持仓检查功能...")
    
    try:
        # 创建机器人实例
        bot = AutoTradingBot(testnet=False)
        
        print("\n📊 获取当前所有持仓...")
        positions = bot.api.get_positions()
        
        # 过滤有效持仓
        active_positions = []
        for position in positions:
            position_amt = float(position.get('positionAmt', 0))
            if abs(position_amt) > 0:
                active_positions.append(position)
        
        print(f"当前有 {len(active_positions)} 个持仓:")
        for position in active_positions:
            symbol = position.get('symbol', '')
            position_amt = float(position.get('positionAmt', 0))
            unrealized_pnl = float(position.get('unRealizedProfit', 0))
            side = "做空" if position_amt < 0 else "做多"
            
            print(f"  📍 {symbol}: {side} {abs(position_amt)}, 未实现盈亏: {unrealized_pnl:.4f} USDT")
            
            # 测试 has_position 方法
            has_pos = bot.has_position(symbol)
            print(f"     🔍 has_position({symbol}) 返回: {has_pos}")
            
            # 测试 get_position_info 方法
            pos_info = bot.api.get_position_info(symbol)
            if pos_info:
                print(f"     📋 get_position_info 返回的 positionAmt: {pos_info.get('positionAmt', 'N/A')}")
            else:
                print(f"     ❌ get_position_info 返回 None")
        
        if not active_positions:
            print("  📝 当前没有持仓")
            
            # 测试一些常见的交易对
            test_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
            print(f"\n🧪 测试无持仓的交易对的检查结果:")
            for symbol in test_symbols:
                has_pos = bot.has_position(symbol)
                print(f"  🔍 has_position({symbol}) 返回: {has_pos}")
        
        print("\n✅ 持仓检查调试完成")
        
    except Exception as e:
        print(f"❌ 调试过程中出错: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

if __name__ == "__main__":
    debug_position_check() 