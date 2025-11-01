#!/usr/bin/env python3
"""
简化版OKX实时分析器 - 测试GUI显示
确保图表窗口能正常显示和更新
"""

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import numpy as np
import requests
import threading
import time
from datetime import datetime
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)

class SimpleOKXGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("OKX BTC-USDT 实时价格监控")
        self.root.geometry("1200x800")
        
        # 确保窗口在最前面
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after_idle(lambda: self.root.attributes('-topmost', False))
        
        # 数据存储
        self.prices = []
        self.timestamps = []
        self.max_points = 100
        
        # 创建GUI
        self.setup_gui()
        
        # 启动数据获取线程
        self.data_thread = threading.Thread(target=self.fetch_data_loop, daemon=True)
        self.data_thread.start()
        
        logging.info("简化版GUI已启动")
    
    def setup_gui(self):
        """设置GUI界面"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 状态显示
        self.status_label = ttk.Label(main_frame, text="正在连接...", font=("Arial", 12))
        self.status_label.pack(pady=5)
        
        self.price_label = ttk.Label(main_frame, text="当前价格: --", font=("Arial", 14, "bold"))
        self.price_label.pack(pady=5)
        
        # 创建图表
        self.fig, self.ax = plt.subplots(figsize=(12, 6))
        self.fig.patch.set_facecolor('#1e1e1e')
        self.ax.set_facecolor('#2d2d2d')
        
        # 设置图表样式
        self.ax.tick_params(colors='white')
        self.ax.set_title('BTC-USDT 实时价格', color='white', fontsize=14)
        self.ax.set_xlabel('时间', color='white')
        self.ax.set_ylabel('价格 (USDT)', color='white')
        self.ax.grid(True, alpha=0.3)
        
        # 初始化线条
        self.price_line, = self.ax.plot([], [], 'lime', linewidth=2, label='BTC-USDT')
        self.ax.legend(loc='upper left')
        
        # 将图表嵌入GUI
        self.canvas = FigureCanvasTkAgg(self.fig, main_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 启动动画
        self.animation = FuncAnimation(
            self.fig, 
            self.update_chart, 
            interval=2000,  # 2秒更新一次
            blit=False, 
            cache_frame_data=False
        )
        
        logging.info("GUI界面创建完成")
    
    def fetch_data_loop(self):
        """数据获取循环"""
        while True:
            try:
                # 获取当前价格
                url = "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('code') == '0' and data.get('data'):
                        price = float(data['data'][0]['last'])
                        current_time = datetime.now()
                        
                        # 更新数据
                        self.prices.append(price)
                        self.timestamps.append(current_time)
                        
                        # 限制数据点数量
                        if len(self.prices) > self.max_points:
                            self.prices.pop(0)
                            self.timestamps.pop(0)
                        
                        # 更新GUI标签
                        self.root.after(0, lambda: self.update_labels(price))
                        
                        logging.info(f"获取价格: {price} USDT")
                        
                    else:
                        logging.warning(f"API返回错误: {data}")
                else:
                    logging.error(f"HTTP错误: {response.status_code}")
                    
            except Exception as e:
                logging.error(f"获取数据错误: {e}")
            
            time.sleep(5)  # 5秒获取一次数据
    
    def update_labels(self, price):
        """更新状态标签"""
        try:
            self.status_label.config(text=f"已连接 - 数据点: {len(self.prices)}")
            self.price_label.config(text=f"当前价格: {price:,.2f} USDT")
        except Exception as e:
            logging.error(f"更新标签错误: {e}")
    
    def update_chart(self, frame):
        """更新图表"""
        try:
            if len(self.prices) < 2:
                return
            
            # 更新价格线
            self.price_line.set_data(range(len(self.prices)), self.prices)
            
            # 调整坐标轴
            self.ax.set_xlim(0, max(10, len(self.prices)))
            
            if self.prices:
                price_min = min(self.prices)
                price_max = max(self.prices)
                price_range = price_max - price_min
                margin = price_range * 0.1 if price_range > 0 else 100
                
                self.ax.set_ylim(price_min - margin, price_max + margin)
            
            # 格式化Y轴
            self.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
            
            # 设置X轴标签
            if len(self.timestamps) > 0:
                step = max(1, len(self.timestamps) // 10)
                tick_positions = list(range(0, len(self.timestamps), step))
                tick_labels = [self.timestamps[i].strftime('%H:%M:%S') for i in tick_positions]
                
                self.ax.set_xticks(tick_positions)
                self.ax.set_xticklabels(tick_labels, rotation=45)
            
            self.canvas.draw_idle()
            logging.info(f"图表已更新 - 价格点数: {len(self.prices)}")
            
        except Exception as e:
            logging.error(f"更新图表错误: {e}")
    
    def run(self):
        """运行GUI"""
        try:
            logging.info("启动GUI主循环")
            self.root.mainloop()
        except KeyboardInterrupt:
            logging.info("程序被用户中断")
        except Exception as e:
            logging.error(f"GUI运行错误: {e}")

def main():
    """主函数"""
    try:
        app = SimpleOKXGUI()
        app.run()
    except Exception as e:
        logging.error(f"程序启动错误: {e}")

if __name__ == "__main__":
    main()
