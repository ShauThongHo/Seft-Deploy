#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略模式对比分析
比较保守、平衡、激进三种策略的信号生成情况
"""

import json
import pandas as pd
import numpy as np
from flexible_signal_detector import FlexibleSignalDetector

def create_test_data(length: int = 1000) -> pd.DataFrame:
    """创建测试数据"""
    np.random.seed(42)  # 固定随机种子以便重现
    
    # 创建价格走势
    prices = []
    price = 50000
    for i in range(length):
        change = np.random.normal(0, 0.002)  # 0.2%的日常波动
        price = price * (1 + change)
        prices.append(price)
    
    # 基于价格计算其他指标
    df = pd.DataFrame({
        'close': prices,
        'high': [p * (1 + abs(np.random.normal(0, 0.001))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0, 0.001))) for p in prices],
        'volume': np.random.uniform(1000000, 5000000, length)
    })
    
    # 计算技术指标（简化版）
    df['macd'] = df['close'].ewm(span=12).mean() - df['close'].ewm(span=26).mean()
    df['signal'] = df['macd'].ewm(span=9).mean()
    
    # KDJ
    df['k'] = np.random.uniform(0, 100, length)
    df['d'] = df['k'].rolling(3).mean()
    
    # RSI
    price_change = df['close'].pct_change()
    gain = price_change.where(price_change > 0, 0)
    loss = -price_change.where(price_change < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # Williams %R
    df['williams_r'] = np.random.uniform(-100, 0, length)
    
    # BBI
    df['bbi'] = (df['close'].rolling(3).mean() + 
                 df['close'].rolling(6).mean() + 
                 df['close'].rolling(12).mean() + 
                 df['close'].rolling(24).mean()) / 4
    
    # ZLMM
    df['zlmm'] = np.random.normal(0, 500, length)
    
    return df.fillna(method='bfill')

def test_strategy_performance(strategy_name: str, config: dict) -> dict:
    """测试特定策略的表现"""
    import os
    # 创建临时配置文件
    strategy_map = {"保守策略": "conservative", "平衡策略": "balanced", "激进策略": "aggressive"}
    strategy_key = strategy_map.get(strategy_name, "test")
    temp_config_path = os.path.join(os.getcwd(), f"temp_{strategy_key}_config.json")
    
    base_config = {
        "api_key": "test",
        "secret_key": "test",
        "passphrase": "test",
        "sandbox": True,
        "trading_enabled": False,
        "trading_settings": config
    }
    
    with open(temp_config_path, 'w', encoding='utf-8') as f:
        json.dump(base_config, f, indent=4)
    
    # 创建信号检测器
    detector = FlexibleSignalDetector(temp_config_path)
    
    # 创建测试数据
    df = create_test_data(1000)
    
    # 统计信号
    buy_signals = 0
    sell_signals = 0
    buy_details = []
    sell_details = []
    
    for i in range(30, len(df)):
        # 检测买入信号
        should_buy, buy_strength, buy_conditions = detector.detect_buy_signals(df, i)
        if should_buy:
            buy_signals += 1
            buy_details.append({
                'index': i,
                'strength': buy_strength,
                'conditions': len(buy_conditions)
            })
        
        # 检测卖出信号
        should_sell, sell_strength, sell_conditions = detector.detect_sell_signals(df, i)
        if should_sell:
            sell_signals += 1
            sell_details.append({
                'index': i,
                'strength': sell_strength,
                'conditions': len(sell_conditions)
            })
    
    # 清理临时文件
    import os
    os.remove(temp_config_path)
    
    return {
        'strategy': strategy_name,
        'mode': detector.strategy_mode,
        'buy_signals': buy_signals,
        'sell_signals': sell_signals,
        'total_signals': buy_signals + sell_signals,
        'signal_frequency': (buy_signals + sell_signals) / (len(df) - 30) * 100,
        'avg_buy_strength': np.mean([d['strength'] for d in buy_details]) if buy_details else 0,
        'avg_sell_strength': np.mean([d['strength'] for d in sell_details]) if sell_details else 0
    }

def main():
    """主函数 - 策略对比分析"""
    print("📊 策略模式对比分析")
    print("=" * 60)
    
    # 定义三种策略配置
    strategies = {
        "保守策略": {
            "trade_amount_usdt": 150,
            "min_trade_interval": 300,
            "max_trades_per_day": 5,
            "stop_loss_percent": 5.0,
            "take_profit_percent": 10.0,
            "risk_management": {
                "max_position_percent": 20,
                "max_drawdown_percent": 10
            }
        },
        "平衡策略": {
            "trade_amount_usdt": 300,
            "min_trade_interval": 180,
            "max_trades_per_day": 10,
            "stop_loss_percent": 3.0,
            "take_profit_percent": 6.0,
            "risk_management": {
                "max_position_percent": 30,
                "max_drawdown_percent": 15
            }
        },
        "激进策略": {
            "trade_amount_usdt": 500,
            "min_trade_interval": 60,
            "max_trades_per_day": 20,
            "stop_loss_percent": 2.0,
            "take_profit_percent": 4.0,
            "risk_management": {
                "max_position_percent": 50,
                "max_drawdown_percent": 20
            }
        }
    }
    
    print("⏳ 正在分析1000个数据点的信号生成情况...\n")
    
    results = []
    for name, config in strategies.items():
        result = test_strategy_performance(name, config)
        results.append(result)
    
    # 显示结果
    print("📈 策略对比结果:")
    print("-" * 60)
    print(f"{'策略':<8} {'模式':<12} {'买入':<6} {'卖出':<6} {'总计':<6} {'频率':<8} {'买入强度':<8} {'卖出强度'}")
    print("-" * 60)
    
    for result in results:
        print(f"{result['strategy']:<8} "
              f"{result['mode']:<12} "
              f"{result['buy_signals']:<6} "
              f"{result['sell_signals']:<6} "
              f"{result['total_signals']:<6} "
              f"{result['signal_frequency']:.2f}%{'':<3} "
              f"{result['avg_buy_strength']:.1f}{'':<7} "
              f"{result['avg_sell_strength']:.1f}")
    
    print("-" * 60)
    
    # 分析总结
    print("\n📋 分析总结:")
    most_active = max(results, key=lambda x: x['total_signals'])
    least_active = min(results, key=lambda x: x['total_signals'])
    
    print(f"🔥 最活跃策略: {most_active['strategy']} ({most_active['total_signals']}个信号)")
    print(f"🛡️ 最保守策略: {least_active['strategy']} ({least_active['total_signals']}个信号)")
    
    print(f"\n💡 建议:")
    print(f"   - 如果你希望更频繁的交易机会，选择 激进策略")
    print(f"   - 如果你希望高质量的信号，选择 保守策略")
    print(f"   - 如果你希望平衡风险和机会，选择 平衡策略")
    
    print(f"\n⚠️ 注意:")
    print(f"   - 更多的信号不一定意味着更好的收益")
    print(f"   - 策略选择应该结合你的风险承受能力")
    print(f"   - 沙盒环境测试成功后再考虑实盘交易")

if __name__ == "__main__":
    main()
