#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的交易策略逻辑
验证1小时资金费率结算检查和持仓条件检查功能
"""

import os
import sys
from main import AutoTradingBot, logging

def test_hourly_funding_check():
    """测试1小时资金费率结算检查功能"""
    print("🔍 测试1小时资金费率结算检查功能...")
    
    try:
        # 创建机器人实例
        bot = AutoTradingBot(testnet=False)
        
        # 测试一些常见的交易对
        test_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT']
        
        print(f"\n📊 测试 {len(test_symbols)} 个交易对的1小时资金费率结算:")
        for symbol in test_symbols:
            try:
                has_hourly = bot.check_hourly_funding(symbol)
                status = "✅ 有1小时结算" if has_hourly else "❌ 无1小时结算"
                print(f"  {symbol}: {status}")
            except Exception as e:
                print(f"  {symbol}: ❌ 检查失败 - {e}")
        
        print("\n✅ 1小时资金费率结算检查测试完成")
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

def test_position_conditions_check():
    """测试持仓条件检查功能"""
    print("\n🔍 测试持仓条件检查功能...")
    
    try:
        # 创建机器人实例
        bot = AutoTradingBot(testnet=False)
        
        # 获取当前持仓
        positions = bot.api.get_positions()
        if not positions:
            print("📝 当前没有持仓，无法测试持仓条件检查")
            return
        
        # 过滤有效持仓
        active_positions = []
        for position in positions:
            position_amt = float(position.get('positionAmt', 0))
            if abs(position_amt) > 0:
                active_positions.append(position)
        
        if not active_positions:
            print("📝 当前没有有效持仓，无法测试持仓条件检查")
            return
        
        print(f"\n📊 检查 {len(active_positions)} 个持仓的条件:")
        for position in active_positions:
            symbol = position.get('symbol', '')
            position_amt = float(position.get('positionAmt', 0))
            side = "做空" if position_amt < 0 else "做多"
            
            print(f"\n  📍 {symbol} ({side} {abs(position_amt)}):")
            
            # 只检查多头持仓
            if position_amt > 0:
                is_valid, reason = bot.check_position_conditions(symbol)
                status = "✅ 符合条件" if is_valid else f"❌ 不符合条件: {reason}"
                print(f"    {status}")
            else:
                print(f"    🔴 空头持仓，跳过检查")
        
        print("\n✅ 持仓条件检查测试完成")
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

def test_long_candidates():
    """测试做多候选合约筛选功能"""
    print("\n🔍 测试做多候选合约筛选功能...")
    
    try:
        # 创建机器人实例
        bot = AutoTradingBot(testnet=False)
        
        print("📊 开始筛选做多候选合约...")
        candidates = bot.get_long_candidates()
        
        if candidates:
            print(f"\n✅ 找到 {len(candidates)} 个做多候选合约:")
            for i, symbol in enumerate(candidates, 1):
                print(f"  {i}. {symbol}")
        else:
            print("\n📝 当前没有符合条件的做多候选合约")
        
        print("\n✅ 做多候选合约筛选测试完成")
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

def main():
    """主测试函数"""
    print("🚀 新交易策略逻辑测试")
    print("=" * 50)
    
    print("\n📋 新策略说明:")
    print("🔍 做多筛选条件:")
    print("   • 资金费率: < -0.1%")
    print("   • 24小时交易量: > 6000万USDT")
    print("   • MACD日级慢线: > 0")
    print("   • 多空比: < 1")
    print("   • 24小时涨幅: > 0")
    print("   • 资金费率结算时间: 1小时")
    print("   • 剔除资金费率为0的合约")
    print("📈 平仓策略: 当持仓合约不符合条件时自动平仓")
    
    print("\n" + "=" * 50)
    
    # 测试1小时资金费率结算检查
    test_hourly_funding_check()
    
    # 测试持仓条件检查
    test_position_conditions_check()
    
    # 测试做多候选合约筛选
    test_long_candidates()
    
    print("\n" + "=" * 50)
    print("✅ 所有测试完成")

if __name__ == "__main__":
    main()
