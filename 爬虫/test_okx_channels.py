#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试正确的OKX WebSocket频道格式
"""

import websocket
import json
import time

class OKXChannelTest:
    def __init__(self):
        self.message_count = 0
        
    def on_message(self, ws, message):
        self.message_count += 1
        print(f"\n[消息 #{self.message_count}]")
        try:
            data = json.loads(message)
            if 'event' in data:
                print(f"事件: {data['event']}")
                if data['event'] == 'error':
                    print(f"❌ 错误: {data['msg']}")
                elif data['event'] == 'subscribe':
                    print(f"✅ 订阅成功: {data}")
            
            if 'data' in data and len(data['data']) > 0:
                print(f"✅ 收到K线数据: {len(data['data'])}条")
                for item in data['data']:
                    print(f"   价格: {item[4]}, 时间: {item[0]}")
                    
        except Exception as e:
            print(f"解析错误: {e}")
    
    def on_error(self, ws, error):
        print(f"❌ 错误: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        print(f"🔴 连接关闭: {close_status_code}")
    
    def on_open(self, ws):
        print("🟢 连接成功!")
        
        # 测试正确的频道格式
        test_channels = [
            "candle1m",      # 1分钟K线
            "candle5m",      # 5分钟K线  
            "candle1H",      # 1小时K线
            "candle1D",      # 1天K线
            "tickers",       # 行情数据
            "books5",        # 5档订单簿
        ]
        
        print(f"📡 测试不同频道格式...")
        
        for channel in test_channels:
            sub_msg = {
                "op": "subscribe",
                "args": [{
                    "channel": channel,
                    "instId": "BTC-USDT"
                }]
            }
            print(f"发送: {channel}")
            ws.send(json.dumps(sub_msg))
            time.sleep(2)
    
    def test(self):
        print("🧪 测试OKX正确的频道格式...")
        
        self.ws = websocket.WebSocketApp(
            "wss://ws.okx.com:8443/ws/v5/public",
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        
        self.ws.run_forever()

if __name__ == "__main__":
    tester = OKXChannelTest()
    tester.test()
