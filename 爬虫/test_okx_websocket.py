#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OKX WebSocket连接测试脚本
用于验证OKX WebSocket API的连接和数据接收
"""

import websocket
import json
import time
import threading

class OKXWebSocketTest:
    def __init__(self):
        self.ws = None
        self.message_count = 0
        
    def on_message(self, ws, message):
        """消息处理"""
        self.message_count += 1
        print(f"\n[消息 #{self.message_count}] 收到数据:")
        
        try:
            data = json.loads(message)
            print(f"JSON数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # 解析K线数据
            if 'data' in data and len(data['data']) > 0:
                for item in data['data']:
                    print(f"K线数据: 时间={item[0]}, 开={item[1]}, 高={item[2]}, 低={item[3]}, 收={item[4]}, 量={item[5]}")
                    
        except Exception as e:
            print(f"解析错误: {e}")
            print(f"原始消息: {message}")
    
    def on_error(self, ws, error):
        """错误处理"""
        print(f"❌ WebSocket错误: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        """连接关闭"""
        print(f"🔴 连接已关闭: code={close_status_code}, msg={close_msg}")
    
    def on_open(self, ws):
        """连接成功"""
        print("🟢 WebSocket连接成功!")
        
        # 测试不同的订阅格式
        test_subscriptions = [
            # 格式1: 标准格式
            {
                "op": "subscribe",
                "args": [{
                    "channel": "candle1m",
                    "instId": "BTC-USDT"
                }]
            },
            # 格式2: 备用格式
            {
                "op": "subscribe", 
                "args": [{
                    "channel": "candle1M",
                    "instId": "BTC-USDT"
                }]
            }
        ]
        
        for i, sub in enumerate(test_subscriptions):
            print(f"\n📡 发送订阅请求 #{i+1}: {json.dumps(sub, ensure_ascii=False)}")
            ws.send(json.dumps(sub))
            time.sleep(1)  # 间隔1秒
    
    def test_connection(self):
        """测试连接"""
        print("🔍 开始测试OKX WebSocket连接...")
        print("🌐 连接地址: wss://ws.okx.com:8443/ws/v5/public")
        
        # 启用调试
        websocket.enableTrace(True)
        
        self.ws = websocket.WebSocketApp(
            "wss://ws.okx.com:8443/ws/v5/public",
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        
        # 运行连接
        self.ws.run_forever()

def main():
    print("=" * 60)
    print("🧪 OKX WebSocket API 连接测试")
    print("=" * 60)
    
    tester = OKXWebSocketTest()
    
    try:
        tester.test_connection()
    except KeyboardInterrupt:
        print("\n\n⏹️ 用户中断测试")
    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
    
    print("\n📊 测试统计:")
    print(f"   收到消息数量: {tester.message_count}")
    print("=" * 60)

if __name__ == "__main__":
    main()
