#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
灵活的信号检测系统
支持保守、平衡、激进三种策略模式
"""

import json
from typing import List, Dict, Tuple
import pandas as pd

class FlexibleSignalDetector:
    def __init__(self, config_path: str = "trading_config.json"):
        self.config_path = config_path
        self.load_config()
        self.strategy_mode = self.get_strategy_mode()
    
    def load_config(self):
        """加载配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            # 默认配置
            self.config = {
                "trading_settings": {
                    "trade_amount_usdt": 150,
                    "min_trade_interval": 300,
                    "max_trades_per_day": 5,
                    "stop_loss_percent": 5.0,
                    "take_profit_percent": 10.0
                }
            }
    
    def get_strategy_mode(self) -> str:
        """根据配置判断策略模式"""
        settings = self.config["trading_settings"]
        
        # 根据交易频率和风险参数判断模式
        if (settings["max_trades_per_day"] <= 5 and 
            settings["min_trade_interval"] >= 300 and
            settings["stop_loss_percent"] >= 5.0):
            return "conservative"
        elif (settings["max_trades_per_day"] <= 10 and 
              settings["min_trade_interval"] >= 180 and
              settings["stop_loss_percent"] >= 3.0):
            return "balanced"
        else:
            return "aggressive"
    
    def detect_buy_signals(self, df: pd.DataFrame, i: int) -> Tuple[bool, int, List[str]]:
        """
        检测买入信号
        返回: (是否买入, 信号强度, 触发条件列表)
        """
        if i < 10:  # 需要足够的历史数据
            return False, 0, []
        
        # 基础买入条件
        buy_conditions = {
            'macd_golden': (
                df.iloc[i]['macd'] > df.iloc[i]['signal'] and 
                df.iloc[i-1]['macd'] <= df.iloc[i-1]['signal'] and
                df.iloc[i]['macd'] > 0
            ),
            'kdj_bullish': (
                df.iloc[i]['k'] > df.iloc[i]['d'] and 
                (df.iloc[i]['k'] < 80 or df.iloc[i-5]['k'] < 20)
            ),
            'rsi_positive': (
                df.iloc[i]['rsi'] > 50 or 
                (df.iloc[i]['rsi'] > 30 and df.iloc[i-5]['rsi'] < 30)
            ),
            'williams_positive': (
                df.iloc[i]['williams_r'] > -50 or 
                (df.iloc[i]['williams_r'] > -80 and df.iloc[i-5]['williams_r'] < -80)
            ),
            'price_above_bbi': df.iloc[i]['close'] > df.iloc[i]['bbi'],
            'zlmm_positive': df.iloc[i]['zlmm'] > 0
        }
        
        # 计算满足的条件
        satisfied_conditions = [name for name, condition in buy_conditions.items() if condition]
        signal_strength = len(satisfied_conditions)
        
        # 根据策略模式决定买入门槛
        should_buy = self._should_buy_based_on_strategy(signal_strength, satisfied_conditions)
        
        return should_buy, signal_strength, satisfied_conditions
    
    def detect_sell_signals(self, df: pd.DataFrame, i: int) -> Tuple[bool, int, List[str]]:
        """
        检测卖出信号
        返回: (是否卖出, 信号强度, 触发条件列表)
        """
        if i < 10:
            return False, 0, []
        
        # 基础卖出条件
        sell_conditions = {
            'rsi_overbought': df.iloc[i]['rsi'] > 70,
            'kdj_overbought': df.iloc[i]['k'] > 80 and df.iloc[i]['d'] > 80,
            'williams_overbought': df.iloc[i]['williams_r'] > -20,
            'macd_death_cross': (
                df.iloc[i]['macd'] < df.iloc[i]['signal'] and 
                df.iloc[i-1]['macd'] >= df.iloc[i-1]['signal']
            ),
            'price_far_from_bbi': abs(df.iloc[i]['close'] - df.iloc[i]['bbi']) / df.iloc[i]['bbi'] > 0.05,
            'zlmm_negative': df.iloc[i]['zlmm'] < 0
        }
        
        # 计算满足的条件
        satisfied_conditions = [name for name, condition in sell_conditions.items() if condition]
        signal_strength = len(satisfied_conditions)
        
        # 根据策略模式决定卖出门槛
        should_sell = self._should_sell_based_on_strategy(signal_strength, satisfied_conditions)
        
        return should_sell, signal_strength, satisfied_conditions
    
    def _should_buy_based_on_strategy(self, signal_strength: int, conditions: List[str]) -> bool:
        """根据策略模式决定是否买入"""
        if self.strategy_mode == "conservative":
            # 保守模式：需要所有6个条件或至少5个强势条件
            return signal_strength >= 6 or (signal_strength >= 5 and 'macd_golden' in conditions)
        
        elif self.strategy_mode == "balanced":
            # 平衡模式：需要至少4个条件，且必须包含MACD或KDJ
            return (signal_strength >= 4 and 
                   ('macd_golden' in conditions or 'kdj_bullish' in conditions))
        
        else:  # aggressive
            # 激进模式：需要至少3个条件
            return signal_strength >= 3
    
    def _should_sell_based_on_strategy(self, signal_strength: int, conditions: List[str]) -> bool:
        """根据策略模式决定是否卖出"""
        if self.strategy_mode == "conservative":
            # 保守模式：需要至少4个卖出条件
            return signal_strength >= 4
        
        elif self.strategy_mode == "balanced":
            # 平衡模式：需要至少3个卖出条件
            return signal_strength >= 3
        
        else:  # aggressive
            # 激进模式：需要至少2个卖出条件
            return signal_strength >= 2
    
    def get_signal_description(self, signal_type: str, strength: int, conditions: List[str]) -> str:
        """获取信号描述"""
        condition_names = {
            'macd_golden': 'MACD金叉',
            'kdj_bullish': 'KDJ看涨',
            'rsi_positive': 'RSI积极',
            'williams_positive': 'Williams积极',
            'price_above_bbi': '价格>BBI',
            'zlmm_positive': 'ZLMM积极',
            'rsi_overbought': 'RSI超买',
            'kdj_overbought': 'KDJ超买',
            'williams_overbought': 'Williams超买',
            'macd_death_cross': 'MACD死叉',
            'price_far_from_bbi': '偏离BBI',
            'zlmm_negative': 'ZLMM消极'
        }
        
        condition_text = ", ".join([condition_names.get(c, c) for c in conditions])
        
        strength_level = "弱" if strength <= 2 else "中" if strength <= 4 else "强"
        
        return f"{signal_type}信号 (强度: {strength_level} {strength}/6) - {condition_text}"

