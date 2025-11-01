@echo off
title OKX K-Line Technical Analysis Tool (Enhanced with Professional Trading Signals)
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                      🚀 OKX K线技术分析器 - 增强版 🚀                        ║
echo ║                          Professional Trading Signal System                   ║
echo ╠══════════════════════════════════════════════════════════════════════════════╣
echo ║                                                                              ║
echo ║  📊 核心功能:                                                                 ║
echo ║  • 六大技术指标: MACD, KDJ, RSI, Williams%%R, BBI, ZLMM                      ║
echo ║  • 智能买卖信号: 🔴红箭头买入 + 🟡黄柱确认 + 🔻绿箭头卖出                      ║
echo ║  • 持有期指导: 🟣洋红色背景显示推荐持有时间                                    ║
echo ║  • 专业图表: 4面板多层次信号展示                                              ║
echo ║                                                                              ║
echo ║  🎯 信号系统:                                                                 ║
echo ║  • 买入信号: 六指标同时确认时显示红色向上箭头                                   ║
echo ║  • 卖出信号: 多维度风险提醒时显示绿色向下箭头                                   ║
echo ║  • 持有指导: 洋红色区域可视化持有期间                                          ║
echo ║                                                                              ║
echo ║  � 使用建议:                                                                 ║
echo ║  • 选择主流交易对 (BTC-USDT, ETH-USDT)                                       ║
echo ║  • 推荐1小时周期，获取300条数据                                               ║
echo ║  • 关注红箭头+黄柱+洋红背景的组合信号                                          ║
echo ║                                                                              ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.
echo 🔥 正在启动增强版OKX K线分析器...
echo 💡 提示: 程序启动后请先选择交易对，然后点击"获取数据"开始分析
echo ⚠️  风险提示: 技术分析信号仅供参考，投资有风险，请谨慎决策！
echo.

cd /d "%~dp0"

echo Checking Python installation...
echo 检查Python安装...
C:\Users\hosha\AppData\Local\Programs\Python\Python311\python.exe --version
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python not found!
    echo 错误：未找到Python！
    pause
    exit /b 1
)

echo.
echo Launching Enhanced OKX K-Line Analyzer with Trading Signals...
echo 启动带交易信号的增强版OKX K线分析器...
echo.

C:\Users\hosha\AppData\Local\Programs\Python\Python311\python.exe okx_kline_analyzer_enhanced.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error occurred while running the application.
    echo 运行应用程序时发生错误。
    echo.
    pause
)

echo.
echo Application closed.
echo 应用程序已关闭。
pause
