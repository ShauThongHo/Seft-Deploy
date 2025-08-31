#!/usr/bin/env python3
"""
测试图表显示是否正常
"""
import matplotlib.pyplot as plt
import numpy as np
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def test_chart():
    # 创建主窗口
    root = tk.Tk()
    root.title("图表测试")
    root.geometry("800x600")
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('#1e1e1e')
    ax.set_facecolor('#2d2d2d')
    
    # 生成测试数据
    x = np.linspace(0, 10, 100)
    y = np.sin(x) * 100 + 108900  # 模拟BTC价格
    
    # 绘制
    ax.plot(x, y, 'lime', linewidth=2, label='BTC价格')
    ax.set_title('测试图表', color='white', fontsize=14)
    ax.set_xlabel('时间', color='white')
    ax.set_ylabel('价格', color='white')
    ax.tick_params(colors='white')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # 嵌入到tkinter
    canvas = FigureCanvasTkAgg(fig, root)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    print("测试图表已创建，如果你能看到这个窗口，说明matplotlib显示正常")
    
    root.mainloop()

if __name__ == "__main__":
    test_chart()
