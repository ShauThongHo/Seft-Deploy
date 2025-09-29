#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试限价单模拟市价单
"""

import json
from okx_trading_api import OKXTradingAPI

def main():
    print("🔧 测试限价单模拟市价单")
    print("=" * 50)
    
    # 初始化API
    api = OKXTradingAPI()
    
    print(f"🏖️  Sandbox Mode: {api.sandbox}")
    
    # 计算交易数量
    trade_amount = 150.0
    
    # 获取当前价格
    ticker_response = api.make_request('GET', '/api/v5/market/ticker', {
        'instId': 'BTC-USDT'
    })
    current_price = float(ticker_response['data'][0]['last'])
    trade_size = api.calculate_trade_size('BTC-USDT', current_price)
    
    print(f"📊 交易参数:")
    print(f"   当前价格: {current_price} USDT")
    print(f"   计划金额: {trade_amount} USDT")
    print(f"   计算数量: {trade_size:.8f} BTC")
    print(f"   实际金额: {trade_size * current_price:.2f} USDT")
    
    if trade_size <= 0:
        print("❌ 交易数量计算失败")
        return
    
    # 测试模拟市价买单
    print(f"\n🛒 测试限价单模拟市价买单...")
    buy_result = api.place_market_order_as_limit('BTC-USDT', 'buy', trade_size)
    
    if buy_result.get('code') == '0':
        order_id = buy_result['data'][0]['ordId']
        print(f"✅ 买单下单成功!")
        print(f"   订单ID: {order_id}")
        
        # 等待一下，然后检查订单状态
        import time
        time.sleep(2)
        
        # 检查订单状态
        order_info = api.make_request('GET', '/api/v5/trade/order', {
            'instId': 'BTC-USDT',
            'ordId': order_id
        })
        
        if order_info.get('code') == '0' and order_info.get('data'):
            order_data = order_info['data'][0]
            state = order_data.get('state', 'unknown')
            filled_sz = order_data.get('fillSz', '0')
            avg_px = order_data.get('avgPx', '0')
            
            print(f"   订单状态: {state}")
            print(f"   成交数量: {filled_sz}")
            print(f"   成交均价: {avg_px}")
            
            if state == 'filled':
                print(f"✅ 订单已完全成交!")
                actual_amount = float(filled_sz) * float(avg_px) if avg_px != '0' else 0
                print(f"   实际成交金额: {actual_amount:.2f} USDT")
                
                # 测试卖出
                print(f"\n💰 测试限价单模拟市价卖单...")
                sell_result = api.place_market_order_as_limit('BTC-USDT', 'sell', float(filled_sz))
                
                if sell_result.get('code') == '0':
                    sell_order_id = sell_result['data'][0]['ordId']
                    print(f"✅ 卖单下单成功!")
                    print(f"   卖单ID: {sell_order_id}")
                else:
                    print(f"❌ 卖单失败: {sell_result}")
                    
            elif state in ['live', 'partially_filled']:
                print(f"⚠️  订单未完全成交，撤销订单...")
                cancel_result = api.make_request('POST', '/api/v5/trade/cancel-order', {
                    'instId': 'BTC-USDT',
                    'ordId': order_id
                })
                if cancel_result.get('code') == '0':
                    print(f"✅ 订单已撤销")
                else:
                    print(f"❌ 撤销失败: {cancel_result}")
            else:
                print(f"❌ 订单状态异常: {state}")
        else:
            print(f"❌ 无法获取订单状态: {order_info}")
    else:
        print(f"❌ 买单失败: {buy_result}")
    
    print("\n🎉 测试完成！")

if __name__ == "__main__":
    main()
