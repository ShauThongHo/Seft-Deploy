@echo off
chcp 65001 > nul
title OKX实时交易分析器 v2.1 - 带交易功能版

echo.
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                  🚀 OKX 实时交易分析器 v2.1 交易版 🚀                     ║
echo ║                   Enhanced Real-time Trading Analysis System                  ║
echo ╠══════════════════════════════════════════════════════════════════════════════╣
echo ║                                                                              ║
echo ║  💰 新增交易功能:                                                           ║
echo ║  • 实盘交易支持 - 根据技术信号自动买卖                                      ║
echo ║  • 智能风险管理 - 止损止盈保护                                              ║
echo ║  • 多重安全机制 - 防止过度交易                                              ║
echo ║  • 实时交易监控 - 持仓状态显示                                              ║
echo ║                                                                              ║
echo ║  📊 技术指标 实时计算:                                                       ║
echo ║  • MACD - 平滑异同平均线                                                     ║
echo ║  • KDJ - 随机指标                                                            ║
echo ║  • RSI - 相对强弱指数                                                        ║
echo ║  • Williams %R - 威廉指标                                                    ║
echo ║  • BBI - 多空指标                                                            ║
echo ║  • ZLMM - 零滞后动量指标                                                     ║
echo ║                                                                              ║
echo ║  🛡️ 安全提醒:                                                                ║
echo ║  • 当前设置: 模拟交易模式 (sandbox=true)                                     ║
echo ║  • 默认交易: 关闭状态，需手动启用                                            ║
echo ║  • 建议先测试: 模拟环境验证后再实盘                                          ║
echo ║  • 风险提示: 请设置合理的交易金额                                            ║
echo ║                                                                              ║
echo ║  🔧 配置文件: trading_config.json                                           ║
echo ║  📚 使用说明: 交易功能使用说明.md                                            ║
echo ║                                                                              ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝

echo.
echo 🔍 正在检查Python环境...
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未找到Python环境！
    echo 💡 请先安装Python 3.8或更高版本
    pause
    exit /b 1
)

echo ✅ Python环境检查通过
echo.

echo 🔍 正在检查依赖库...
python -c "import requests, pandas, numpy, matplotlib, tkinter, websocket" > nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 缺少必要的依赖库！
    echo 💡 正在安装依赖...
    pip install requests pandas numpy matplotlib websocket-client
)

echo ✅ 依赖检查通过
echo.

echo 🔍 正在检查配置文件...
if not exist "trading_config.json" (
    echo ❌ 缺少交易配置文件！
    echo 💡 请确保 trading_config.json 文件存在并配置正确的API密钥
    pause
    exit /b 1
)

echo ✅ 配置文件检查通过
echo.

echo 🚀 正在启动实时交易分析器...
echo 💡 提示: 程序启动后可在界面中控制是否启用实盘交易
echo 🔍 如遇问题，请查看终端输出信息
echo ⚠️  风险提示: 实盘交易有风险，请谨慎操作！

python okx_realtime_analyzer.py

echo.
echo ✅ 程序正常结束
echo 📊 感谢使用OKX实时交易分析器！
echo 🔗 如有问题，请查看使用说明文档
pause
