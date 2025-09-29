#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OKX 交易系统启动器
支持策略调整和系统启动
"""

import os
import sys
import json
import subprocess
from typing import Dict

def show_current_strategy():
    """显示当前策略设置"""
    try:
        with open("trading_config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        settings = config["trading_settings"]
        print("📊 当前交易策略设置:")
        print(f"   💰 单笔交易金额: {settings['trade_amount_usdt']} USDT")
        print(f"   ⏱️  最小交易间隔: {settings['min_trade_interval']}秒")
        print(f"   📈 每日最大交易数: {settings['max_trades_per_day']}笔")
        print(f"   🛑 止损比例: {settings['stop_loss_percent']}%")
        print(f"   🎯 止盈比例: {settings['take_profit_percent']}%")
        
        # 判断策略类型
        if (settings["max_trades_per_day"] <= 5 and 
            settings["min_trade_interval"] >= 300 and
            settings["stop_loss_percent"] >= 5.0):
            strategy_type = "🛡️ 保守策略"
        elif (settings["max_trades_per_day"] <= 10 and 
              settings["min_trade_interval"] >= 180 and
              settings["stop_loss_percent"] >= 3.0):
            strategy_type = "⚖️ 平衡策略"
        else:
            strategy_type = "⚡ 激进策略"
        
        print(f"   📋 策略类型: {strategy_type}")
        
    except FileNotFoundError:
        print("❌ 未找到配置文件")
    except Exception as e:
        print(f"❌ 读取配置错误: {e}")

def main():
    print("🚀 OKX 实时交易分析系统")
    print("=" * 50)
    
    show_current_strategy()
    
    print("\n🎯 选择操作:")
    print("1. 🔧 调整交易策略")
    print("2. 📊 启动实时分析系统")
    print("3. 🧪 测试信号检测器")
    print("4. 📈 查看当前配置")
    print("0. 🚪 退出")
    
    while True:
        try:
            choice = input("\n请选择操作 (0-4): ").strip()
            
            if choice == "0":
                print("👋 再见！")
                break
            elif choice == "1":
                print("\n🔧 正在启动策略调整工具...")
                subprocess.run([sys.executable, "strategy_adjuster.py"])
                show_current_strategy()
            elif choice == "2":
                print("\n📊 正在启动实时分析系统...")
                print("💡 提示: 现在系统使用灵活的信号检测，信号频率会根据策略设置调整")
                subprocess.run([sys.executable, "okx_realtime_analyzer.py"])
            elif choice == "3":
                print("\n🧪 正在测试信号检测器...")
                subprocess.run([sys.executable, "flexible_signal_detector.py"])
            elif choice == "4":
                print()
                show_current_strategy()
            else:
                print("❌ 无效选择，请输入0-4")
                
        except KeyboardInterrupt:
            print("\n👋 退出")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")

if __name__ == "__main__":
    main()
