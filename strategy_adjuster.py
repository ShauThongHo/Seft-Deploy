#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易策略调整工具
可以在保守、平衡、激进三种模式间切换
"""

import json
import os
from typing import Dict, Any

class TradingStrategyAdjuster:
    def __init__(self, config_path: str = "trading_config.json"):
        self.config_path = config_path
        self.load_current_config()
    
    def load_current_config(self):
        """加载当前配置"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
    
    def save_config(self):
        """保存配置"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
    
    def set_conservative_strategy(self):
        """保守策略 - 当前设置"""
        self.config["trading_settings"].update({
            "trade_amount_usdt": 150,
            "min_trade_interval": 300,  # 5分钟
            "max_trades_per_day": 5,
            "stop_loss_percent": 5.0,
            "take_profit_percent": 10.0,
            "risk_management": {
                "max_position_percent": 20,
                "max_drawdown_percent": 10
            }
        })
        print("✅ 已设置为保守策略")
        print("   - 每日最多5笔交易")
        print("   - 5分钟交易间隔")
        print("   - 150 USDT单笔金额")
        print("   - 5%止损，10%止盈")
    
    def set_balanced_strategy(self):
        """平衡策略 - 中等风险"""
        self.config["trading_settings"].update({
            "trade_amount_usdt": 300,
            "min_trade_interval": 180,  # 3分钟
            "max_trades_per_day": 10,
            "stop_loss_percent": 3.0,
            "take_profit_percent": 6.0,
            "risk_management": {
                "max_position_percent": 30,
                "max_drawdown_percent": 15
            }
        })
        print("✅ 已设置为平衡策略")
        print("   - 每日最多10笔交易")
        print("   - 3分钟交易间隔")
        print("   - 300 USDT单笔金额")
        print("   - 3%止损，6%止盈")
    
    def set_aggressive_strategy(self):
        """激进策略 - 高频交易"""
        self.config["trading_settings"].update({
            "trade_amount_usdt": 500,
            "min_trade_interval": 60,   # 1分钟
            "max_trades_per_day": 20,
            "stop_loss_percent": 2.0,
            "take_profit_percent": 4.0,
            "risk_management": {
                "max_position_percent": 50,
                "max_drawdown_percent": 20
            }
        })
        print("✅ 已设置为激进策略")
        print("   - 每日最多20笔交易")
        print("   - 1分钟交易间隔")
        print("   - 500 USDT单笔金额")
        print("   - 2%止损，4%止盈")
    
    def show_current_strategy(self):
        """显示当前策略"""
        settings = self.config["trading_settings"]
        print("📊 当前交易策略设置:")
        print(f"   💰 单笔交易金额: {settings['trade_amount_usdt']} USDT")
        print(f"   ⏱️  最小交易间隔: {settings['min_trade_interval']}秒")
        print(f"   📈 每日最大交易数: {settings['max_trades_per_day']}笔")
        print(f"   🛑 止损比例: {settings['stop_loss_percent']}%")
        print(f"   🎯 止盈比例: {settings['take_profit_percent']}%")
        print(f"   📊 最大仓位比例: {settings['risk_management']['max_position_percent']}%")
        print(f"   ⚠️  最大回撤: {settings['risk_management']['max_drawdown_percent']}%")

def main():
    adjuster = TradingStrategyAdjuster()
    
    print("🎯 OKX 交易策略调整工具")
    print("=" * 50)
    
    adjuster.show_current_strategy()
    
    print("\n🔧 可选策略模式:")
    print("1. 保守策略 (Conservative) - 低风险低频")
    print("2. 平衡策略 (Balanced)    - 中等风险中频")
    print("3. 激进策略 (Aggressive)  - 高风险高频")
    print("4. 查看当前设置")
    print("0. 退出")
    
    while True:
        try:
            choice = input("\n请选择策略模式 (0-4): ").strip()
            
            if choice == "0":
                print("👋 再见！")
                break
            elif choice == "1":
                adjuster.set_conservative_strategy()
                adjuster.save_config()
                print("💾 配置已保存")
            elif choice == "2":
                adjuster.set_balanced_strategy()
                adjuster.save_config()
                print("💾 配置已保存")
            elif choice == "3":
                adjuster.set_aggressive_strategy()
                adjuster.save_config()
                print("💾 配置已保存")
            elif choice == "4":
                adjuster.show_current_strategy()
            else:
                print("❌ 无效选择，请输入0-4")
        
        except KeyboardInterrupt:
            print("\n👋 退出")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")

if __name__ == "__main__":
    main()
