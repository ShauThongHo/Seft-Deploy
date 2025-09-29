#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的策略对比分析
"""

import json
import pandas as pd
import numpy as np

# 简化的信号检测逻辑
def get_strategy_thresholds(strategy_mode: str):
    """获取不同策略的信号门槛"""
    if strategy_mode == "conservative":
        return {"buy_threshold": 6, "sell_threshold": 4}  # 需要所有6个条件
    elif strategy_mode == "balanced":
        return {"buy_threshold": 4, "sell_threshold": 3}  # 需要4个条件
    else:  # aggressive
        return {"buy_threshold": 3, "sell_threshold": 2}  # 需要3个条件

def simulate_signals(strategy_mode: str, data_points: int = 1000):
    """模拟信号生成"""
    np.random.seed(42)
    thresholds = get_strategy_thresholds(strategy_mode)
    
    buy_signals = 0
    sell_signals = 0
    
    for _ in range(data_points):
        # 模拟满足条件的数量 (0-6个条件)
        buy_conditions_met = np.random.poisson(3)  # 平均3个条件满足
        sell_conditions_met = np.random.poisson(2)  # 平均2个条件满足
        
        # 限制在0-6范围内
        buy_conditions_met = min(6, max(0, buy_conditions_met))
        sell_conditions_met = min(6, max(0, sell_conditions_met))
        
        # 判断是否触发信号
        if buy_conditions_met >= thresholds["buy_threshold"]:
            buy_signals += 1
        
        if sell_conditions_met >= thresholds["sell_threshold"]:
            sell_signals += 1
    
    return buy_signals, sell_signals

def main():
    print("📊 策略模式对比分析 (简化版)")
    print("=" * 50)
    
    strategies = ["conservative", "balanced", "aggressive"]
    strategy_names = {"conservative": "保守策略", "balanced": "平衡策略", "aggressive": "激进策略"}
    
    print("📈 基于1000个数据点的信号频率对比:")
    print("-" * 50)
    print(f"{'策略类型':<12} {'买入信号':<8} {'卖出信号':<8} {'总信号':<8} {'信号频率'}")
    print("-" * 50)
    
    results = []
    for strategy in strategies:
        buy_signals, sell_signals = simulate_signals(strategy)
        total_signals = buy_signals + sell_signals
        frequency = total_signals / 1000 * 100
        
        results.append({
            'name': strategy_names[strategy],
            'mode': strategy,
            'buy': buy_signals,
            'sell': sell_signals,
            'total': total_signals,
            'frequency': frequency
        })
        
        print(f"{strategy_names[strategy]:<12} {buy_signals:<8} {sell_signals:<8} {total_signals:<8} {frequency:.1f}%")
    
    print("-" * 50)
    
    # 当前配置分析
    print(f"\n🔍 当前系统配置分析:")
    try:
        with open("trading_config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        settings = config["trading_settings"]
        
        # 判断当前策略类型
        if (settings["max_trades_per_day"] <= 5 and 
            settings["min_trade_interval"] >= 300 and
            settings["stop_loss_percent"] >= 5.0):
            current_strategy = "🛡️ 保守策略"
        elif (settings["max_trades_per_day"] <= 10 and 
              settings["min_trade_interval"] >= 180 and
              settings["stop_loss_percent"] >= 3.0):
            current_strategy = "⚖️ 平衡策略"
        else:
            current_strategy = "⚡ 激进策略"
        
        print(f"   当前策略: {current_strategy}")
        print(f"   每日最大交易: {settings['max_trades_per_day']}笔")
        print(f"   交易间隔: {settings['min_trade_interval']}秒")
        print(f"   单笔金额: {settings['trade_amount_usdt']} USDT")
        
        # 预估信号频率
        for result in results:
            if current_strategy.endswith(result['name']):
                print(f"   预估信号频率: {result['frequency']:.1f}% (每1000个数据点约{result['total']}个信号)")
                break
                
    except Exception as e:
        print(f"   ❌ 无法读取配置: {e}")
    
    print(f"\n💡 策略建议:")
    print(f"   🛡️ 保守策略: 适合稳健投资者，信号质量高但频率低")
    print(f"   ⚖️ 平衡策略: 适合一般投资者，平衡风险与机会")
    print(f"   ⚡ 激进策略: 适合风险承受能力强的投资者，信号频率高")
    
    print(f"\n⚠️ 重要提醒:")
    print(f"   - 更多信号 ≠ 更多收益，质量比数量重要")
    print(f"   - 建议先在沙盒环境充分测试")
    print(f"   - 根据个人风险承受能力选择合适的策略")

if __name__ == "__main__":
    main()
