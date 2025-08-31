#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OKX 实时K线技术分析器
Real-time K-line Technical Analyzer for OKX
========================

功能特点:
- 实时WebSocket数据流
- 动态图表更新 
- 六大技术指标实时计算
- 智能买卖信号检测
- 专业级图表界面

技术指标:
- MACD (平滑异同平均线)
- KDJ (随机指标)
- RSI (相对强弱指数) 
- Williams %R (威廉指标)
- BBI (多空指标)
- ZLMM (零滞后动量指标)

作者: GitHub Copilot
版本: 2.0 (实时版)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from matplotlib.animation import FuncAnimation
import pandas as pd
import numpy as np
import requests
import json
import websocket
import threading
import time
from datetime import datetime, timedelta
import queue
import logging
from typing import Dict, List, Tuple, Optional
import warnings

# 忽略matplotlib警告
warnings.filterwarnings('ignore', category=UserWarning)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TechnicalIndicators:
    """技术指标计算类"""
    
    @staticmethod
    def calculate_macd(data: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算MACD指标"""
        ema_fast = data.ewm(span=fast_period).mean()
        ema_slow = data.ewm(span=slow_period).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def calculate_kdj(high: pd.Series, low: pd.Series, close: pd.Series, n: int = 9, m1: int = 3, m2: int = 3) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算KDJ指标"""
        lowest_low = low.rolling(window=n).min()
        highest_high = high.rolling(window=n).max()
        rsv = (close - lowest_low) / (highest_high - lowest_low) * 100
        rsv = rsv.fillna(50)
        
        k = rsv.ewm(alpha=1/m1).mean()
        d = k.ewm(alpha=1/m2).mean()
        j = 3 * k - 2 * d
        
        return k, d, j
    
    @staticmethod
    def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """计算RSI指标"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """计算Williams %R指标"""
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()
        williams_r = (highest_high - close) / (highest_high - lowest_low) * -100
        return williams_r
    
    @staticmethod
    def calculate_bbi(close: pd.Series, periods: List[int] = [3, 6, 12, 24]) -> pd.Series:
        """计算BBI多空指标"""
        ma_sum = sum(close.rolling(window=period).mean() for period in periods)
        bbi = ma_sum / len(periods)
        return bbi
    
    @staticmethod
    def calculate_zlmm(close: pd.Series, period: int = 21) -> pd.Series:
        """计算零滞后动量指标"""
        momentum = close.pct_change(period) * 100
        zlmm = momentum.rolling(window=5).mean()
        return zlmm

class RealTimeDataFeed:
    """实时数据获取类"""
    
    def __init__(self, symbol: str = "BTC-USDT", interval: str = "1m"):
        self.symbol = symbol
        self.interval = interval
        self.ws = None
        self.data_queue = queue.Queue()
        self.is_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.reconnect_timer = None
        self.ping_timer = None
        self.last_message_time = time.time()
        self.connection_timeout = 30  # 30秒无消息判断为断线
        
    def on_message(self, ws, message):
        """WebSocket消息处理"""
        try:
            self.last_message_time = time.time()
            logger.debug(f"Raw message received: {message}")
            
            data = json.loads(message)
            logger.debug(f"Parsed message: {data}")
            
            # 处理ping消息
            if 'event' in data and data['event'] == 'pong':
                logger.debug("Received pong from server")
                return
                
            # 处理订阅确认
            if 'event' in data:
                if data['event'] == 'subscribe':
                    logger.info(f"Subscription confirmed: {data}")
                    return
                elif data['event'] == 'error':
                    logger.error(f"Subscription error: {data}")
                    return
            
            # 处理K线数据
            if 'data' in data and len(data['data']) > 0:
                logger.info(f"Received {len(data['data'])} data items")
                for item in data['data']:
                    logger.debug(f"Processing data item: {item}")
                    try:
                        kline_data = {
                            'timestamp': int(item[0]),
                            'open': float(item[1]),
                            'high': float(item[2]),
                            'low': float(item[3]),
                            'close': float(item[4]),
                            'volume': float(item[5])
                        }
                        self.data_queue.put(kline_data)
                        logger.info(f"Added to queue: Close={kline_data['close']}, Volume={kline_data['volume']}")
                    except (ValueError, IndexError) as e:
                        logger.error(f"Error parsing data item {item}: {e}")
            else:
                logger.warning(f"Message received but no data field or empty data: {data}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON message: {e}")
            logger.debug(f"Raw message causing error: {message}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            logger.debug(f"Raw message: {message}")
    
    def on_error(self, ws, error):
        """WebSocket错误处理"""
        logger.error(f"WebSocket error: {error}")
        self.is_connected = False
        # 停止ping定时器
        if self.ping_timer:
            self.ping_timer.cancel()
    
    def on_close(self, ws, close_status_code, close_msg):
        """WebSocket关闭处理"""
        logger.info(f"WebSocket connection closed: code={close_status_code}, msg={close_msg}")
        self.is_connected = False
        # 停止ping定时器
        if self.ping_timer:
            self.ping_timer.cancel()
        # 自动重连
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.schedule_reconnect()
    
    def on_open(self, ws):
        """WebSocket连接成功"""
        logger.info("WebSocket connection opened")
        self.is_connected = True
        self.reconnect_attempts = 0
        self.last_message_time = time.time()
        
        # 订阅K线数据 - 修正订阅格式
        channel_name = f"candle{self.interval}"
        subscribe_msg = {
            "op": "subscribe",
            "args": [{
                "channel": channel_name,
                "instId": self.symbol
            }]
        }
        
        logger.info(f"Sending subscription: {subscribe_msg}")
        ws.send(json.dumps(subscribe_msg))
        logger.info(f"Subscribed to {self.symbol} {channel_name}")
        
        # 启动ping定时器保持连接
        self.start_ping_timer()
    
    def start_ping_timer(self):
        """启动ping定时器"""
        def send_ping():
            if self.ws and self.is_connected:
                try:
                    # OKX WebSocket ping格式应该是字符串"ping"
                    self.ws.send("ping")
                    logger.debug("Sent ping to server")
                    # 继续下一次ping
                    self.ping_timer = threading.Timer(25.0, send_ping)
                    self.ping_timer.start()
                except Exception as e:
                    logger.error(f"Error sending ping: {e}")
        
        # 启动ping定时器 (每25秒ping一次)
        self.ping_timer = threading.Timer(25.0, send_ping)
        self.ping_timer.start()
    
    def schedule_reconnect(self):
        """计划重连"""
        if self.reconnect_timer:
            self.reconnect_timer.cancel()
        
        delay = min(5 * (2 ** self.reconnect_attempts), 60)  # 指数退避，最大60秒
        logger.info(f"Scheduling reconnect in {delay} seconds...")
        
        self.reconnect_timer = threading.Timer(delay, self.reconnect)
        self.reconnect_timer.start()
    
    def reconnect(self):
        """重连机制"""
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            logger.info(f"Attempting to reconnect... ({self.reconnect_attempts}/{self.max_reconnect_attempts})")
            self.connect()
        else:
            logger.error("Max reconnection attempts reached")
    
    def connect(self):
        """建立WebSocket连接"""
        try:
            # 如果已经有连接，先关闭
            if self.ws:
                self.ws.close()
            
            # 设置WebSocket调试模式
            websocket.enableTrace(False)
            
            # 创建新连接
            self.ws = websocket.WebSocketApp(
                "wss://ws.okx.com:8443/ws/v5/business",
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
                on_open=self.on_open
            )
            
            # 在新线程中运行，设置ping参数
            wst = threading.Thread(
                target=self.ws.run_forever,
                kwargs={
                    'ping_interval': 30,  # 30秒ping间隔
                    'ping_timeout': 10,   # 10秒ping超时
                    'ping_payload': b'ping'
                }
            )
            wst.daemon = True
            wst.start()
            
            logger.info("WebSocket connection initiated")
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self.schedule_reconnect()
    
    def disconnect(self):
        """断开连接"""
        try:
            self.is_connected = False
            
            # 停止定时器
            if self.ping_timer:
                self.ping_timer.cancel()
                self.ping_timer = None
            
            if self.reconnect_timer:
                self.reconnect_timer.cancel()
                self.reconnect_timer = None
            
            # 关闭WebSocket连接
            if self.ws:
                self.ws.close()
                self.ws = None
                
            logger.info("WebSocket connection closed")
            
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
    
    def check_connection_health(self):
        """检查连接健康状态"""
        current_time = time.time()
        if self.is_connected and (current_time - self.last_message_time) > self.connection_timeout:
            logger.warning("Connection appears dead, forcing reconnect")
            self.is_connected = False
            if self.ws:
                self.ws.close()
    
    def get_data(self) -> Optional[Dict]:
        """获取最新数据"""
        try:
            # 检查连接健康状态
            self.check_connection_health()
            return self.data_queue.get_nowait()
        except queue.Empty:
            return None

class OKXRealTimeAnalyzer:
    """OKX实时K线分析器主类"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("OKX 实时K线技术分析器 v2.0")
        self.root.geometry("1920x1080")
        self.root.configure(bg='#f0f0f0')
        
        # 确保窗口显示在前面且居中
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after_idle(lambda: self.root.attributes('-topmost', False))
        
        # 居中显示窗口
        self.root.update_idletasks()
        width = 1400
        height = 900
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        # 数据存储
        self.df = pd.DataFrame()
        self.max_data_points = 300  # 默认最大数据点数，可以通过界面修改
        
        # 实时数据源
        self.data_feed = None
        self.is_running = False
        
        # 技术指标计算器
        self.indicators = TechnicalIndicators()
        
        # 图表相关
        self.fig = None
        self.canvas = None
        self.animation = None
        
        # 信号检测
        self.buy_signals = []
        self.sell_signals = []
        self.hold_periods = []
        
        self.setup_ui()
        self.setup_chart()
        
    def setup_ui(self):
        """设置用户界面"""
        # 主容器
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建左右布局
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        # 控制面板（左上）
        control_frame = ttk.LabelFrame(left_frame, text="实时控制面板", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 第一行控件
        row1_frame = ttk.Frame(control_frame)
        row1_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(row1_frame, text="交易对:").pack(side=tk.LEFT, padx=(0, 5))
        self.symbol_var = tk.StringVar(value="BTC-USDT")
        symbol_combo = ttk.Combobox(row1_frame, textvariable=self.symbol_var, width=12)
        symbol_combo['values'] = ('BTC-USDT', 'ETH-USDT', 'SOL-USDT', 'ADA-USDT', 'CRO-USDT', 'LINK-USDT')
        symbol_combo.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(row1_frame, text="时间周期:").pack(side=tk.LEFT, padx=(0, 5))
        self.interval_var = tk.StringVar(value="1m")
        interval_combo = ttk.Combobox(row1_frame, textvariable=self.interval_var, width=8)
        interval_combo['values'] = ('1m', '3m', '5m', '15m', '30m', '1H', '2H', '4H', '1D')
        interval_combo.pack(side=tk.LEFT, padx=(0, 20))
        
        # 连接状态指示器和详细信息
        status_frame = ttk.Frame(row1_frame)
        status_frame.pack(side=tk.LEFT, padx=(20, 0))
        
        ttk.Label(status_frame, text="连接状态:").pack(side=tk.LEFT, padx=(0, 5))
        self.status_var = tk.StringVar(value="🔴 未连接")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, foreground="red")
        status_label.pack(side=tk.LEFT)
        
        # 添加更明显的状态显示
        self.big_status_var = tk.StringVar(value="等待启动...")
        big_status_label = ttk.Label(status_frame, textvariable=self.big_status_var, 
                                   font=("Arial", 12, "bold"), foreground="blue")
        big_status_label.pack(side=tk.LEFT, padx=(20, 0))
        
        # 连接详情按钮
        detail_btn = ttk.Button(status_frame, text="详情", command=self.show_connection_details, width=6)
        detail_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # 第二行控件
        row2_frame = ttk.Frame(control_frame)
        row2_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.start_btn = ttk.Button(row2_frame, text="🚀 开始实时分析", command=self.start_realtime)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(row2_frame, text="⏹️ 停止分析", command=self.stop_realtime, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_btn = ttk.Button(row2_frame, text="🗑️ 清空数据", command=self.clear_data)
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 20))
        
        # 数据量选择
        ttk.Label(row2_frame, text="数据量:").pack(side=tk.LEFT, padx=(0, 5))
        self.data_points_var = tk.StringVar(value="300")
        data_points_combo = ttk.Combobox(row2_frame, textvariable=self.data_points_var, width=8)
        data_points_combo['values'] = ('300', '1000', '2000')
        data_points_combo['state'] = 'readonly'  # 只读，防止输入其他值
        data_points_combo.pack(side=tk.LEFT, padx=(0, 5))
        data_points_combo.bind('<<ComboboxSelected>>', self.on_data_points_changed)
        
        ttk.Label(row2_frame, text="个数据点").pack(side=tk.LEFT)
        
        # 实时信息显示
        info_frame = ttk.LabelFrame(row2_frame, text="实时信息", padding="5")
        info_frame.pack(side=tk.RIGHT)
        
        self.price_var = tk.StringVar(value="价格: --")
        ttk.Label(info_frame, textvariable=self.price_var, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 10))
        
        self.signal_var = tk.StringVar(value="信号: --")
        ttk.Label(info_frame, textvariable=self.signal_var, font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        
        # 技术指标信号显示面板（右侧）
        indicators_frame = ttk.LabelFrame(right_frame, text="技术指标信号", padding="10")
        indicators_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建垂直排列的指标信号显示
        signals_container = ttk.Frame(indicators_frame)
        signals_container.pack(fill=tk.BOTH, expand=True)
        
        # MACD信号
        macd_frame = ttk.Frame(signals_container)
        macd_frame.pack(fill=tk.X, pady=5)
        ttk.Label(macd_frame, text="MACD", font=("Arial", 12, "bold")).pack()
        self.macd_signal_var = tk.StringVar(value="⚪")
        self.macd_signal_label = ttk.Label(macd_frame, textvariable=self.macd_signal_var, font=("Arial", 24))
        self.macd_signal_label.pack()
        
        # RSI信号
        rsi_frame = ttk.Frame(signals_container)
        rsi_frame.pack(fill=tk.X, pady=5)
        ttk.Label(rsi_frame, text="RSI", font=("Arial", 12, "bold")).pack()
        self.rsi_signal_var = tk.StringVar(value="⚪")
        self.rsi_signal_label = ttk.Label(rsi_frame, textvariable=self.rsi_signal_var, font=("Arial", 24))
        self.rsi_signal_label.pack()
        
        # KDJ信号
        kdj_frame = ttk.Frame(signals_container)
        kdj_frame.pack(fill=tk.X, pady=5)
        ttk.Label(kdj_frame, text="KDJ", font=("Arial", 12, "bold")).pack()
        self.kdj_signal_var = tk.StringVar(value="⚪")
        self.kdj_signal_label = ttk.Label(kdj_frame, textvariable=self.kdj_signal_var, font=("Arial", 24))
        self.kdj_signal_label.pack()
        
        # Williams %R信号
        williams_frame = ttk.Frame(signals_container)
        williams_frame.pack(fill=tk.X, pady=5)
        ttk.Label(williams_frame, text="Williams %R", font=("Arial", 12, "bold")).pack()
        self.williams_signal_var = tk.StringVar(value="⚪")
        self.williams_signal_label = ttk.Label(williams_frame, textvariable=self.williams_signal_var, font=("Arial", 24))
        self.williams_signal_label.pack()
        
        # BBI信号
        bbi_frame = ttk.Frame(signals_container)
        bbi_frame.pack(fill=tk.X, pady=5)
        ttk.Label(bbi_frame, text="BBI", font=("Arial", 12, "bold")).pack()
        self.bbi_signal_var = tk.StringVar(value="⚪")
        self.bbi_signal_label = ttk.Label(bbi_frame, textvariable=self.bbi_signal_var, font=("Arial", 24))
        self.bbi_signal_label.pack()
        
        # ZLMM信号
        zlmm_frame = ttk.Frame(signals_container)
        zlmm_frame.pack(fill=tk.X, pady=5)
        ttk.Label(zlmm_frame, text="ZLMM", font=("Arial", 12, "bold")).pack()
        self.zlmm_signal_var = tk.StringVar(value="⚪")
        self.zlmm_signal_label = ttk.Label(zlmm_frame, textvariable=self.zlmm_signal_var, font=("Arial", 24))
        self.zlmm_signal_label.pack()
        
        # 图表容器（左下）
        self.chart_frame = ttk.LabelFrame(left_frame, text="实时K线图表", padding="5")
        self.chart_frame.pack(fill=tk.BOTH, expand=True)
        
    def setup_chart(self):
        """设置图表"""
        # 创建matplotlib图形
        plt.style.use('dark_background')
        self.fig = Figure(figsize=(14, 8), dpi=100, facecolor='#2E2E2E')
        
        # 创建子图 - 增加到7个子图（包括BBI独立图表）
        gs = self.fig.add_gridspec(7, 1, height_ratios=[3, 1, 1, 1, 1, 1, 1], hspace=0.3)
        
        self.ax_main = self.fig.add_subplot(gs[0])  # 主图 - K线
        self.ax_bbi = self.fig.add_subplot(gs[1])   # BBI独立图表
        self.ax_rsi = self.fig.add_subplot(gs[2])   # RSI
        self.ax_williams = self.fig.add_subplot(gs[3])  # Williams %R
        self.ax_macd = self.fig.add_subplot(gs[4])  # MACD
        self.ax_kdj = self.fig.add_subplot(gs[5])   # KDJ
        self.ax_zlmm = self.fig.add_subplot(gs[6])  # ZLMM
        
        # 设置子图样式
        for ax in [self.ax_main, self.ax_bbi, self.ax_rsi, self.ax_williams, self.ax_macd, self.ax_kdj, self.ax_zlmm]:
            ax.set_facecolor('#1E1E1E')
            ax.grid(True, alpha=0.3, color='#404040')
            ax.tick_params(colors='white')
        
        # 创建canvas
        self.canvas = FigureCanvasTkAgg(self.fig, self.chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def get_historical_data(self, symbol: str, interval: str, limit: int = None) -> pd.DataFrame:
        """获取历史数据初始化"""
        try:
            # 如果没有指定limit，使用当前设置的max_data_points
            if limit is None:
                limit = self.max_data_points
                
            url = "https://www.okx.com/api/v5/market/candles"
            params = {
                'instId': symbol,
                'bar': interval,
                'limit': limit
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data['code'] != '0':
                raise Exception(f"API Error: {data['msg']}")
            
            # 处理数据
            df = pd.DataFrame(data['data'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote', 'confirm'])
            df = df.astype({
                'timestamp': 'int64',
                'open': 'float64',
                'high': 'float64', 
                'low': 'float64',
                'close': 'float64',
                'volume': 'float64'
            })
            
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            logger.info(f"Historical data loaded: {len(df)} records")
            return df
            
        except Exception as e:
            logger.error(f"Failed to get historical data: {e}")
            return pd.DataFrame()
    
    def calculate_indicators(self):
        """计算技术指标"""
        if len(self.df) < 30:
            return
        
        try:
            # 计算各项指标
            macd, signal, histogram = self.indicators.calculate_macd(self.df['close'])
            k, d, j = self.indicators.calculate_kdj(self.df['high'], self.df['low'], self.df['close'])
            rsi = self.indicators.calculate_rsi(self.df['close'])
            williams_r = self.indicators.calculate_williams_r(self.df['high'], self.df['low'], self.df['close'])
            bbi = self.indicators.calculate_bbi(self.df['close'])
            zlmm = self.indicators.calculate_zlmm(self.df['close'])
            
            # 存储指标
            self.df['macd'] = macd
            self.df['signal'] = signal
            self.df['histogram'] = histogram
            self.df['k'] = k
            self.df['d'] = d
            self.df['j'] = j
            self.df['rsi'] = rsi
            self.df['williams_r'] = williams_r
            self.df['bbi'] = bbi
            self.df['zlmm'] = zlmm
            
            # 检测信号
            self.detect_signals()
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
    
    def detect_signals(self):
        """检测买卖信号"""
        if len(self.df) < 50:
            return
        
        try:
            # 重置信号
            self.buy_signals = []
            self.sell_signals = []
            
            for i in range(30, len(self.df)):
                # 买入信号条件（6个指标同时确认）
                buy_conditions = [
                    # MACD金叉且在零轴上方
                    (self.df.iloc[i]['macd'] > self.df.iloc[i]['signal'] and 
                     self.df.iloc[i-1]['macd'] <= self.df.iloc[i-1]['signal'] and
                     self.df.iloc[i]['macd'] > 0),
                    
                    # KDJ指标：K>D且未超买，或从超卖区向上
                    (self.df.iloc[i]['k'] > self.df.iloc[i]['d'] and 
                     (self.df.iloc[i]['k'] < 80 or self.df.iloc[i-5]['k'] < 20)),
                    
                    # RSI > 50或从超卖区回升
                    (self.df.iloc[i]['rsi'] > 50 or 
                     (self.df.iloc[i]['rsi'] > 30 and self.df.iloc[i-5]['rsi'] < 30)),
                    
                    # Williams %R > -50或从超卖区向上
                    (self.df.iloc[i]['williams_r'] > -50 or 
                     (self.df.iloc[i]['williams_r'] > -80 and self.df.iloc[i-5]['williams_r'] < -80)),
                    
                    # 价格在BBI上方
                    self.df.iloc[i]['close'] > self.df.iloc[i]['bbi'],
                    
                    # ZLMM动量为正值
                    self.df.iloc[i]['zlmm'] > 0
                ]
                
                if all(buy_conditions):
                    self.buy_signals.append(i)
                
                # 卖出信号条件（4个以上条件满足）
                sell_conditions = [
                    self.df.iloc[i]['rsi'] > 70,  # RSI超买
                    self.df.iloc[i]['k'] > 80 and self.df.iloc[i]['d'] > 80,  # KDJ超买
                    self.df.iloc[i]['williams_r'] > -20,  # Williams超买
                    (self.df.iloc[i]['macd'] < self.df.iloc[i]['signal'] and 
                     self.df.iloc[i-1]['macd'] >= self.df.iloc[i-1]['signal']),  # MACD死叉
                    abs(self.df.iloc[i]['close'] - self.df.iloc[i]['bbi']) / self.df.iloc[i]['bbi'] > 0.05,  # 价格偏离BBI
                    self.df.iloc[i]['zlmm'] < 0  # 动量转负
                ]
                
                if sum(sell_conditions) >= 4:
                    self.sell_signals.append(i)
            
            # 计算持有期间
            self.calculate_hold_periods()
            
        except Exception as e:
            logger.error(f"Error detecting signals: {e}")
    
    def calculate_hold_periods(self):
        """计算持有期间"""
        self.hold_periods = []
        
        for buy_idx in self.buy_signals:
            # 找到对应的卖出信号
            sell_idx = None
            for sell in self.sell_signals:
                if sell > buy_idx:
                    sell_idx = sell
                    break
            
            # 如果没找到卖出信号，使用最大持有期（20个周期）
            if sell_idx is None:
                sell_idx = min(buy_idx + 20, len(self.df) - 1)
            
            self.hold_periods.append((buy_idx, sell_idx))
    
    def update_chart(self, frame=None):
        """更新图表"""
        if self.df.empty:
            logger.info("Chart update skipped: DataFrame is empty")
            return
        
        try:
            logger.info(f"Updating chart with {len(self.df)} data points - DataFrame shape: {self.df.shape}")
            
            # 强制计算技术指标（确保有数据）
            if len(self.df) >= 50:
                self.calculate_indicators()
            
            # 清空所有子图
            self.ax_main.clear()
            self.ax_bbi.clear()
            self.ax_rsi.clear()
            self.ax_williams.clear()
            self.ax_macd.clear()
            self.ax_kdj.clear()
            self.ax_zlmm.clear()
            
            # 设置颜色和样式
            for ax in [self.ax_main, self.ax_bbi, self.ax_rsi, self.ax_williams, self.ax_macd, self.ax_kdj, self.ax_zlmm]:
                ax.set_facecolor('#1E1E1E')
                ax.grid(True, alpha=0.3, color='#404040')
                ax.tick_params(colors='white')
            
            # 获取最新的数据段
            plot_data = self.df.tail(min(self.max_data_points, len(self.df)))  # 显示最近设定数量的数据点
            x_data = range(len(plot_data))
            
            logger.info(f"Plot data shape: {plot_data.shape}, columns: {list(plot_data.columns)}")
            
            # 1. 主图 - 简化的价格线图
            if 'close' in plot_data.columns:
                self.ax_main.plot(x_data, plot_data['close'], label='价格', color='lime', linewidth=2)
                self.ax_main.set_title(f'BTC-USDT 实时价格 ({len(plot_data)}条数据)', color='white', fontsize=12)
                self.ax_main.legend(loc='upper left')
                logger.info(f"Plotted price data: min={plot_data['close'].min()}, max={plot_data['close'].max()}")
            
            # 2. BBI（独立图表）
            bbi_plotted = False
            if 'bbi' in plot_data.columns and len(plot_data) >= 30:
                # 过滤掉NaN值
                valid_bbi = plot_data['bbi'].dropna()
                logger.info(f"BBI data check: total={len(plot_data['bbi'])}, valid={len(valid_bbi)}, first_few_values={plot_data['bbi'].head(10).tolist()}")
                
                if len(valid_bbi) > 0:
                    # 使用有效的bbi数据进行绘图
                    valid_indices = valid_bbi.index
                    bbi_x_data = [x_data[plot_data.index.get_loc(idx)] for idx in valid_indices]
                    
                    self.ax_bbi.plot(bbi_x_data, valid_bbi.values, label='BBI', color='yellow', linewidth=2)
                    # 绘制价格线用于对比
                    self.ax_bbi.plot(x_data, plot_data['close'], label='价格', color='lime', linewidth=1, alpha=0.7)
                    
                    bbi_plotted = True
                    logger.info(f"BBI plotted successfully with {len(valid_bbi)} points")
                else:
                    logger.warning("BBI data exists but all values are NaN")
            else:
                logger.warning(f"BBI plotting conditions not met: 'bbi' in columns={('bbi' in plot_data.columns)}, data_length={len(plot_data)}")
            
            self.ax_bbi.set_title('BBI 多空指标' + (' - 已绘制' if bbi_plotted else ' - 无数据'), color='white', fontsize=10)
            self.ax_bbi.set_ylabel('BBI', color='white')
            if bbi_plotted:
                self.ax_bbi.legend(loc='upper left')
            else:
                # 显示占位文本
                self.ax_bbi.text(0.5, 0.5, '等待BBI数据...', transform=self.ax_bbi.transAxes, 
                               ha='center', va='center', color='gray', fontsize=12)
            
            # 3. RSI（独立图表）
            if 'rsi' in plot_data.columns and not plot_data['rsi'].isna().all():
                valid_rsi = plot_data['rsi'].dropna()
                if len(valid_rsi) > 0:
                    self.ax_rsi.plot(valid_rsi.index, valid_rsi.values, label='RSI', color='orange', linewidth=1)
                    self.ax_rsi.axhline(y=70, color='red', linestyle='--', alpha=0.7)
                    self.ax_rsi.axhline(y=30, color='green', linestyle='--', alpha=0.7)
                    self.ax_rsi.set_title('RSI指标', color='white', fontsize=10)
                    self.ax_rsi.set_ylabel('RSI', color='white')
                    self.ax_rsi.legend(loc='upper left')
            else:
                self.ax_rsi.text(0.5, 0.5, '等待RSI数据...', transform=self.ax_rsi.transAxes, 
                               ha='center', va='center', color='white', fontsize=12)
            
            # 4. Williams %R（独立图表）
            if 'williams_r' in plot_data.columns and not plot_data['williams_r'].isna().all():
                valid_williams = plot_data['williams_r'].dropna()
                if len(valid_williams) > 0:
                    self.ax_williams.plot(valid_williams.index, valid_williams.values, label='Williams %R', color='purple', linewidth=1)
                    self.ax_williams.axhline(y=-20, color='red', linestyle='--', alpha=0.7)
                    self.ax_williams.axhline(y=-80, color='green', linestyle='--', alpha=0.7)
                    self.ax_williams.set_title('Williams %R指标', color='white', fontsize=10)
                    self.ax_williams.set_ylabel('Williams %R', color='white')
                    self.ax_williams.legend(loc='upper left')
            else:
                self.ax_williams.text(0.5, 0.5, '等待Williams %R数据...', transform=self.ax_williams.transAxes, 
                                    ha='center', va='center', color='white', fontsize=12)
            
            # 5. MACD（如果有数据）
            if 'macd' in plot_data.columns and not plot_data['macd'].isna().all():
                valid_macd = plot_data['macd'].dropna()
                if len(valid_macd) > 0:
                    self.ax_macd.plot(valid_macd.index, valid_macd.values, label='MACD', color='blue', linewidth=1)
                    if 'signal' in plot_data.columns:
                        valid_signal = plot_data['signal'].dropna()
                        if len(valid_signal) > 0:
                            self.ax_macd.plot(valid_signal.index, valid_signal.values, label='Signal', color='red', linewidth=1)
                    self.ax_macd.set_title('MACD指标', color='white', fontsize=10)
                    self.ax_macd.set_ylabel('MACD', color='white')
                    self.ax_macd.legend(loc='upper left')
            else:
                self.ax_macd.text(0.5, 0.5, '等待MACD数据...', transform=self.ax_macd.transAxes, 
                                ha='center', va='center', color='white', fontsize=12)
            
            # 6. KDJ（如果有数据）
            if 'k' in plot_data.columns and not plot_data['k'].isna().all():
                for line, color in [('k', 'yellow'), ('d', 'blue'), ('j', 'red')]:
                    if line in plot_data.columns:
                        valid_data = plot_data[line].dropna()
                        if len(valid_data) > 0:
                            self.ax_kdj.plot(valid_data.index, valid_data.values, label=line.upper(), color=color, linewidth=1)
                
                self.ax_kdj.axhline(y=80, color='red', linestyle='--', alpha=0.7)
                self.ax_kdj.axhline(y=20, color='green', linestyle='--', alpha=0.7)
                self.ax_kdj.set_title('KDJ指标', color='white', fontsize=10)
                self.ax_kdj.set_ylabel('KDJ', color='white')
                self.ax_kdj.legend(loc='upper left')
            else:
                self.ax_kdj.text(0.5, 0.5, '等待KDJ数据...', transform=self.ax_kdj.transAxes, 
                               ha='center', va='center', color='white', fontsize=12)
            
            # 7. ZLMM（独立图表）
            if 'zlmm' in plot_data.columns and not plot_data['zlmm'].isna().all():
                valid_zlmm = plot_data['zlmm'].dropna()
                if len(valid_zlmm) > 0:
                    self.ax_zlmm.plot(valid_zlmm.index, valid_zlmm.values, label='ZLMM', color='cyan', linewidth=1)
                    self.ax_zlmm.axhline(y=0, color='white', linestyle='-', alpha=0.5)
                    self.ax_zlmm.set_title('ZLMM指标', color='white', fontsize=10)
                    self.ax_zlmm.set_ylabel('ZLMM', color='white')
                    self.ax_zlmm.set_xlabel('时间', color='white')
                    self.ax_zlmm.legend(loc='upper left')
            else:
                self.ax_zlmm.text(0.5, 0.5, '等待ZLMM数据...', transform=self.ax_zlmm.transAxes, 
                                ha='center', va='center', color='white', fontsize=12)
            
            # 调整布局
            self.fig.tight_layout()
            self.canvas.draw()
            
            # 更新实时信息
            self.update_info_display()
            
            # 强制刷新画布
            self.canvas.draw()
            self.canvas.flush_events()
            self.root.update_idletasks()
            
            logger.info("Chart updated successfully")
            
        except Exception as e:
            logger.error(f"Error updating chart: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # 获取最新的数据段
            plot_data = self.df.tail(min(self.max_data_points, len(self.df)))  # 显示最近设定数量的数据点
            x_data = range(len(plot_data))
            
            # 1. 主图 - K线图（移除BBI）
            self.plot_candlestick(self.ax_main, plot_data, x_data)
            
            # 绘制买卖信号（如果有足够数据）
            if len(plot_data) >= 30:
                self.plot_signals(self.ax_main, plot_data, x_data)
            
            self.ax_main.set_title(f'实时K线图 ({len(plot_data)}条数据)', color='white', fontsize=12)
            self.ax_main.legend(loc='upper left')
            
            # 2. BBI（独立图表）
            bbi_plotted = False
            if 'bbi' in plot_data.columns and len(plot_data) >= 30:
                # 过滤掉NaN值
                valid_bbi = plot_data['bbi'].dropna()
                logger.info(f"BBI data check: total={len(plot_data['bbi'])}, valid={len(valid_bbi)}, first_few_values={plot_data['bbi'].head(10).tolist()}")
                
                if len(valid_bbi) > 0:
                    # 使用有效的bbi数据进行绘图
                    valid_indices = valid_bbi.index
                    bbi_x_data = [plot_data.index.get_loc(idx) for idx in valid_indices]
                    
                    self.ax_bbi.plot(bbi_x_data, valid_bbi.values, label='BBI', color='yellow', linewidth=2)
                    # 绘制价格线用于对比
                    self.ax_bbi.plot(x_data, plot_data['close'], label='价格', color='lime', linewidth=1, alpha=0.7)
                    
                    # 添加价格突破BBI的信号点
                    for i in range(1, len(plot_data)):
                        if not pd.isna(plot_data.iloc[i]['bbi']) and not pd.isna(plot_data.iloc[i-1]['bbi']):
                            if (plot_data.iloc[i]['close'] > plot_data.iloc[i]['bbi'] and 
                                plot_data.iloc[i-1]['close'] <= plot_data.iloc[i-1]['bbi']):
                                self.ax_bbi.scatter(i, plot_data.iloc[i]['bbi'], color='green', s=50, alpha=0.8)
                            elif (plot_data.iloc[i]['close'] < plot_data.iloc[i]['bbi'] and 
                                  plot_data.iloc[i-1]['close'] >= plot_data.iloc[i-1]['bbi']):
                                self.ax_bbi.scatter(i, plot_data.iloc[i]['bbi'], color='red', s=50, alpha=0.8)
                    
                    bbi_plotted = True
                    logger.info(f"BBI plotted successfully with {len(valid_bbi)} points")
                else:
                    logger.warning("BBI data exists but all values are NaN")
            else:
                logger.warning(f"BBI plotting conditions not met: 'bbi' in columns={('bbi' in plot_data.columns)}, data_length={len(plot_data)}")
            
            self.ax_bbi.set_title('BBI 多空指标' + (' - 已绘制' if bbi_plotted else ' - 无数据'), color='white', fontsize=10)
            self.ax_bbi.set_ylabel('BBI', color='white')
            if bbi_plotted:
                self.ax_bbi.legend(loc='upper left')
            else:
                # 显示占位文本
                self.ax_bbi.text(0.5, 0.5, '等待BBI数据...', transform=self.ax_bbi.transAxes, 
                               ha='center', va='center', color='gray', fontsize=12)
            
            # 3. RSI（独立图表）
            if 'rsi' in plot_data.columns and len(plot_data) >= 14:
                self.ax_rsi.plot(x_data, plot_data['rsi'], label='RSI', color='orange', linewidth=1)
                self.ax_rsi.axhline(y=70, color='red', linestyle='--', alpha=0.7)
                self.ax_rsi.axhline(y=30, color='green', linestyle='--', alpha=0.7)
                self.ax_rsi.axhline(y=50, color='white', linestyle='-', alpha=0.5)
            
            self.ax_rsi.set_title('RSI', color='white', fontsize=10)
            self.ax_rsi.set_ylabel('RSI', color='white')
            self.ax_rsi.legend(loc='upper left')
            
            # 4. Williams %R（独立图表）
            if 'williams_r' in plot_data.columns:
                self.ax_williams.plot(x_data, plot_data['williams_r'], label='Williams %R', color='purple', linewidth=1)
                self.ax_williams.axhline(y=-20, color='red', linestyle='--', alpha=0.7)
                self.ax_williams.axhline(y=-80, color='green', linestyle='--', alpha=0.7)
                self.ax_williams.axhline(y=-50, color='white', linestyle='-', alpha=0.5)
            
            self.ax_williams.set_title('Williams %R', color='white', fontsize=10)
            self.ax_williams.set_ylabel('Williams %R', color='white')
            self.ax_williams.legend(loc='upper left')
            
            # 5. MACD
            if 'macd' in plot_data.columns:
                self.ax_macd.plot(x_data, plot_data['macd'], label='MACD', color='blue', linewidth=1)
                self.ax_macd.plot(x_data, plot_data['signal'], label='Signal', color='red', linewidth=1)
                
                # MACD柱状图，买入信号时显示黄色
                colors = []
                for i, idx in enumerate(plot_data.index):
                    original_idx = self.df.index.get_loc(idx)
                    if original_idx in self.buy_signals:
                        colors.append('yellow')
                    elif plot_data.iloc[i]['histogram'] >= 0:
                        colors.append('red')
                    else:
                        colors.append('green')
                
                self.ax_macd.bar(x_data, plot_data['histogram'], alpha=0.7, color=colors, width=0.8)
                self.ax_macd.axhline(y=0, color='white', linestyle='-', alpha=0.5)
            
            self.ax_macd.set_title('MACD', color='white', fontsize=10)
            self.ax_macd.set_ylabel('MACD', color='white')
            self.ax_macd.legend(loc='upper left')
            
            # 6. KDJ
            if 'k' in plot_data.columns:
                self.ax_kdj.plot(x_data, plot_data['k'], label='K', color='yellow', linewidth=1)
                self.ax_kdj.plot(x_data, plot_data['d'], label='D', color='blue', linewidth=1)
                self.ax_kdj.plot(x_data, plot_data['j'], label='J', color='red', linewidth=1)
                self.ax_kdj.axhline(y=80, color='red', linestyle='--', alpha=0.7)
                self.ax_kdj.axhline(y=20, color='green', linestyle='--', alpha=0.7)
                self.ax_kdj.axhline(y=50, color='white', linestyle='-', alpha=0.5)
            
            self.ax_kdj.set_title('KDJ', color='white', fontsize=10)
            self.ax_kdj.set_ylabel('KDJ', color='white')
            self.ax_kdj.legend(loc='upper left')
            
            # 7. ZLMM（独立图表）
            if 'zlmm' in plot_data.columns:
                self.ax_zlmm.plot(x_data, plot_data['zlmm'], label='ZLMM', color='cyan', linewidth=1)
                self.ax_zlmm.axhline(y=0, color='white', linestyle='-', alpha=0.5)
                # 添加动量变化的颜色填充
                zlmm_data = plot_data['zlmm']
                self.ax_zlmm.fill_between(x_data, 0, zlmm_data, 
                                         where=(zlmm_data >= 0), 
                                         color='green', alpha=0.3, interpolate=True)
                self.ax_zlmm.fill_between(x_data, 0, zlmm_data, 
                                         where=(zlmm_data < 0), 
                                         color='red', alpha=0.3, interpolate=True)
            
            self.ax_zlmm.set_title('ZLMM (零滞后动量指标)', color='white', fontsize=10)
            self.ax_zlmm.set_ylabel('ZLMM', color='white')
            self.ax_zlmm.set_xlabel('时间', color='white')
            self.ax_zlmm.legend(loc='upper left')
            
            # 调整布局
            self.fig.tight_layout()
            self.canvas.draw()
            
            # 更新实时信息
            self.update_info_display()
            
            logger.info("Chart updated successfully")
            
        except Exception as e:
            logger.error(f"Error updating chart: {e}")
    
    def plot_candlestick(self, ax, data, x_data):
        """绘制K线图"""
        try:
            for i, (idx, row) in enumerate(data.iterrows()):
                color = 'red' if row['close'] >= row['open'] else 'green'
                
                # 绘制影线
                ax.plot([i, i], [row['low'], row['high']], color=color, linewidth=1)
                
                # 绘制实体
                body_height = abs(row['close'] - row['open'])
                body_bottom = min(row['open'], row['close'])
                
                rect = plt.Rectangle((i-0.4, body_bottom), 0.8, body_height, 
                                   facecolor=color, edgecolor=color, alpha=0.8)
                ax.add_patch(rect)
        except Exception as e:
            logger.error(f"Error plotting candlestick: {e}")
    
    def plot_signals(self, ax, plot_data, x_data):
        """绘制买卖信号"""
        try:
            # 绘制持有期间背景
            for start_idx, end_idx in self.hold_periods:
                start_pos = None
                end_pos = None
                
                for i, idx in enumerate(plot_data.index):
                    original_idx = self.df.index.get_loc(idx)
                    if original_idx == start_idx:
                        start_pos = i
                    if original_idx == end_idx:
                        end_pos = i
                
                if start_pos is not None and end_pos is not None:
                    ax.axvspan(start_pos, end_pos, alpha=0.2, color='magenta', label='持有期间')
            
            # 绘制买入信号
            for i, idx in enumerate(plot_data.index):
                original_idx = self.df.index.get_loc(idx)
                if original_idx in self.buy_signals:
                    ax.annotate('↑', xy=(i, plot_data.iloc[i]['low']), 
                              xytext=(i, plot_data.iloc[i]['low'] - plot_data.iloc[i]['low']*0.02),
                              color='red', fontsize=20, ha='center', weight='bold')
                    ax.axvline(x=i, color='yellow', alpha=0.7, linewidth=2, label='买入确认')
            
            # 绘制卖出信号
            for i, idx in enumerate(plot_data.index):
                original_idx = self.df.index.get_loc(idx)
                if original_idx in self.sell_signals:
                    ax.annotate('↓', xy=(i, plot_data.iloc[i]['high']), 
                              xytext=(i, plot_data.iloc[i]['high'] + plot_data.iloc[i]['high']*0.02),
                              color='green', fontsize=20, ha='center', weight='bold')
        
        except Exception as e:
            logger.error(f"Error plotting signals: {e}")
    
    def get_indicator_signals(self):
        """获取各个指标的信号"""
        signals = {'macd': 0, 'rsi': 0, 'kdj': 0, 'williams': 0, 'bbi': 0, 'zlmm': 0}  # 1=看多, -1=看空, 0=中性
        
        if len(self.df) < 2:
            return signals
            
        try:
            latest = self.df.iloc[-1]
            previous = self.df.iloc[-2] if len(self.df) > 1 else latest
            
            # MACD信号判断
            if not pd.isna(latest['macd']) and not pd.isna(latest['signal']):
                if latest['macd'] > latest['signal'] and previous['macd'] <= previous['signal']:
                    signals['macd'] = 1  # 金叉看多
                elif latest['macd'] < latest['signal'] and previous['macd'] >= previous['signal']:
                    signals['macd'] = -1  # 死叉看空
                elif latest['macd'] > latest['signal']:
                    signals['macd'] = 1  # 维持看多
                elif latest['macd'] < latest['signal']:
                    signals['macd'] = -1  # 维持看空
            
            # RSI信号判断
            if not pd.isna(latest['rsi']):
                if latest['rsi'] < 30:
                    signals['rsi'] = 1  # 超卖看多
                elif latest['rsi'] > 70:
                    signals['rsi'] = -1  # 超买看空
                elif latest['rsi'] > 50:
                    signals['rsi'] = 1  # 强势看多
                elif latest['rsi'] < 50:
                    signals['rsi'] = -1  # 弱势看空
            
            # KDJ信号判断
            if not pd.isna(latest['k']) and not pd.isna(latest['d']):
                if latest['k'] > latest['d'] and previous['k'] <= previous['d']:
                    signals['kdj'] = 1  # K线上穿D线看多
                elif latest['k'] < latest['d'] and previous['k'] >= previous['d']:
                    signals['kdj'] = -1  # K线下穿D线看空
                elif latest['k'] > latest['d']:
                    signals['kdj'] = 1  # 维持看多
                elif latest['k'] < latest['d']:
                    signals['kdj'] = -1  # 维持看空
            
            # Williams %R信号判断
            if not pd.isna(latest['williams_r']):
                if latest['williams_r'] > -20:
                    signals['williams'] = -1  # 超买看空
                elif latest['williams_r'] < -80:
                    signals['williams'] = 1  # 超卖看多
                elif latest['williams_r'] > -50:
                    signals['williams'] = -1  # 偏弱势看空
                elif latest['williams_r'] < -50:
                    signals['williams'] = 1  # 偏强势看多
            
            # BBI信号判断
            if not pd.isna(latest['bbi']):
                if latest['close'] > latest['bbi'] and previous['close'] <= previous['bbi']:
                    signals['bbi'] = 1  # 价格突破BBI看多
                elif latest['close'] < latest['bbi'] and previous['close'] >= previous['bbi']:
                    signals['bbi'] = -1  # 价格跌破BBI看空
                elif latest['close'] > latest['bbi']:
                    signals['bbi'] = 1  # 维持看多
                elif latest['close'] < latest['bbi']:
                    signals['bbi'] = -1  # 维持看空
            
            # ZLMM信号判断
            if not pd.isna(latest['zlmm']) and not pd.isna(previous['zlmm']):
                if latest['zlmm'] > 0 and previous['zlmm'] <= 0:
                    signals['zlmm'] = 1  # 零滞后动量转正看多
                elif latest['zlmm'] < 0 and previous['zlmm'] >= 0:
                    signals['zlmm'] = -1  # 零滞后动量转负看空
                elif latest['zlmm'] > 0:
                    signals['zlmm'] = 1  # 维持看多
                elif latest['zlmm'] < 0:
                    signals['zlmm'] = -1  # 维持看空
                    
        except Exception as e:
            logger.error(f"Error calculating indicator signals: {e}")
            
        return signals
    
    def update_indicator_displays(self):
        """更新指标信号显示"""
        signals = self.get_indicator_signals()
        
        # 更新MACD显示
        if signals['macd'] == 1:
            self.macd_signal_var.set("🟢↗")
            self.macd_signal_label.configure(foreground="green")
        elif signals['macd'] == -1:
            self.macd_signal_var.set("🔴↘")
            self.macd_signal_label.configure(foreground="red")
        else:
            self.macd_signal_var.set("⚪➡")
            self.macd_signal_label.configure(foreground="gray")
        
        # 更新RSI显示
        if signals['rsi'] == 1:
            self.rsi_signal_var.set("🟢↗")
            self.rsi_signal_label.configure(foreground="green")
        elif signals['rsi'] == -1:
            self.rsi_signal_var.set("🔴↘")
            self.rsi_signal_label.configure(foreground="red")
        else:
            self.rsi_signal_var.set("⚪➡")
            self.rsi_signal_label.configure(foreground="gray")
        
        # 更新KDJ显示
        if signals['kdj'] == 1:
            self.kdj_signal_var.set("🟢↗")
            self.kdj_signal_label.configure(foreground="green")
        elif signals['kdj'] == -1:
            self.kdj_signal_var.set("🔴↘")
            self.kdj_signal_label.configure(foreground="red")
        else:
            self.kdj_signal_var.set("⚪➡")
            self.kdj_signal_label.configure(foreground="gray")
        
        # 更新Williams %R显示
        if signals['williams'] == 1:
            self.williams_signal_var.set("🟢↗")
            self.williams_signal_label.configure(foreground="green")
        elif signals['williams'] == -1:
            self.williams_signal_var.set("🔴↘")
            self.williams_signal_label.configure(foreground="red")
        else:
            self.williams_signal_var.set("⚪➡")
            self.williams_signal_label.configure(foreground="gray")
        
        # 更新BBI显示
        if signals['bbi'] == 1:
            self.bbi_signal_var.set("🟢↗")
            self.bbi_signal_label.configure(foreground="green")
        elif signals['bbi'] == -1:
            self.bbi_signal_var.set("🔴↘")
            self.bbi_signal_label.configure(foreground="red")
        else:
            self.bbi_signal_var.set("⚪➡")
            self.bbi_signal_label.configure(foreground="gray")
        
        # 更新ZLMM显示
        if signals['zlmm'] == 1:
            self.zlmm_signal_var.set("🟢↗")
            self.zlmm_signal_label.configure(foreground="green")
        elif signals['zlmm'] == -1:
            self.zlmm_signal_var.set("🔴↘")
            self.zlmm_signal_label.configure(foreground="red")
        else:
            self.zlmm_signal_var.set("⚪➡")
            self.zlmm_signal_label.configure(foreground="gray")
    
    def update_info_display(self):
        """更新实时信息显示"""
        if not self.df.empty:
            latest = self.df.iloc[-1]
            self.price_var.set(f"价格: ${latest['close']:.4f}")
            
            # 检查最新信号
            latest_idx = len(self.df) - 1
            if latest_idx in self.buy_signals:
                self.signal_var.set("信号: 🔴 买入")
            elif latest_idx in self.sell_signals:
                self.signal_var.set("信号: 🔻 卖出")
            else:
                self.signal_var.set("信号: ⏸️ 观望")
            
            # 更新技术指标信号显示
            self.update_indicator_displays()
    
    def start_realtime(self):
        """开始实时分析"""
        try:
            symbol = self.symbol_var.get()
            interval = self.interval_var.get()
            
            # 连接诊断
            self.status_var.set("🔍 连接诊断...")
            self.big_status_var.set("🔍 正在诊断连接...")
            logger.info(f"Starting connection diagnostics for {symbol} {interval}")
            
            # 测试基础网络连接
            try:
                import socket
                socket.create_connection(("ws.okx.com", 8443), timeout=10)
                logger.info("Network connectivity test passed")
            except Exception as e:
                logger.error(f"Network connectivity test failed: {e}")
                messagebox.showerror("网络错误", f"无法连接到OKX服务器: {e}")
                self.big_status_var.set("❌ 网络连接失败")
                return
            
            # 获取历史数据初始化
            self.status_var.set("📊 加载历史数据...")
            self.big_status_var.set(f"📊 正在加载{self.max_data_points}个历史数据...")
            self.df = self.get_historical_data(symbol, interval)
            
            if self.df.empty:
                messagebox.showerror("错误", "无法获取历史数据，请检查网络连接")
                self.status_var.set("❌ 数据获取失败")
                self.big_status_var.set("❌ 数据获取失败")
                return
            
            logger.info(f"Historical data loaded: {len(self.df)} records")
            
            # 计算初始指标
            self.status_var.set("🔢 计算技术指标...")
            self.big_status_var.set("🔢 正在计算技术指标...")
            self.calculate_indicators()
            
            # 启动实时数据源
            self.status_var.set("🔌 建立WebSocket连接...")
            self.big_status_var.set("🔌 正在建立WebSocket连接...")
            self.data_feed = RealTimeDataFeed(symbol, interval)
            self.data_feed.connect()
            
            # 等待连接建立
            connection_wait = 0
            while connection_wait < 10 and not self.data_feed.is_connected:
                time.sleep(0.5)
                connection_wait += 0.5
                self.status_var.set(f"⏳ 等待连接... {connection_wait:.1f}s")
                self.root.update()
            
            if not self.data_feed.is_connected:
                logger.warning("WebSocket connection not established within timeout")
                self.status_var.set("⚠️ 连接超时，但继续运行")
            
            # 启动更新线程
            self.is_running = True
            self.update_thread = threading.Thread(target=self.realtime_update_loop)
            self.update_thread.daemon = True
            self.update_thread.start()
            
            # 启动图表动画
            try:
                self.animation = FuncAnimation(
                    self.fig, 
                    self.update_chart, 
                    interval=2000,  # 2秒更新一次
                    blit=False, 
                    cache_frame_data=False,
                    repeat=True
                )
                logger.info("Chart animation started")
                
                # 立即进行一次图表更新
                self.root.after(1000, self.update_chart)
                
            except Exception as e:
                logger.error(f"Failed to start chart animation: {e}")
            
            # 更新界面状态
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            
            if self.data_feed.is_connected:
                self.status_var.set("🟢 实时连接成功")
                self.big_status_var.set(f"🚀 实时分析运行中... ({self.max_data_points}点)")
                logger.info("Real-time analysis started successfully")
                messagebox.showinfo("成功", f"实时分析已启动\n交易对: {symbol}\n周期: {interval}\n数据点: {self.max_data_points}")
            else:
                self.status_var.set("⚠️ 部分功能运行")
                self.big_status_var.set(f"⚠️ 部分功能运行... ({self.max_data_points}点)")
                logger.warning("Real-time analysis started with connection issues")
                messagebox.showwarning("警告", f"历史数据分析正常，但实时连接存在问题\n请检查网络连接\n当前使用{self.max_data_points}个数据点")
            
        except Exception as e:
            logger.error(f"Error starting real-time analysis: {e}")
            self.status_var.set("❌ 启动失败")
            messagebox.showerror("错误", f"启动失败: {e}\n\n可能原因:\n1. 网络连接问题\n2. OKX服务器维护\n3. 防火墙阻止连接")
    
    def realtime_update_loop(self):
        """实时更新循环"""
        connection_check_interval = 0
        
        while self.is_running:
            try:
                if self.data_feed:
                    # 每10秒检查一次连接状态
                    connection_check_interval += 1
                    if connection_check_interval >= 10:
                        self.data_feed.check_connection_health()
                        connection_check_interval = 0
                    
                    if self.data_feed.is_connected:
                        self.status_var.set("🟢 实时连接")
                        current_time = datetime.now().strftime("%H:%M:%S")
                        self.big_status_var.set(f"📈 实时更新中 {current_time}")
                        
                        # 获取新数据
                        new_data = self.data_feed.get_data()
                        if new_data:
                            self.process_new_data(new_data)
                    else:
                        self.status_var.set("🔴 连接断开")
                        self.big_status_var.set("🔄 正在重连...")
                        # 如果连接断开，尝试重连
                        if self.data_feed.reconnect_attempts < self.data_feed.max_reconnect_attempts:
                            if not hasattr(self.data_feed, 'reconnect_timer') or not self.data_feed.reconnect_timer:
                                self.data_feed.schedule_reconnect()
                else:
                    self.status_var.set("🔴 未连接")
                    self.big_status_var.set("❌ 数据源未连接")
                
                time.sleep(1)  # 每秒检查一次
                
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                self.status_var.set("🔴 连接错误")
                time.sleep(5)
    
    def process_new_data(self, new_data):
        """处理新的实时数据"""
        try:
            logger.info(f"Processing new data: Close={new_data['close']}, Volume={new_data['volume']}")
            
            # 转换为DataFrame格式
            new_row = {
                'timestamp': new_data['timestamp'],
                'open': new_data['open'],
                'high': new_data['high'],
                'low': new_data['low'],
                'close': new_data['close'],
                'volume': new_data['volume'],
                'datetime': pd.to_datetime(new_data['timestamp'], unit='ms')
            }
            
            # 检查是否为新的K线或更新现有K线
            if not self.df.empty:
                last_timestamp = self.df.iloc[-1]['timestamp']
                
                if new_data['timestamp'] > last_timestamp:
                    # 新的K线
                    self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
                    logger.info(f"Added new K-line, total data points: {len(self.df)}")
                else:
                    # 更新最后一根K线
                    self.df.iloc[-1] = new_row
                    logger.info(f"Updated last K-line, total data points: {len(self.df)}")
            
            # 限制数据量
            if len(self.df) > self.max_data_points:
                self.df = self.df.tail(self.max_data_points).reset_index(drop=True)
            
            # 重新计算指标
            self.calculate_indicators()
            
        except Exception as e:
            logger.error(f"Error processing new data: {e}")
    
    def stop_realtime(self):
        """停止实时分析"""
        try:
            self.is_running = False
            
            if self.data_feed:
                self.data_feed.disconnect()
                self.data_feed = None
            
            if self.animation:
                self.animation.event_source.stop()
                self.animation = None
            
            # 更新界面状态
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.status_var.set("🔴 已停止")
            
            logger.info("Real-time analysis stopped")
            
        except Exception as e:
            logger.error(f"Error stopping real-time analysis: {e}")
    
    def clear_data(self):
        """清空数据"""
        self.df = pd.DataFrame()
        self.buy_signals = []
        self.sell_signals = []
        self.hold_periods = []
        
        # 清空图表
        for ax in [self.ax_main, self.ax_rsi, self.ax_macd, self.ax_kdj]:
            ax.clear()
            ax.set_facecolor('#1E1E1E')
            ax.grid(True, alpha=0.3, color='#404040')
            ax.tick_params(colors='white')
        
        self.canvas.draw()
        
        # 重置信息显示
        self.price_var.set("价格: --")
        self.signal_var.set("信号: --")
        
        logger.info("Data cleared")
    
    def on_data_points_changed(self, event=None):
        """数据量选择变化时的回调函数"""
        try:
            new_data_points = int(self.data_points_var.get())
            old_data_points = self.max_data_points
            
            self.max_data_points = new_data_points
            logger.info(f"Data points changed from {old_data_points} to {new_data_points}")
            
            # 如果当前有数据且新的数据量小于当前数据量，需要截取
            if not self.df.empty and len(self.df) > new_data_points:
                self.df = self.df.tail(new_data_points).reset_index(drop=True)
                logger.info(f"Truncated data to {new_data_points} points")
                
                # 重新计算指标
                self.calculate_indicators()
                
            # 更新状态显示
            if self.is_running:
                self.big_status_var.set(f"📊 实时分析中 ({new_data_points}点)")
            else:
                self.big_status_var.set(f"等待启动... (将使用{new_data_points}个数据点)")
                
        except ValueError:
            logger.error(f"Invalid data points value: {self.data_points_var.get()}")
            # 重置为之前的值
            self.data_points_var.set(str(self.max_data_points))
    
    def show_connection_details(self):
        """显示连接详细信息"""
        details = []
        
        if self.data_feed:
            details.append(f"交易对: {self.data_feed.symbol}")
            details.append(f"时间周期: {self.data_feed.interval}")
            details.append(f"连接状态: {'已连接' if self.data_feed.is_connected else '未连接'}")
            details.append(f"重连次数: {self.data_feed.reconnect_attempts}/{self.data_feed.max_reconnect_attempts}")
            
            if hasattr(self.data_feed, 'last_message_time'):
                last_msg_ago = time.time() - self.data_feed.last_message_time
                details.append(f"最后消息: {last_msg_ago:.1f}秒前")
            
            details.append(f"数据队列: {self.data_feed.data_queue.qsize()}条消息")
            details.append(f"数据点数: {len(self.df)}条")
        else:
            details.append("数据源: 未初始化")
        
        details.append(f"历史数据: {len(self.df)}条记录")
        details.append(f"运行状态: {'运行中' if self.is_running else '已停止'}")
        
        detail_text = "\n".join(details)
        messagebox.showinfo("连接详情", detail_text)
    
    def on_closing(self):
        """程序关闭处理"""
        try:
            logger.info("Application closing...")
            self.stop_realtime()
            
            # 等待线程结束
            if hasattr(self, 'update_thread') and self.update_thread.is_alive():
                self.update_thread.join(timeout=2)
            
            self.root.destroy()
            logger.info("Application closed successfully")
        except Exception as e:
            logger.error(f"Error during closing: {e}")
            self.root.destroy()
    
    def run(self):
        """运行程序"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 确保窗口显示和获得焦点
        self.root.deiconify()
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after(1000, lambda: self.root.attributes('-topmost', False))  # 1秒后取消置顶
        self.root.focus_force()
        
        self.root.mainloop()

def main():
    """主函数"""
    try:
        app = OKXRealTimeAnalyzer()
        app.run()
    except Exception as e:
        logger.error(f"Application error: {e}")
        messagebox.showerror("严重错误", f"程序启动失败: {e}")

if __name__ == "__main__":
    main()
