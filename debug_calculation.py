#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细的数量计算调试工具
"""

import json
from okx_trading_api import OKXTradingAPI

def main():
    print("🔧 数量计算详细调试")
    print("=" * 50)
    
    # 初始化API
    api = OKXTradingAPI()
    
    # 获取当前价格
    ticker_response = api.make_request('GET', '/api/v5/market/ticker', {
        'instId': 'BTC-USDT'
    })
    
    current_price = float(ticker_response['data'][0]['last'])
    print(f"📊 当前BTC价格: {current_price} USDT")
    
    # 获取交易对详情
    inst_response = api.make_request('GET', '/api/v5/public/instruments', {
        'instType': 'SPOT',
        'instId': 'BTC-USDT'
    })
    
    if inst_response['code'] == '0' and inst_response['data']:
        data = inst_response['data'][0]
        min_size = float(data.get('minSz', 0))
        lot_sz = data.get('lotSz', '1')
        
        print(f"📋 交易规则:")
        print(f"   最小数量 (minSz): {min_size}")
        print(f"   数量步长 (lotSz): {lot_sz}")
        
        # 模拟计算过程
        trade_amount = 150.0
        trade_size = trade_amount / current_price
        
        print(f"\n🧮 原始计算:")
        print(f"   计划金额: {trade_amount} USDT")
        print(f"   原始数量: {trade_size:.12f} BTC")
        
        # 检查最小数量
        if trade_size < min_size:
            print(f"❌ 数量小于最小值，调整为: {min_size}")
            trade_size = min_size
        else:
            print(f"✅ 数量满足最小值要求")
        
        # 精度调整
        if '.' in lot_sz:
            decimal_places = len(lot_sz.split('.')[1])
            print(f"🎯 根据lotSz调整精度到 {decimal_places} 位小数")
            adjusted_size = round(trade_size, decimal_places)
            print(f"   调整前: {trade_size:.12f}")
            print(f"   调整后: {adjusted_size:.12f}")
            trade_size = adjusted_size
        
        # 检查lotSz的倍数
        lot_sz_float = float(lot_sz)
        remainder = trade_size % lot_sz_float
        if remainder != 0:
            # 向下调整到最近的lot_sz倍数
            adjusted_size = trade_size - remainder
            print(f"⚠️  调整到lotSz的倍数:")
            print(f"   原数量: {trade_size:.12f}")
            print(f"   余数: {remainder:.12f}")
            print(f"   调整后: {adjusted_size:.12f}")
            trade_size = adjusted_size
        
        # 最终结果
        final_amount = trade_size * current_price
        print(f"\n🎯 最终结果:")
        print(f"   下单数量: {trade_size:.8f} BTC")
        print(f"   预计金额: {final_amount:.2f} USDT")
        print(f"   格式化数量: {f'{trade_size:.8f}'.rstrip('0').rstrip('.')}")
        
        # 验证是否是lotSz的精确倍数
        times = trade_size / lot_sz_float
        print(f"\n🔍 验证:")
        print(f"   是否为lotSz的整数倍: {times:.12f} (应为整数)")
        print(f"   是否满足最小数量: {'✅' if trade_size >= min_size else '❌'}")

if __name__ == "__main__":
    main()
