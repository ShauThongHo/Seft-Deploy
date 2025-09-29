#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OKX 下单测试工具
用于测试实际下单功能
"""

import sys
import json
from okx_trading_api import OKXTradingAPI
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    print("🔧 OKX 下单测试工具")
    print("=" * 50)
    
    try:
        # 初始化API
        print("📡 正在初始化API...")
        api = OKXTradingAPI()
        
        print(f"🏖️  Sandbox Mode: {api.sandbox}")
        if not api.sandbox:
            response = input("⚠️  当前为实盘模式，是否继续？(y/N): ")
            if response.lower() != 'y':
                print("已取消操作")
                return
        
        # 获取当前BTC价格
        print("\n📊 获取BTC当前价格...")
        ticker_response = api.get_ticker('BTC-USDT')
        
        if ticker_response.get('code') == '0' and ticker_response.get('data'):
            current_price = float(ticker_response['data'][0]['last'])
            print(f"✅ BTC当前价格: {current_price} USDT")
        else:
            print(f"❌ 获取价格失败: {ticker_response}")
            return
        
        # 计算下单数量
        print("\n🧮 计算下单数量...")
        trade_size = api.calculate_trade_size('BTC-USDT', current_price)
        
        if trade_size <= 0:
            print("❌ 下单数量计算失败")
            return
        
        print(f"✅ 计算的下单数量: {trade_size} BTC")
        print(f"   预计交易金额: {trade_size * current_price:.2f} USDT")
        
        # 确认下单
        print(f"\n📋 下单详情:")
        print(f"   交易对: BTC-USDT")
        print(f"   方向: 买入")
        print(f"   数量: {trade_size} BTC")
        print(f"   类型: 市价单")
        print(f"   预计金额: {trade_size * current_price:.2f} USDT")
        
        if api.sandbox:
            print("   🏖️  模拟交易模式 - 安全测试")
        else:
            print("   ⚠️  实盘交易模式 - 真实资金")
        
        confirm = input("\n是否确认下单？(y/N): ")
        if confirm.lower() != 'y':
            print("已取消下单")
            return
        
        # 执行下单
        print("\n🚀 正在下单...")
        order_result = api.place_market_order('BTC-USDT', 'buy', trade_size)
        
        if order_result.get('code') == '0':
            order_data = order_result['data'][0]
            order_id = order_data.get('ordId')
            print(f"✅ 下单成功！")
            print(f"   订单ID: {order_id}")
            print(f"   状态: {order_data.get('sMsg', 'Success')}")
        else:
            print(f"❌ 下单失败!")
            print(f"   错误代码: {order_result.get('code')}")
            print(f"   错误信息: {order_result.get('msg')}")
            
            if order_result.get('data'):
                for error in order_result['data']:
                    print(f"   详细错误: {error.get('sCode')} - {error.get('sMsg')}")
        
        print("\n🎉 测试完成！")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        logger.error(f"Test failed: {e}", exc_info=True)

if __name__ == "__main__":
    main()
