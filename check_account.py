#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查账户配置和权限
"""

import json
from okx_trading_api import OKXTradingAPI

def main():
    print("🔧 账户配置检查")
    print("=" * 50)
    
    # 初始化API
    api = OKXTradingAPI()
    
    print(f"🏖️  Sandbox Mode: {api.sandbox}")
    
    # 1. 检查账户配置
    print("\n📋 1. 检查账户配置...")
    try:
        config_response = api.make_request('GET', '/api/v5/account/config', {})
        if config_response.get('code') == '0':
            config_data = config_response.get('data', [{}])[0]
            print(f"   账户级别: {config_data.get('acctLv', 'N/A')}")
            print(f"   自动借币: {config_data.get('autoLoan', 'N/A')}")
            print(f"   持仓模式: {config_data.get('posMode', 'N/A')}")
            print(f"   余额模式: {config_data.get('balMode', 'N/A')}")
            print(f"   UID: {config_data.get('uid', 'N/A')}")
            print(f"   完整配置: {json.dumps(config_data, indent=2)}")
        else:
            print(f"   ❌ 获取账户配置失败: {config_response}")
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    # 2. 检查最大可用余额
    print("\n💰 2. 检查最大可用余额...")
    try:
        max_size_response = api.make_request('GET', '/api/v5/account/max-size', {
            'instId': 'BTC-USDT',
            'tdMode': 'cash'
        })
        if max_size_response.get('code') == '0':
            max_data = max_size_response.get('data', [{}])[0]
            print(f"   最大买入量: {max_data.get('maxBuy', 'N/A')}")
            print(f"   最大卖出量: {max_data.get('maxSell', 'N/A')}")
            print(f"   币种: {max_data.get('ccy', 'N/A')}")
            print(f"   交易对: {max_data.get('instId', 'N/A')}")
        else:
            print(f"   ❌ 获取最大可用余额失败: {max_size_response}")
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    # 3. 检查最大可用金额
    print("\n💵 3. 检查最大可用金额...")
    try:
        max_avail_response = api.make_request('GET', '/api/v5/account/max-avail-size', {
            'instId': 'BTC-USDT',
            'tdMode': 'cash'
        })
        if max_avail_response.get('code') == '0':
            avail_data = max_avail_response.get('data', [{}])[0]
            print(f"   最大可用买入量: {avail_data.get('availBuy', 'N/A')}")
            print(f"   最大可用卖出量: {avail_data.get('availSell', 'N/A')}")
            print(f"   币种: {avail_data.get('ccy', 'N/A')}")
            print(f"   交易对: {avail_data.get('instId', 'N/A')}")
        else:
            print(f"   ❌ 获取最大可用金额失败: {max_avail_response}")
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    # 4. 检查API权限
    print("\n🔑 4. 检查API权限...")
    try:
        # 尝试获取订单历史来测试权限
        orders_response = api.make_request('GET', '/api/v5/trade/orders-history-archive', {
            'instType': 'SPOT'
        })
        if orders_response.get('code') == '0':
            print(f"   ✅ 交易权限正常")
        else:
            print(f"   ❌ 交易权限异常: {orders_response}")
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    # 5. 测试限价单
    print("\n📈 5. 测试限价单...")
    try:
        ticker_response = api.make_request('GET', '/api/v5/market/ticker', {
            'instId': 'BTC-USDT'
        })
        current_price = float(ticker_response['data'][0]['last'])
        
        # 设置一个较低的限价，这样不会真正成交
        limit_price = current_price * 0.8  # 低于市价20%
        order_size = 100 / limit_price  # 100 USDT的订单
        order_size = round(order_size, 8)
        
        limit_params = {
            'instId': 'BTC-USDT',
            'tdMode': 'cash',
            'side': 'buy',
            'ordType': 'limit',
            'sz': f"{order_size:.8f}".rstrip('0').rstrip('.'),
            'px': f"{limit_price:.1f}"
        }
        
        print(f"   当前价格: {current_price}")
        print(f"   限价: {limit_price}")
        print(f"   数量: {order_size:.8f}")
        print(f"   参数: {limit_params}")
        
        limit_result = api.make_request('POST', '/api/v5/trade/order', limit_params)
        
        if limit_result.get('code') == '0':
            print(f"   ✅ 限价单下单成功!")
            order_id = limit_result['data'][0]['ordId']
            print(f"   订单ID: {order_id}")
            
            # 立即撤销订单
            cancel_result = api.make_request('POST', '/api/v5/trade/cancel-order', {
                'instId': 'BTC-USDT',
                'ordId': order_id
            })
            if cancel_result.get('code') == '0':
                print(f"   ✅ 订单已撤销")
            else:
                print(f"   ⚠️  撤销失败: {cancel_result}")
        else:
            print(f"   ❌ 限价单失败: {limit_result}")
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")

if __name__ == "__main__":
    main()
