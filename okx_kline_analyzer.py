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
if platform.system() == 'Windows':
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']  # 设置中文字体
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
elif platform.system() == 'Darwin':  # macOS
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
else:  # Linux
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class TechnicalIndicators:
    """技术指标计算类"""
    
    @staticmethod
    def moving_average(data, window):
        """移动平均线"""
        return data.rolling(window=window).mean()
    
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
        """MACD指标"""
        exp1 = data.ewm(span=fast).mean()
        exp2 = data.ewm(span=slow).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def bollinger_bands(data, window=20, num_std=2):
        """布林通道"""
        sma = data.rolling(window=window).mean()
        std = data.rolling(window=window).std()
        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)
        return upper_band, sma, lower_band
    
    @staticmethod
    def stochastic_oscillator(high, low, close, k_window=14, d_window=3):
        """KD指标"""
        lowest_low = low.rolling(window=k_window).min()
        highest_high = high.rolling(window=k_window).max()
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_window).mean()
        return k_percent, d_percent
    
    @staticmethod
    def bias_ratio(close, ma):
        """乖离率"""
        return ((close - ma) / ma) * 100

class OKXKLineAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("OKX K线技术分析工具")
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
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 交易对选择
        ttk.Label(control_frame, text="交易对:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.symbol_var = tk.StringVar(value="BTC-USDT")
        self.symbol_entry = ttk.Entry(control_frame, textvariable=self.symbol_var, width=15)
        self.symbol_entry.grid(row=0, column=1, padx=(0, 20))
        
        # 时间周期选择
        ttk.Label(control_frame, text="时间周期:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.timeframe_var = tk.StringVar(value="1H")
        timeframe_combo = ttk.Combobox(control_frame, textvariable=self.timeframe_var, width=10)
        timeframe_combo['values'] = ['1m', '3m', '5m', '15m', '30m', '1H', '2H', '4H', '6H', '12H', '1D']
        timeframe_combo.grid(row=0, column=3, padx=(0, 20))
        
        # 数据量选择
        ttk.Label(control_frame, text="数据量:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        self.limit_var = tk.StringVar(value="300")
        limit_combo = ttk.Combobox(control_frame, textvariable=self.limit_var, width=8)
        limit_combo['values'] = ['100', '200', '300']
        limit_combo.grid(row=0, column=5, padx=(0, 20))
        
        # 获取数据按钮
        self.fetch_btn = ttk.Button(control_frame, text="获取数据", command=self.fetch_data_thread)
        self.fetch_btn.grid(row=0, column=6, padx=(0, 10))
        
        # 分析按钮
        self.analyze_btn = ttk.Button(control_frame, text="技术分析", command=self.analyze_data, state=tk.DISABLED)
        self.analyze_btn.grid(row=0, column=7)
        
        # 进度条
        self.progress = ttk.Progressbar(control_frame, mode='indeterminate')
        self.progress.grid(row=1, column=0, columnspan=8, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # 内容区域
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧图表区域
        chart_frame = ttk.LabelFrame(content_frame, text="K线图表", padding=5)
        chart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 创建图表
        self.create_chart(chart_frame)
        
        # 右侧分析结果区域
        analysis_frame = ttk.LabelFrame(content_frame, text="技术分析结果", padding=5)
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
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, pady=(10, 0))
        
    def create_chart(self, parent):
        """创建图表"""
        self.fig, (self.ax1, self.ax2, self.ax3) = plt.subplots(3, 1, figsize=(12, 8), 
                                                                gridspec_kw={'height_ratios': [3, 1, 1]})
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 设置图表标题
        self.ax1.set_title("K线图与技术指标")
        self.ax2.set_title("RSI")
        self.ax3.set_title("MACD")
        
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
            self.root.after(0, lambda: self.status_var.set("正在获取数据..."))
            
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
                raise Exception(f"API错误: {data['msg']}")
            
            # 解析数据
            kline_data = data['data']
            if not kline_data:
                raise Exception("没有获取到数据")
            
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
            self.root.after(0, lambda: self.status_var.set(f"成功获取 {len(self.df)} 条数据"))
            
            # 自动进行分析
            self.root.after(100, self.analyze_data)
            
        except Exception as e:
            self.root.after(0, lambda: self.progress.stop())
            self.root.after(0, lambda: self.fetch_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.status_var.set(f"错误: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("错误", f"获取数据失败: {str(e)}"))
            
    def analyze_data(self):
        """进行技术分析"""
        if self.df is None or self.df.empty:
            messagebox.showwarning("警告", "请先获取数据")
            return
            
        try:
            self.status_var.set("正在进行技术分析...")
            
            # 计算技术指标
            indicators = self.calculate_indicators()
            
            # 绘制图表
            self.plot_charts(indicators)
            
            # 生成分析报告
            self.generate_analysis_report(indicators)
            
            self.status_var.set("技术分析完成")
            
        except Exception as e:
            messagebox.showerror("错误", f"分析失败: {str(e)}")
            self.status_var.set(f"分析错误: {str(e)}")
            
    def calculate_indicators(self):
        """计算所有技术指标"""
        close = self.df['close']
        high = self.df['high']
        low = self.df['low']
        
        indicators = {}
        
        # 移动平均线
        indicators['ma5'] = TechnicalIndicators.moving_average(close, 5)
        indicators['ma10'] = TechnicalIndicators.moving_average(close, 10)
        indicators['ma20'] = TechnicalIndicators.moving_average(close, 20)
        indicators['ma50'] = TechnicalIndicators.moving_average(close, 50)
        
        # RSI
        indicators['rsi'] = TechnicalIndicators.rsi(close)
        
        # MACD
        macd_line, signal_line, histogram = TechnicalIndicators.macd(close)
        indicators['macd'] = macd_line
        indicators['macd_signal'] = signal_line
        indicators['macd_histogram'] = histogram
        
        # 布林通道
        bb_upper, bb_middle, bb_lower = TechnicalIndicators.bollinger_bands(close)
        indicators['bb_upper'] = bb_upper
        indicators['bb_middle'] = bb_middle
        indicators['bb_lower'] = bb_lower
        
        # KD指标
        k_percent, d_percent = TechnicalIndicators.stochastic_oscillator(high, low, close)
        indicators['k'] = k_percent
        indicators['d'] = d_percent
        
        # 乖离率
        indicators['bias_ma20'] = TechnicalIndicators.bias_ratio(close, indicators['ma20'])
        
        return indicators
        
    def plot_charts(self, indicators):
        """绘制图表"""
        # 清除之前的图表
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        
        dates = self.df['datetime']
        
        # 主图 - K线和移动平均线
        self.ax1.plot(dates, self.df['close'], label='收盘价', color='black', linewidth=1)
        self.ax1.plot(dates, indicators['ma5'], label='MA5', color='red', alpha=0.7)
        self.ax1.plot(dates, indicators['ma10'], label='MA10', color='orange', alpha=0.7)
        self.ax1.plot(dates, indicators['ma20'], label='MA20', color='blue', alpha=0.7)
        self.ax1.plot(dates, indicators['ma50'], label='MA50', color='purple', alpha=0.7)
        
        # 布林通道
        self.ax1.plot(dates, indicators['bb_upper'], label='BB上轨', color='gray', alpha=0.5, linestyle='--')
        self.ax1.plot(dates, indicators['bb_middle'], label='BB中轨', color='gray', alpha=0.5)
        self.ax1.plot(dates, indicators['bb_lower'], label='BB下轨', color='gray', alpha=0.5, linestyle='--')
        self.ax1.fill_between(dates, indicators['bb_upper'], indicators['bb_lower'], alpha=0.1, color='gray')
        
        self.ax1.set_title(f"{self.symbol_var.get()} K线图与技术指标")
        self.ax1.legend()
        self.ax1.grid(True, alpha=0.3)
        
        # RSI图
        self.ax2.plot(dates, indicators['rsi'], label='RSI', color='purple')
        self.ax2.axhline(y=70, color='red', linestyle='--', alpha=0.7, label='超买线(70)')
        self.ax2.axhline(y=30, color='green', linestyle='--', alpha=0.7, label='超卖线(30)')
        self.ax2.axhline(y=50, color='gray', linestyle='-', alpha=0.5)
        self.ax2.set_ylim(0, 100)
        self.ax2.set_title("RSI指标")
        self.ax2.legend()
        self.ax2.grid(True, alpha=0.3)
        
        # MACD图
        self.ax3.plot(dates, indicators['macd'], label='MACD', color='blue')
        self.ax3.plot(dates, indicators['macd_signal'], label='信号线', color='red')
        self.ax3.bar(dates, indicators['macd_histogram'], label='MACD柱', alpha=0.3, color='green')
        self.ax3.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        self.ax3.set_title("MACD指标")
        self.ax3.legend()
        self.ax3.grid(True, alpha=0.3)
        
        # 格式化x轴日期
        for ax in [self.ax1, self.ax2, self.ax3]:
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
        self.insert_text("=== 技术分析报告 ===\n\n", "header")
        self.insert_text(f"交易对: {self.symbol_var.get()}\n", "header")
        self.insert_text(f"当前价格: ${current_price:.4f}\n", "header")
        self.insert_text(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n", "header")
        
        # 分析各项指标
        bullish_signals = 0
        bearish_signals = 0
        
        # 移动平均线分析
        self.insert_text("1. 移动平均线分析\n", "header")
        
        ma5_current = indicators['ma5'].iloc[-1]
        ma10_current = indicators['ma10'].iloc[-1]
        ma20_current = indicators['ma20'].iloc[-1]
        ma50_current = indicators['ma50'].iloc[-1]
        
        if current_price > ma5_current > ma10_current > ma20_current:
            self.insert_text("• 多头排列，强烈看涨信号\n", "bullish")
            bullish_signals += 2
        elif current_price > ma20_current:
            self.insert_text("• 价格在MA20上方，看涨信号\n", "bullish")
            bullish_signals += 1
        elif current_price < ma20_current:
            self.insert_text("• 价格在MA20下方，看跌信号\n", "bearish")
            bearish_signals += 1
        
        # RSI分析
        self.insert_text("\n2. RSI指标分析\n", "header")
        rsi_current = indicators['rsi'].iloc[-1]
        
        if rsi_current > 70:
            self.insert_text(f"• RSI = {rsi_current:.2f} > 70，超买状态，看跌信号\n", "bearish")
            bearish_signals += 1
        elif rsi_current < 30:
            self.insert_text(f"• RSI = {rsi_current:.2f} < 30，超卖状态，看涨信号\n", "bullish")
            bullish_signals += 1
        elif 40 <= rsi_current <= 60:
            self.insert_text(f"• RSI = {rsi_current:.2f}，处于中性区域\n", "neutral")
        else:
            self.insert_text(f"• RSI = {rsi_current:.2f}，正常范围\n", "neutral")
        
        # MACD分析
        self.insert_text("\n3. MACD指标分析\n", "header")
        macd_current = indicators['macd'].iloc[-1]
        signal_current = indicators['macd_signal'].iloc[-1]
        histogram_current = indicators['macd_histogram'].iloc[-1]
        
        if macd_current > signal_current and histogram_current > 0:
            self.insert_text("• MACD金叉且柱状图为正，看涨信号\n", "bullish")
            bullish_signals += 1
        elif macd_current < signal_current and histogram_current < 0:
            self.insert_text("• MACD死叉且柱状图为负，看跌信号\n", "bearish")
            bearish_signals += 1
        else:
            self.insert_text("• MACD信号不明确\n", "neutral")
        
        # KD指标分析
        self.insert_text("\n4. KD指标分析\n", "header")
        k_current = indicators['k'].iloc[-1]
        d_current = indicators['d'].iloc[-1]
        
        if k_current > d_current and k_current < 80:
            self.insert_text(f"• K线({k_current:.2f}) > D线({d_current:.2f})，看涨信号\n", "bullish")
            bullish_signals += 1
        elif k_current < d_current and k_current > 20:
            self.insert_text(f"• K线({k_current:.2f}) < D线({d_current:.2f})，看跌信号\n", "bearish")
            bearish_signals += 1
        else:
            self.insert_text(f"• KD指标处于极值区域，注意反转\n", "neutral")
        
        # 布林通道分析
        self.insert_text("\n5. 布林通道分析\n", "header")
        bb_upper_current = indicators['bb_upper'].iloc[-1]
        bb_lower_current = indicators['bb_lower'].iloc[-1]
        bb_middle_current = indicators['bb_middle'].iloc[-1]
        
        if current_price > bb_upper_current:
            self.insert_text("• 价格突破布林上轨，强势看涨但注意回调\n", "bullish")
            bullish_signals += 1
        elif current_price < bb_lower_current:
            self.insert_text("• 价格跌破布林下轨，超卖但可能反弹\n", "bullish")
            bullish_signals += 1
        elif current_price > bb_middle_current:
            self.insert_text("• 价格在布林中轨上方，轻微看涨\n", "bullish")
        else:
            self.insert_text("• 价格在布林中轨下方，轻微看跌\n", "bearish")
        
        # 乖离率分析
        self.insert_text("\n6. 乖离率分析\n", "header")
        bias_current = indicators['bias_ma20'].iloc[-1]
        
        if bias_current > 10:
            self.insert_text(f"• 乖离率 = {bias_current:.2f}% > 10%，严重偏离，看跌信号\n", "bearish")
            bearish_signals += 1
        elif bias_current < -10:
            self.insert_text(f"• 乖离率 = {bias_current:.2f}% < -10%，严重偏离，看涨信号\n", "bullish")
            bullish_signals += 1
        else:
            self.insert_text(f"• 乖离率 = {bias_current:.2f}%，正常范围\n", "neutral")
        
        # 综合分析结论
        self.insert_text("\n" + "="*50 + "\n", "header")
        self.insert_text("7. 综合投资建议\n", "header")
        self.insert_text("="*50 + "\n\n", "header")
        
        total_signals = bullish_signals + bearish_signals
        if total_signals == 0:
            sentiment = "中性"
            color = "neutral"
        else:
            bullish_ratio = bullish_signals / total_signals
            if bullish_ratio >= 0.7:
                sentiment = "强烈看涨"
                color = "bullish"
            elif bullish_ratio >= 0.6:
                sentiment = "看涨"
                color = "bullish"
            elif bullish_ratio >= 0.4:
                sentiment = "中性偏涨"
                color = "neutral"
            elif bullish_ratio >= 0.3:
                sentiment = "中性偏跌"
                color = "neutral"
            else:
                sentiment = "看跌"
                color = "bearish"
        
        self.insert_text(f"看涨信号数: {bullish_signals}\n", "bullish")
        self.insert_text(f"看跌信号数: {bearish_signals}\n", "bearish")
        self.insert_text(f"\n综合判断: {sentiment}\n\n", color)
        
        # 投资建议
        if sentiment == "强烈看涨":
            self.insert_text("投资建议: 适合买入，但注意风险控制\n", "bullish")
        elif sentiment == "看涨":
            self.insert_text("投资建议: 可以考虑买入，设置止损\n", "bullish")
        elif "中性" in sentiment:
            self.insert_text("投资建议: 观望为主，等待明确信号\n", "neutral")
        else:
            self.insert_text("投资建议: 谨慎操作，考虑减仓或止损\n", "bearish")
        
        self.insert_text("\n⚠️  风险提示: 技术分析仅供参考，投资有风险，请谨慎决策！", "header")
        
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
