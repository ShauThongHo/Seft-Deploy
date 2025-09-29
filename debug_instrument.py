#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OKX 交易对详情调试工具
用于查看BTC-USDT的具体交易规则
"""

import json
from okx_trading_api import OKXTradingAPI

def main():
    print("🔧 OKX 交易对详情调试")
    print("=" * 50)
    
    # 初始化API
    api = OKXTradingAPI()
    
    print("📊 获取BTC-USDT交易对详情...")
    
    # 获取交易对详情
    try:
        response = api.make_request('GET', '/api/v5/public/instruments', {
            'instType': 'SPOT',
            'instId': 'BTC-USDT'
        })
        
        if response['code'] == '0' and response['data']:
            instrument = response['data'][0]
            
            print("\n📋 BTC-USDT 交易规则:")
            print(f"   最小交易量 (minSz): {instrument.get('minSz', 'N/A')}")
            print(f"   数量精度 (lotSz): {instrument.get('lotSz', 'N/A')}")
            print(f"   价格精度 (tickSz): {instrument.get('tickSz', 'N/A')}")
            print(f"   最大市价买入金额 (maxMktAmt): {instrument.get('maxMktAmt', 'N/A')}")
            print(f"   最大限价买入金额 (maxLmtAmt): {instrument.get('maxLmtAmt', 'N/A')}")
            print(f"   最大市价买入数量 (maxMktSz): {instrument.get('maxMktSz', 'N/A')}")
            print(f"   最大限价买入数量 (maxLmtSz): {instrument.get('maxLmtSz', 'N/A')}")
            
            print("\n🔍 完整交易对信息:")
            print(json.dumps(instrument, indent=2, ensure_ascii=False))
            
            # 计算最小交易金额
            min_sz = float(instrument.get('minSz', '0'))
            print(f"\n💰 根据minSz计算的最小交易金额:")
            
            # 获取当前价格
            ticker_response = api.make_request('GET', '/api/v5/market/ticker', {
                'instId': 'BTC-USDT'
            })
            
            if ticker_response['code'] == '0' and ticker_response['data']:
                current_price = float(ticker_response['data'][0]['last'])
                min_amount = min_sz * current_price
                print(f"   当前价格: {current_price} USDT")
                print(f"   最小数量: {min_sz} BTC")
                print(f"   最小金额: {min_amount:.2f} USDT")
                
                # 检查我们的计算
                our_amount = 150.0
                our_size = our_amount / current_price
                print(f"\n🧮 我们的下单参数:")
                print(f"   计划金额: {our_amount} USDT")
                print(f"   计算数量: {our_size:.8f} BTC")
                print(f"   是否满足最小数量: {'✅' if our_size >= min_sz else '❌'}")
                
        else:
            print(f"❌ 获取交易对信息失败: {response}")
            
    except Exception as e:
        print(f"❌ 异常: {e}")

if __name__ == "__main__":
    main()
