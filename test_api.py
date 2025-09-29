#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OKX API 连接测试工具
用于诊断和测试API配置是否正确
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
    print("🔧 OKX API 连接测试工具")
    print("=" * 50)
    
    try:
        # 初始化API
        print("📡 正在初始化API...")
        api = OKXTradingAPI()
        
        # 显示配置信息
        print(f"🔑 API Key: {api.api_key[:8]}...{api.api_key[-8:]}")
        print(f"🔐 Secret Key: {api.secret_key[:8]}...{api.secret_key[-8:]}")
        print(f"🔒 Passphrase: {api.passphrase[:3]}...{api.passphrase[-3:]}")
        print(f"🏖️  Sandbox Mode: {api.sandbox}")
        print(f"💰 Trade Amount: {api.trade_amount_usdt} USDT")
        print()
        
        # 测试API连接
        print("🔍 测试API连接...")
        test_result = api.test_api_connection()
        
        if test_result['success']:
            print("✅ API连接成功！")
        else:
            print(f"❌ API连接失败: {test_result['message']}")
            return
        
        print()
        
        # 获取账户余额
        print("💰 获取账户余额...")
        balance_response = api.get_account_balance()
        
        if balance_response.get('code') == '0':
            print("✅ 余额获取成功！")
            
            for detail in balance_response.get('data', [{}])[0].get('details', []):
                currency = detail.get('ccy')
                available = detail.get('availBal', '0')
                frozen = detail.get('frozenBal', '0')
                
                if float(available) > 0 or float(frozen) > 0:
                    print(f"   {currency}: 可用 {available}, 冻结 {frozen}")
        else:
            print(f"❌ 余额获取失败: {balance_response.get('msg')}")
            return
        
        print()
        
        # 测试交易对信息
        print("📊 测试交易对信息...")
        test_pairs = ['BTC-USDT', 'ETH-USDT', 'SOL-USDT']
        
        for pair in test_pairs:
            inst_info = api.get_instrument_info(pair)
            if inst_info.get('code') == '0' and inst_info.get('data'):
                data = inst_info['data'][0]
                min_size = data.get('minSz', 'N/A')
                lot_sz = data.get('lotSz', 'N/A')
                print(f"   {pair}: 最小下单量 {min_size}, 下单精度 {lot_sz}")
            else:
                print(f"   {pair}: ❌ 获取失败")
        
        print()
        
        # 测试下单数量计算
        print("🧮 测试下单数量计算...")
        test_price = 100000  # 假设BTC价格为10万USDT
        trade_size = api.calculate_trade_size('BTC-USDT', test_price)
        
        if trade_size > 0:
            print(f"✅ 计算成功: {trade_size} BTC (约 {trade_size * test_price:.2f} USDT)")
        else:
            print("❌ 下单数量计算失败，可能是余额不足或参数错误")
        
        print()
        print("🎉 测试完成！")
        
        # 给出建议
        print("\n💡 建议:")
        if api.sandbox:
            print("   - 当前在模拟交易模式，可以安全测试")
            print("   - 如需实盘交易，请修改配置文件中的 sandbox 为 false")
        else:
            print("   - ⚠️  当前为实盘模式，请谨慎操作")
        
        print("   - 确保账户有足够的USDT余额")
        print("   - 建议从小金额开始测试")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        logger.error(f"Test failed: {e}", exc_info=True)

if __name__ == "__main__":
    main()
