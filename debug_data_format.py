#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import websocket
import json
import time

def on_message(ws, message):
    try:
        data = json.loads(message)
        print(f"收到原始数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        # 解析数据结构
        if 'data' in data:
            print(f"数据类型: {type(data['data'])}")
            if isinstance(data['data'], list) and len(data['data']) > 0:
                kline_data = data['data'][0]
                print(f"K线数据: {kline_data}")
                print(f"K线数据长度: {len(kline_data) if isinstance(kline_data, list) else 'N/A'}")
                
                if isinstance(kline_data, list) and len(kline_data) >= 9:
                    print(f"解析结果:")
                    print(f"  时间戳: {kline_data[0]}")
                    print(f"  开盘价: {kline_data[1]}")
                    print(f"  最高价: {kline_data[2]}")
                    print(f"  最低价: {kline_data[3]}")
                    print(f"  收盘价: {kline_data[4]}")
                    print(f"  成交量: {kline_data[5]}")
                    print(f"  成交额: {kline_data[6]}")
                    print(f"  其他字段: {kline_data[7:]}")
        print("-" * 50)
    except Exception as e:
        print(f"解析错误: {e}")
        print(f"原始消息: {message}")

def on_error(ws, error):
    print(f"错误: {error}")

def on_close(ws, close_status_code, close_msg):
    print("连接关闭")

def on_open(ws):
    print("连接打开")
    # 订阅1分钟K线数据 - 使用正确的频道格式
    subscribe_msg = {
        "op": "subscribe",
        "args": [{"channel": "candle1M", "instId": "BTC-USDT"}]
    }
    ws.send(json.dumps(subscribe_msg))
    print("已订阅BTC-USDT 1分钟K线 (candle1M)")

if __name__ == "__main__":
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp("wss://ws.okx.com:8443/ws/v5/public",
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close,
                                on_open=on_open)
    
    try:
        ws.run_forever()
    except KeyboardInterrupt:
        print("程序被用户中断")
        ws.close()
