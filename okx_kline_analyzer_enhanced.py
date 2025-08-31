import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import time
import threading
import platform

# 设置中文字体
try:
    if platform.system() == 'Windows':
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial']
    elif platform.system() == 'Darwin':
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'Arial']
    else:
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial']
    plt.rcParams['axes.unicode_minus'] = False
except:
    # 如果字体设置失败，使用英文标题
    pass

class TechnicalIndicators:
    """技术指标计算类"""
    
    @staticmethod
    def rsi(data, window=14):
        """相对强弱指数RSI"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def macd(data, fast=12, slow=26, signal=9):
        """平滑异同平均线指标MACD"""
        exp1 = data.ewm(span=fast).mean()
        exp2 = data.ewm(span=slow).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def kdj(high, low, close, k_window=9, d_window=3, j_window=3):
        """超买超卖随机指标KDJ"""
        lowest_low = low.rolling(window=k_window).min()
        highest_high = high.rolling(window=k_window).max()
        
        # RSV (Raw Stochastic Value)
        rsv = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        
        # K值 = 2/3 * 前一日K值 + 1/3 * 当日RSV
        k_values = []
        k = 50  # 初始K值
        for rsv_val in rsv:
            if pd.isna(rsv_val):
                k_values.append(np.nan)
            else:
                k = (2/3) * k + (1/3) * rsv_val
                k_values.append(k)
        
        k_series = pd.Series(k_values, index=rsv.index)
        
        # D值 = 2/3 * 前一日D值 + 1/3 * 当日K值
        d_values = []
        d = 50  # 初始D值
        for k_val in k_series:
            if pd.isna(k_val):
                d_values.append(np.nan)
            else:
                d = (2/3) * d + (1/3) * k_val
                d_values.append(d)
        
        d_series = pd.Series(d_values, index=k_series.index)
        
        # J值 = 3K - 2D
        j_series = 3 * k_series - 2 * d_series
        
        return k_series, d_series, j_series
    
    @staticmethod
    def williams_r(high, low, close, window=14):
        """威廉指标LWR (Williams %R)"""
        highest_high = high.rolling(window=window).max()
        lowest_low = low.rolling(window=window).min()
        wr = -100 * ((highest_high - close) / (highest_high - lowest_low))
        return wr
    
    @staticmethod
    def bbi(close, window1=3, window2=6, window3=12, window4=24):
        """多空指标BBI (Bull and Bear Index)"""
        ma1 = close.rolling(window=window1).mean()
        ma2 = close.rolling(window=window2).mean()
        ma3 = close.rolling(window=window3).mean()
        ma4 = close.rolling(window=window4).mean()
        bbi = (ma1 + ma2 + ma3 + ma4) / 4
        return bbi
    
    @staticmethod
    def zlmm(close, window=12):
        """动量指标ZLMM (Zero-Lag Momentum)"""
        # 计算动量
        momentum = close - close.shift(window)
        
        # 计算零滞后移动平均
        alpha = 2 / (window + 1)
        zlmm_values = []
        zlmm = 0
        
        for i, mom in enumerate(momentum):
            if pd.isna(mom):
                zlmm_values.append(np.nan)
            else:
                if i == 0:
                    zlmm = mom
                else:
                    zlmm = alpha * mom + (1 - alpha) * zlmm
                zlmm_values.append(zlmm)
        
        return pd.Series(zlmm_values, index=momentum.index)

class OKXKLineAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("OKX K-Line Technical Analysis Tool")
        self.root.geometry("1400x900")
        
        # API基础URL
        self.base_url = "https://www.okx.com/api/v5/market/history-candles"
        
        # 数据存储
        self.df = None
        
        self.create_widgets()
        
    def create_widgets(self):
        """创建GUI界面"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 控制面板
        control_frame = ttk.LabelFrame(main_frame, text="Control Panel | 控制面板", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 交易对选择
        ttk.Label(control_frame, text="Symbol | 交易对:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.symbol_var = tk.StringVar(value="BTC-USDT")
        self.symbol_entry = ttk.Entry(control_frame, textvariable=self.symbol_var, width=15)
        self.symbol_entry.grid(row=0, column=1, padx=(0, 20))
        
        # 时间周期选择
        ttk.Label(control_frame, text="Timeframe | 周期:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.timeframe_var = tk.StringVar(value="1H")
        timeframe_combo = ttk.Combobox(control_frame, textvariable=self.timeframe_var, width=10)
        timeframe_combo['values'] = ['1m', '3m', '5m', '15m', '30m', '1H', '2H', '4H', '6H', '12H', '1D']
        timeframe_combo.grid(row=0, column=3, padx=(0, 20))
        
        # 数据量选择
        ttk.Label(control_frame, text="Limit | 数据量:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        self.limit_var = tk.StringVar(value="300")
        limit_combo = ttk.Combobox(control_frame, textvariable=self.limit_var, width=8)
        limit_combo['values'] = ['100', '200', '300']
        limit_combo.grid(row=0, column=5, padx=(0, 20))
        
        # 获取数据按钮
        self.fetch_btn = ttk.Button(control_frame, text="Fetch Data | 获取数据", command=self.fetch_data_thread)
        self.fetch_btn.grid(row=0, column=6, padx=(0, 10))
        
        # 分析按钮
        self.analyze_btn = ttk.Button(control_frame, text="Analyze | 分析", command=self.analyze_data, state=tk.DISABLED)
        self.analyze_btn.grid(row=0, column=7)
        
        # 进度条
        self.progress = ttk.Progressbar(control_frame, mode='indeterminate')
        self.progress.grid(row=1, column=0, columnspan=8, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # 内容区域
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧图表区域
        chart_frame = ttk.LabelFrame(content_frame, text="Charts | K线图表", padding=5)
        chart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 创建图表
        self.create_chart(chart_frame)
        
        # 右侧分析结果区域
        analysis_frame = ttk.LabelFrame(content_frame, text="Analysis Report | 技术分析报告", padding=5)
        analysis_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        analysis_frame.configure(width=400)
        
        # 分析结果文本区域
        self.analysis_text = scrolledtext.ScrolledText(analysis_frame, width=50, height=30, wrap=tk.WORD)
        self.analysis_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置文本颜色标签
        self.analysis_text.tag_configure("bullish", foreground="green", font=("Arial", 10, "bold"))
        self.analysis_text.tag_configure("bearish", foreground="red", font=("Arial", 10, "bold"))
        self.analysis_text.tag_configure("neutral", foreground="orange", font=("Arial", 10, "bold"))
        self.analysis_text.tag_configure("header", foreground="blue", font=("Arial", 12, "bold"))
        
        # 状态栏
        self.status_var = tk.StringVar(value="Ready | 就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, pady=(10, 0))
        
    def create_chart(self, parent):
        """创建图表"""
        self.fig, (self.ax1, self.ax2, self.ax3, self.ax4) = plt.subplots(4, 1, figsize=(12, 10), 
                                                                gridspec_kw={'height_ratios': [3, 1, 1, 1]})
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 设置图表标题
        self.ax1.set_title("K-Line Chart & BBI")
        self.ax2.set_title("RSI & Williams %R")
        self.ax3.set_title("MACD")
        self.ax4.set_title("KDJ & ZLMM")
        
        plt.tight_layout()
        
    def fetch_data_thread(self):
        """在新线程中获取数据"""
        thread = threading.Thread(target=self.fetch_data)
        thread.daemon = True
        thread.start()
        
    def fetch_data(self):
        """从OKX API获取K线数据"""
        try:
            self.root.after(0, lambda: self.progress.start())
            self.root.after(0, lambda: self.fetch_btn.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.status_var.set("Fetching data... | 正在获取数据..."))
            
            symbol = self.symbol_var.get()
            timeframe = self.timeframe_var.get()
            limit = self.limit_var.get()
            
            # 构建请求参数
            params = {
                'instId': symbol,
                'bar': timeframe,
                'limit': limit
            }
            
            # 发送请求
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['code'] != '0':
                raise Exception(f"API Error: {data['msg']}")
            
            # 解析数据
            kline_data = data['data']
            if not kline_data:
                raise Exception("No data received")
            
            # 转换为DataFrame
            columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote', 'confirm']
            self.df = pd.DataFrame(kline_data, columns=columns)
            
            # 数据类型转换
            for col in ['open', 'high', 'low', 'close', 'volume']:
                self.df[col] = pd.to_numeric(self.df[col])
            
            self.df['timestamp'] = pd.to_numeric(self.df['timestamp'])
            self.df['datetime'] = pd.to_datetime(self.df['timestamp'], unit='ms')
            
            # 按时间排序（最新的在后面）
            self.df = self.df.sort_values('timestamp').reset_index(drop=True)
            
            self.root.after(0, lambda: self.progress.stop())
            self.root.after(0, lambda: self.fetch_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.analyze_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.status_var.set(f"Data fetched: {len(self.df)} records | 已获取 {len(self.df)} 条数据"))
            
            # 自动进行分析
            self.root.after(100, self.analyze_data)
            
        except Exception as e:
            self.root.after(0, lambda: self.progress.stop())
            self.root.after(0, lambda: self.fetch_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.status_var.set(f"Error: {str(e)} | 错误: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("Error | 错误", f"Failed to fetch data | 获取数据失败: {str(e)}"))
            
    def analyze_data(self):
        """进行技术分析"""
        if self.df is None or self.df.empty:
            messagebox.showwarning("Warning | 警告", "Please fetch data first | 请先获取数据")
            return
            
        try:
            self.status_var.set("Analyzing... | 正在分析...")
            
            # 计算技术指标
            indicators = self.calculate_indicators()
            
            # 绘制图表
            self.plot_charts(indicators)
            
            # 生成分析报告
            self.generate_analysis_report(indicators)
            
            self.status_var.set("Analysis completed | 分析完成")
            
        except Exception as e:
            messagebox.showerror("Error | 错误", f"Analysis failed | 分析失败: {str(e)}")
            self.status_var.set(f"Analysis error | 分析错误: {str(e)}")
            
    def calculate_indicators(self):
        """计算所有技术指标"""
        close = self.df['close']
        high = self.df['high']
        low = self.df['low']
        
        indicators = {}
        
        # RSI指标
        indicators['rsi'] = TechnicalIndicators.rsi(close)
        
        # MACD指标
        macd_line, signal_line, histogram = TechnicalIndicators.macd(close)
        indicators['macd'] = macd_line
        indicators['macd_signal'] = signal_line
        indicators['macd_histogram'] = histogram
        
        # KDJ指标
        k, d, j = TechnicalIndicators.kdj(high, low, close)
        indicators['kdj_k'] = k
        indicators['kdj_d'] = d
        indicators['kdj_j'] = j
        
        # 威廉指标LWR
        indicators['williams_r'] = TechnicalIndicators.williams_r(high, low, close)
        
        # 多空指标BBI
        indicators['bbi'] = TechnicalIndicators.bbi(close)
        
        # 动量指标ZLMM
        indicators['zlmm'] = TechnicalIndicators.zlmm(close)
        
        # 计算买卖信号
        indicators['buy_signals'], indicators['sell_signals'], indicators['hold_periods'] = self.detect_signals(indicators)
        
        return indicators
        
    def detect_signals(self, indicators):
        """检测买卖信号"""
        buy_signals = []
        sell_signals = []
        hold_periods = []
        
        for i in range(len(self.df)):
            if i < 50:  # 需要足够的数据来计算指标
                buy_signals.append(False)
                sell_signals.append(False)
                continue
                
            # 获取当前值
            rsi_current = indicators['rsi'].iloc[i] if not pd.isna(indicators['rsi'].iloc[i]) else 50
            macd_current = indicators['macd'].iloc[i] if not pd.isna(indicators['macd'].iloc[i]) else 0
            macd_signal_current = indicators['macd_signal'].iloc[i] if not pd.isna(indicators['macd_signal'].iloc[i]) else 0
            macd_hist_current = indicators['macd_histogram'].iloc[i] if not pd.isna(indicators['macd_histogram'].iloc[i]) else 0
            kdj_k_current = indicators['kdj_k'].iloc[i] if not pd.isna(indicators['kdj_k'].iloc[i]) else 50
            kdj_d_current = indicators['kdj_d'].iloc[i] if not pd.isna(indicators['kdj_d'].iloc[i]) else 50
            williams_current = indicators['williams_r'].iloc[i] if not pd.isna(indicators['williams_r'].iloc[i]) else -50
            current_price = self.df['close'].iloc[i]
            bbi_current = indicators['bbi'].iloc[i] if not pd.isna(indicators['bbi'].iloc[i]) else current_price
            zlmm_current = indicators['zlmm'].iloc[i] if not pd.isna(indicators['zlmm'].iloc[i]) else 0
            
            # 六个指标的买入信号检测
            signals = []
            
            # 1. MACD买入信号：金叉且在零轴上方或MACD线向上
            macd_buy = (macd_current > macd_signal_current and macd_hist_current > 0) or \
                      (macd_current > 0 and macd_hist_current > 0)
            signals.append(macd_buy)
            
            # 2. KDJ买入信号：K>D且K<80，或从超卖区域向上
            kdj_buy = (kdj_k_current > kdj_d_current and kdj_k_current < 80) or \
                     (kdj_k_current < 30 and kdj_k_current > kdj_d_current)
            signals.append(kdj_buy)
            
            # 3. RSI买入信号：RSI>50或从超卖向上
            rsi_buy = (rsi_current > 50) or (rsi_current < 35 and rsi_current > 30)
            signals.append(rsi_buy)
            
            # 4. 威廉指标买入信号：Williams %R > -50或从超卖向上
            williams_buy = (williams_current > -50) or (williams_current < -70 and williams_current > -80)
            signals.append(williams_buy)
            
            # 5. BBI买入信号：价格在BBI上方
            bbi_buy = current_price > bbi_current
            signals.append(bbi_buy)
            
            # 6. ZLMM买入信号：动量为正
            zlmm_buy = zlmm_current > 0
            signals.append(zlmm_buy)
            
            # 买入信号：六个指标都发出买入信号
            is_buy_signal = all(signals)
            buy_signals.append(is_buy_signal)
            
            # 卖出信号：多个指标发出卖出信号
            sell_conditions = []
            sell_conditions.append(rsi_current > 70)  # RSI超买
            sell_conditions.append(kdj_k_current > 80 and kdj_d_current > 80)  # KDJ超买
            sell_conditions.append(williams_current > -20)  # Williams超买
            sell_conditions.append(macd_current < macd_signal_current and macd_hist_current < 0)  # MACD死叉
            sell_conditions.append(current_price < bbi_current * 0.95)  # 价格显著低于BBI
            sell_conditions.append(zlmm_current < 0)  # 动量为负
            
            # 卖出信号：多个条件满足
            is_sell_signal = sum(sell_conditions) >= 4
            sell_signals.append(is_sell_signal)
        
        # 计算持有期间
        hold_periods = self.calculate_hold_periods(buy_signals, sell_signals)
        
        return buy_signals, sell_signals, hold_periods
    
    def calculate_hold_periods(self, buy_signals, sell_signals):
        """计算持有期间"""
        hold_periods = [False] * len(buy_signals)
        
        in_position = False
        buy_index = 0
        
        for i in range(len(buy_signals)):
            if buy_signals[i] and not in_position:
                # 买入信号
                in_position = True
                buy_index = i
                hold_periods[i] = True
            elif in_position:
                # 持有期间
                hold_periods[i] = True
                
                # 检查卖出条件：卖出信号或持有超过推荐天数
                days_held = i - buy_index
                if sell_signals[i] or days_held > 20:  # 假设推荐持有20个周期
                    in_position = False
        
        return hold_periods
        
    def plot_charts(self, indicators):
        """绘制图表"""
        # 清除之前的图表
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.ax4.clear()
        
        dates = self.df['datetime']
        
        # 主图 - K线和BBI
        self.ax1.plot(dates, self.df['close'], label='Close Price', color='black', linewidth=1.5)
        self.ax1.plot(dates, indicators['bbi'], label='BBI (Multi-Average)', color='blue', linewidth=2, alpha=0.8)
        
        # 添加持有期间的洋红色背景
        hold_periods = indicators['hold_periods']
        for i in range(len(hold_periods)):
            if hold_periods[i]:
                self.ax1.axvspan(dates.iloc[i], dates.iloc[min(i+1, len(dates)-1)], 
                               alpha=0.2, color='magenta', label='Hold Period' if i == 0 or not hold_periods[i-1] else "")
        
        # 添加买入信号 - 红色向上箭头和黄色柱子
        buy_signals = indicators['buy_signals']
        sell_signals = indicators['sell_signals']
        
        for i in range(len(buy_signals)):
            if buy_signals[i]:
                # 红色向上箭头
                self.ax1.annotate('↑', xy=(dates.iloc[i], self.df['close'].iloc[i]), 
                                xytext=(dates.iloc[i], self.df['close'].iloc[i] * 0.98),
                                fontsize=20, color='red', weight='bold',
                                ha='center', va='top')
                
                # 黄色买入信号柱子
                self.ax1.axvline(x=dates.iloc[i], color='yellow', alpha=0.7, linewidth=3,
                               label='Buy Signal' if i == 0 or not any(buy_signals[:i]) else "")
        
        # 添加卖出信号 - 绿色向下箭头
        for i in range(len(sell_signals)):
            if sell_signals[i]:
                # 绿色向下箭头
                self.ax1.annotate('↓', xy=(dates.iloc[i], self.df['close'].iloc[i]), 
                                xytext=(dates.iloc[i], self.df['close'].iloc[i] * 1.02),
                                fontsize=20, color='green', weight='bold',
                                ha='center', va='bottom')
        
        self.ax1.set_title(f"{self.symbol_var.get()} K-Line Chart & BBI with Trading Signals")
        self.ax1.legend()
        self.ax1.grid(True, alpha=0.3)
        
        # 第二图 - RSI和威廉指标
        ax2_twin = self.ax2.twinx()
        
        self.ax2.plot(dates, indicators['rsi'], label='RSI', color='purple', linewidth=1.5)
        self.ax2.axhline(y=70, color='red', linestyle='--', alpha=0.7, label='RSI Overbought(70)')
        self.ax2.axhline(y=30, color='green', linestyle='--', alpha=0.7, label='RSI Oversold(30)')
        self.ax2.axhline(y=50, color='gray', linestyle='-', alpha=0.5)
        self.ax2.set_ylim(0, 100)
        self.ax2.set_ylabel('RSI', color='purple')
        
        ax2_twin.plot(dates, indicators['williams_r'], label='Williams %R', color='orange', linewidth=1.5)
        ax2_twin.axhline(y=-20, color='red', linestyle='--', alpha=0.7, label='WR Overbought(-20)')
        ax2_twin.axhline(y=-80, color='green', linestyle='--', alpha=0.7, label='WR Oversold(-80)')
        ax2_twin.set_ylim(-100, 0)
        ax2_twin.set_ylabel('Williams %R', color='orange')
        
        # 在RSI图上也标记买卖信号
        for i in range(len(buy_signals)):
            if buy_signals[i]:
                self.ax2.plot(dates.iloc[i], indicators['rsi'].iloc[i], 'r^', markersize=10, label='Buy' if i == 0 else "")
            if sell_signals[i]:
                self.ax2.plot(dates.iloc[i], indicators['rsi'].iloc[i], 'gv', markersize=10, label='Sell' if i == 0 else "")
        
        self.ax2.set_title("RSI & Williams %R Indicators")
        self.ax2.legend(loc='upper left')
        ax2_twin.legend(loc='upper right')
        self.ax2.grid(True, alpha=0.3)
        
        # 第三图 - MACD
        self.ax3.plot(dates, indicators['macd'], label='MACD', color='blue', linewidth=1.5)
        self.ax3.plot(dates, indicators['macd_signal'], label='Signal', color='red', linewidth=1.5)
        
        # MACD柱状图 - 买入信号时用黄色标记
        colors = []
        for i in range(len(indicators['macd_histogram'])):
            if buy_signals[i]:
                colors.append('yellow')  # 买入信号时的黄色柱子
            elif indicators['macd_histogram'].iloc[i] >= 0:
                colors.append('green')
            else:
                colors.append('red')
        
        self.ax3.bar(dates, indicators['macd_histogram'], label='Histogram', alpha=0.7, color=colors)
        
        self.ax3.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        self.ax3.set_title("MACD Indicator with Buy/Sell Signals")
        self.ax3.legend()
        self.ax3.grid(True, alpha=0.3)
        
        # 第四图 - KDJ和ZLMM
        ax4_twin = self.ax4.twinx()
        
        # KDJ指标
        self.ax4.plot(dates, indicators['kdj_k'], label='K', color='blue', linewidth=1.5)
        self.ax4.plot(dates, indicators['kdj_d'], label='D', color='red', linewidth=1.5)
        self.ax4.plot(dates, indicators['kdj_j'], label='J', color='green', linewidth=1.5)
        self.ax4.axhline(y=80, color='red', linestyle='--', alpha=0.7, label='Overbought(80)')
        self.ax4.axhline(y=20, color='green', linestyle='--', alpha=0.7, label='Oversold(20)')
        self.ax4.set_ylim(0, 100)
        self.ax4.set_ylabel('KDJ', color='blue')
        
        # ZLMM指标
        ax4_twin.plot(dates, indicators['zlmm'], label='ZLMM', color='purple', linewidth=2, alpha=0.8)
        ax4_twin.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        ax4_twin.set_ylabel('ZLMM', color='purple')
        
        # 在KDJ图上标记信号
        for i in range(len(buy_signals)):
            if buy_signals[i]:
                self.ax4.plot(dates.iloc[i], indicators['kdj_k'].iloc[i], 'r^', markersize=8)
            if sell_signals[i]:
                self.ax4.plot(dates.iloc[i], indicators['kdj_k'].iloc[i], 'gv', markersize=8)
        
        self.ax4.set_title("KDJ & ZLMM Indicators")
        self.ax4.legend(loc='upper left')
        ax4_twin.legend(loc='upper right')
        self.ax4.grid(True, alpha=0.3)
        
        # 格式化x轴日期
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=max(1, len(self.df)//10)))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        self.canvas.draw()
        
    def generate_analysis_report(self, indicators):
        """生成分析报告"""
        self.analysis_text.delete(1.0, tk.END)
        
        # 获取最新数据
        latest = self.df.iloc[-1]
        current_price = latest['close']
        
        # 报告标题
        self.insert_text("=== TECHNICAL ANALYSIS REPORT ===\n", "header")
        self.insert_text("=== 技术分析报告 ===\n\n", "header")
        self.insert_text(f"Symbol | 交易对: {self.symbol_var.get()}\n", "header")
        self.insert_text(f"Current Price | 当前价格: ${current_price:.4f}\n", "header")
        self.insert_text(f"Analysis Time | 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n", "header")
        
        # 分析各项指标
        bullish_signals = 0
        bearish_signals = 0
        
        # MACD分析
        self.insert_text("1. MACD Analysis | 平滑异同平均线分析\n", "header")
        macd_current = indicators['macd'].iloc[-1]
        signal_current = indicators['macd_signal'].iloc[-1]
        histogram_current = indicators['macd_histogram'].iloc[-1]
        
        if macd_current > signal_current and histogram_current > 0:
            self.insert_text("• MACD golden cross above zero, strong BULLISH | MACD金叉且在零轴上方，强烈看涨\n", "bullish")
            bullish_signals += 2
        elif macd_current > signal_current:
            self.insert_text("• MACD golden cross, BULLISH | MACD金叉，看涨\n", "bullish")
            bullish_signals += 1
        elif macd_current < signal_current and histogram_current < 0:
            self.insert_text("• MACD death cross below zero, strong BEARISH | MACD死叉且在零轴下方，强烈看跌\n", "bearish")
            bearish_signals += 2
        elif macd_current < signal_current:
            self.insert_text("• MACD death cross, BEARISH | MACD死叉，看跌\n", "bearish")
            bearish_signals += 1
        else:
            self.insert_text("• MACD signal unclear | MACD信号不明确\n", "neutral")
        
        # KDJ分析
        self.insert_text("\n2. KDJ Analysis | 超买超卖随机指标分析\n", "header")
        k_current = indicators['kdj_k'].iloc[-1]
        d_current = indicators['kdj_d'].iloc[-1]
        j_current = indicators['kdj_j'].iloc[-1]
        
        if k_current > 80 and d_current > 80:
            self.insert_text(f"• KDJ all above 80 (K:{k_current:.1f}, D:{d_current:.1f}), overbought BEARISH | KDJ均在80上方，超买看跌\n", "bearish")
            bearish_signals += 1
        elif k_current < 20 and d_current < 20:
            self.insert_text(f"• KDJ all below 20 (K:{k_current:.1f}, D:{d_current:.1f}), oversold BULLISH | KDJ均在20下方，超卖看涨\n", "bullish")
            bullish_signals += 1
        elif k_current > d_current:
            self.insert_text(f"• K line above D line (K:{k_current:.1f}, D:{d_current:.1f}), BULLISH | K线在D线上方，看涨\n", "bullish")
            bullish_signals += 1
        else:
            self.insert_text(f"• K line below D line (K:{k_current:.1f}, D:{d_current:.1f}), BEARISH | K线在D线下方，看跌\n", "bearish")
            bearish_signals += 1
        
        # RSI分析
        self.insert_text("\n3. RSI Analysis | 相对强弱指数分析\n", "header")
        rsi_current = indicators['rsi'].iloc[-1]
        
        if rsi_current > 70:
            self.insert_text(f"• RSI = {rsi_current:.2f} > 70, overbought BEARISH | 超买看跌\n", "bearish")
            bearish_signals += 1
        elif rsi_current < 30:
            self.insert_text(f"• RSI = {rsi_current:.2f} < 30, oversold BULLISH | 超卖看涨\n", "bullish")
            bullish_signals += 1
        elif 40 <= rsi_current <= 60:
            self.insert_text(f"• RSI = {rsi_current:.2f}, neutral zone | 中性区域\n", "neutral")
        elif rsi_current > 50:
            self.insert_text(f"• RSI = {rsi_current:.2f} > 50, mild BULLISH | 轻微看涨\n", "bullish")
        else:
            self.insert_text(f"• RSI = {rsi_current:.2f} < 50, mild BEARISH | 轻微看跌\n", "bearish")
        
        # 威廉指标分析
        self.insert_text("\n4. Williams %R Analysis | 威廉指标分析\n", "header")
        wr_current = indicators['williams_r'].iloc[-1]
        
        if wr_current > -20:
            self.insert_text(f"• Williams %R = {wr_current:.2f} > -20, overbought BEARISH | 超买看跌\n", "bearish")
            bearish_signals += 1
        elif wr_current < -80:
            self.insert_text(f"• Williams %R = {wr_current:.2f} < -80, oversold BULLISH | 超卖看涨\n", "bullish")
            bullish_signals += 1
        elif -60 <= wr_current <= -40:
            self.insert_text(f"• Williams %R = {wr_current:.2f}, neutral zone | 中性区域\n", "neutral")
        elif wr_current > -50:
            self.insert_text(f"• Williams %R = {wr_current:.2f}, mild BEARISH | 轻微看跌\n", "bearish")
        else:
            self.insert_text(f"• Williams %R = {wr_current:.2f}, mild BULLISH | 轻微看涨\n", "bullish")
        
        # BBI分析
        self.insert_text("\n5. BBI Analysis | 多空指标分析\n", "header")
        bbi_current = indicators['bbi'].iloc[-1]
        
        if current_price > bbi_current:
            price_bbi_ratio = (current_price - bbi_current) / bbi_current * 100
            if price_bbi_ratio > 5:
                self.insert_text(f"• Price significantly above BBI (+{price_bbi_ratio:.1f}%), strong BULLISH | 价格显著高于BBI，强烈看涨\n", "bullish")
                bullish_signals += 2
            else:
                self.insert_text(f"• Price above BBI (+{price_bbi_ratio:.1f}%), BULLISH | 价格高于BBI，看涨\n", "bullish")
                bullish_signals += 1
        else:
            price_bbi_ratio = (bbi_current - current_price) / bbi_current * 100
            if price_bbi_ratio > 5:
                self.insert_text(f"• Price significantly below BBI (-{price_bbi_ratio:.1f}%), strong BEARISH | 价格显著低于BBI，强烈看跌\n", "bearish")
                bearish_signals += 2
            else:
                self.insert_text(f"• Price below BBI (-{price_bbi_ratio:.1f}%), BEARISH | 价格低于BBI，看跌\n", "bearish")
                bearish_signals += 1
        
        # ZLMM动量分析
        self.insert_text("\n6. ZLMM Analysis | 动量指标分析\n", "header")
        zlmm_current = indicators['zlmm'].iloc[-1]
        zlmm_prev = indicators['zlmm'].iloc[-2] if len(indicators['zlmm']) > 1 else zlmm_current
        
        if zlmm_current > 0:
            if zlmm_current > zlmm_prev:
                self.insert_text(f"• ZLMM = {zlmm_current:.4f} > 0 and increasing, strong BULLISH | 动量为正且递增，强烈看涨\n", "bullish")
                bullish_signals += 2
            else:
                self.insert_text(f"• ZLMM = {zlmm_current:.4f} > 0 but decreasing, mild BULLISH | 动量为正但递减，轻微看涨\n", "bullish")
                bullish_signals += 1
        elif zlmm_current < 0:
            if zlmm_current < zlmm_prev:
                self.insert_text(f"• ZLMM = {zlmm_current:.4f} < 0 and decreasing, strong BEARISH | 动量为负且递减，强烈看跌\n", "bearish")
                bearish_signals += 2
            else:
                self.insert_text(f"• ZLMM = {zlmm_current:.4f} < 0 but increasing, mild BEARISH | 动量为负但递增，轻微看跌\n", "bearish")
                bearish_signals += 1
        else:
            self.insert_text(f"• ZLMM = {zlmm_current:.4f} ≈ 0, neutral momentum | 动量接近零，中性\n", "neutral")
        
        # 综合分析结论
        self.insert_text("\n" + "="*50 + "\n", "header")
        self.insert_text("7. TRADING SIGNALS ANALYSIS | 交易信号分析\n", "header")
        self.insert_text("="*50 + "\n\n", "header")
        
        # 统计买卖信号
        buy_signals = indicators['buy_signals']
        sell_signals = indicators['sell_signals']
        hold_periods = indicators['hold_periods']
        
        total_buy_signals = sum(buy_signals)
        total_sell_signals = sum(sell_signals)
        current_holding = hold_periods[-1] if hold_periods else False
        
        self.insert_text(f"Total Buy Signals | 买入信号总数: {total_buy_signals}\n", "bullish")
        self.insert_text(f"Total Sell Signals | 卖出信号总数: {total_sell_signals}\n", "bearish")
        self.insert_text(f"Current Status | 当前状态: {'Holding Position | 持仓中' if current_holding else 'No Position | 空仓'}\n", "neutral")
        
        # 最近的信号
        recent_buy = False
        recent_sell = False
        last_signal_index = -1
        
        for i in range(len(buy_signals)-1, max(len(buy_signals)-10, 0), -1):
            if buy_signals[i]:
                recent_buy = True
                last_signal_index = i
                break
            elif sell_signals[i]:
                recent_sell = True
                last_signal_index = i
                break
        
        if recent_buy:
            signal_time = self.df['datetime'].iloc[last_signal_index].strftime('%m-%d %H:%M')
            self.insert_text(f"\n🔴 Recent Buy Signal | 最近买入信号: {signal_time}\n", "bullish")
            self.insert_text("⚠️ Six indicators confirmed buy signal | 六个指标确认买入信号\n", "bullish")
        elif recent_sell:
            signal_time = self.df['datetime'].iloc[last_signal_index].strftime('%m-%d %H:%M')
            self.insert_text(f"\n🔻 Recent Sell Signal | 最近卖出信号: {signal_time}\n", "bearish")
            self.insert_text("⚠️ Multiple indicators suggest selling | 多个指标建议卖出\n", "bearish")
        else:
            self.insert_text(f"\n📊 No Recent Signals | 最近无明确信号\n", "neutral")
        
        self.insert_text("\n" + "="*50 + "\n", "header")
        self.insert_text("8. INVESTMENT RECOMMENDATION | 综合投资建议\n", "header")
        self.insert_text("="*50 + "\n\n", "header")
        
        total_signals = bullish_signals + bearish_signals
        if total_signals == 0:
            sentiment = "NEUTRAL | 中性"
            color = "neutral"
        else:
            bullish_ratio = bullish_signals / total_signals
            if bullish_ratio >= 0.75:
                sentiment = "STRONG BULLISH | 强烈看涨"
                color = "bullish"
            elif bullish_ratio >= 0.6:
                sentiment = "BULLISH | 看涨"
                color = "bullish"
            elif bullish_ratio >= 0.4:
                sentiment = "NEUTRAL BULLISH | 中性偏涨"
                color = "neutral"
            elif bullish_ratio >= 0.25:
                sentiment = "NEUTRAL BEARISH | 中性偏跌"
                color = "neutral"
            else:
                sentiment = "BEARISH | 看跌"
                color = "bearish"
        
        self.insert_text(f"Bullish Signals | 看涨信号: {bullish_signals}\n", "bullish")
        self.insert_text(f"Bearish Signals | 看跌信号: {bearish_signals}\n", "bearish")
        self.insert_text(f"Bullish Ratio | 看涨比例: {bullish_ratio*100:.1f}%\n", "neutral")
        self.insert_text(f"\nOverall Sentiment | 综合判断: {sentiment}\n\n", color)
        
        # 投资建议
        if "STRONG BULLISH" in sentiment:
            self.insert_text("💡 RECOMMENDATION | 建议: Strong BUY signal, consider position building | 强烈买入信号，可考虑建仓\n", "bullish")
            self.insert_text("⚠️ Risk Control | 风险控制: Set stop-loss at -5% | 设置5%止损\n", "neutral")
        elif "BULLISH" in sentiment:
            self.insert_text("💡 RECOMMENDATION | 建议: BUY signal, enter with caution | 买入信号，谨慎进场\n", "bullish")
            self.insert_text("⚠️ Risk Control | 风险控制: Set stop-loss at -3% | 设置3%止损\n", "neutral")
        elif "NEUTRAL BULLISH" in sentiment:
            self.insert_text("💡 RECOMMENDATION | 建议: Light position or wait for better entry | 轻仓或等待更好入场点\n", "neutral")
        elif "NEUTRAL BEARISH" in sentiment:
            self.insert_text("💡 RECOMMENDATION | 建议: Wait and see, avoid new positions | 观望为主，避免新开仓\n", "neutral")
        else:
            self.insert_text("💡 RECOMMENDATION | 建议: SELL signal, consider position reduction | 卖出信号，考虑减仓\n", "bearish")
            self.insert_text("⚠️ Risk Control | 风险控制: Strict stop-loss | 严格止损\n", "neutral")
        
        self.insert_text("\n📊 Technical Summary | 技术面总结:\n", "header")
        self.insert_text(f"• Trend Strength | 趋势强度: {abs(bullish_signals - bearish_signals)}/10\n", "neutral")
        self.insert_text(f"• Signal Clarity | 信号明确度: {total_signals}/10\n", "neutral")
        
        # 图例和信号说明
        self.insert_text("\n📈 CHART SIGNALS GUIDE | 图表信号说明:\n", "header")
        self.insert_text("🔴 Red Arrow Up (↑) | 红色向上箭头: Strong Buy Signal (6 indicators confirm)\n", "bullish")
        self.insert_text("   六个指标同时确认的强烈买入信号\n", "bullish")
        self.insert_text("🟡 Yellow Column | 黄色柱子: Buy Signal Confirmation\n", "bullish")
        self.insert_text("   买入信号确认标记\n", "bullish")
        self.insert_text("🔻 Green Arrow Down (↓) | 绿色向下箭头: Sell Signal\n", "bearish")
        self.insert_text("   卖出信号提示\n", "bearish")
        self.insert_text("🟣 Magenta Background | 洋红色背景: Recommended Holding Period\n", "neutral")
        self.insert_text("   推荐持有期间（约20个周期）\n", "neutral")
        
        self.insert_text("\n⚠️  RISK WARNING | 风险提示: \n", "header")
        self.insert_text("Technical analysis is for reference only. Past performance does not guarantee future results.\n", "header")
        self.insert_text("技术分析仅供参考，过往表现不代表未来收益。投资有风险，入市需谨慎！", "header")
        
    def insert_text(self, text, tag=None):
        """插入带标签的文本"""
        if tag:
            start_pos = self.analysis_text.index(tk.INSERT)
            self.analysis_text.insert(tk.INSERT, text)
            end_pos = self.analysis_text.index(tk.INSERT)
            self.analysis_text.tag_add(tag, start_pos, end_pos)
        else:
            self.analysis_text.insert(tk.INSERT, text)

def main():
    root = tk.Tk()
    app = OKXKLineAnalyzer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