# 测试函数
def test_signal_detector():
    """测试信号检测器"""
    detector = FlexibleSignalDetector()
    print(f"当前策略模式: {detector.strategy_mode}")
    
    # 创建测试数据
    import numpy as np
    
    test_data = pd.DataFrame({
        'close': np.random.uniform(50000, 51000, 20),
        'macd': np.random.uniform(-100, 100, 20),
        'signal': np.random.uniform(-100, 100, 20),
        'k': np.random.uniform(0, 100, 20),
        'd': np.random.uniform(0, 100, 20),
        'rsi': np.random.uniform(0, 100, 20),
        'williams_r': np.random.uniform(-100, 0, 20),
        'bbi': np.random.uniform(49000, 51000, 20),
        'zlmm': np.random.uniform(-1000, 1000, 20)
    })
    
    # 测试最后几个数据点
    for i in range(15, 20):
        buy_signal, buy_strength, buy_conditions = detector.detect_buy_signals(test_data, i)
        sell_signal, sell_strength, sell_conditions = detector.detect_sell_signals(test_data, i)
        
        print(f"\n时间点 {i}:")
        if buy_signal:
            print(f"  🟢 {detector.get_signal_description('买入', buy_strength, buy_conditions)}")
        if sell_signal:
            print(f"  🔴 {detector.get_signal_description('卖出', sell_strength, sell_conditions)}")
        if not buy_signal and not sell_signal:
            print(f"  ⚪ 无信号 (买入强度: {buy_strength}, 卖出强度: {sell_strength})")

if __name__ == "__main__":
    test_signal_detector()
