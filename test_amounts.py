#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试不同金额的下单
"""

import json
from okx_trading_api import OKXTradingAPI

def test_order_amount(api, amount):
    """测试指定金额的下单"""
    print(f"\n💰 测试 {amount} USDT 下单:")
    
    # 获取当前价格
    ticker_response = api.make_request('GET', '/api/v5/market/ticker', {
        'instId': 'BTC-USDT'
    })
    current_price = float(ticker_response['data'][0]['last'])
    
    # 计算数量
    trade_size = amount / current_price
    trade_size = round(trade_size, 8)  # 8位小数精度
    
    print(f"   价格: {current_price} USDT")
    print(f"   数量: {trade_size:.8f} BTC")
    print(f"   实际金额: {trade_size * current_price:.2f} USDT")
    
    # 下单参数
    params = {
        'instId': 'BTC-USDT',
        'tdMode': 'cash',
        'side': 'buy',
        'ordType': 'market',
        'sz': f"{trade_size:.8f}".rstrip('0').rstrip('.')
    }
    
    print(f"   下单参数: {params}")
    
    # 发送下单请求
    result = api.make_request('POST', '/api/v5/trade/order', params)
    
    if result.get('code') == '0':
        print(f"   ✅ 下单成功!")
        return True
    else:
        print(f"   ❌ 下单失败: {result.get('msg', 'Unknown error')}")
        if result.get('data'):
            for error in result['data']:
                print(f"      错误详情: {error.get('sCode')} - {error.get('sMsg')}")
        return False

def main():
    print("🔧 测试不同金额的下单")
    print("=" * 50)
    
    # 初始化API
    api = OKXTradingAPI()
    
    print(f"🏖️  Sandbox Mode: {api.sandbox}")
    
    # 测试不同金额
    test_amounts = [5, 10, 50, 100, 150, 200, 500]
    
    for amount in test_amounts:
        success = test_order_amount(api, amount)
        if success:
            print(f"✅ {amount} USDT 成功！停止测试。")
            break
    
    print("\n🎉 测试完成！")

if __name__ == "__main__":
    main()
