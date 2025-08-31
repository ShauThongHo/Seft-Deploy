@echo off
title OKX 实时K线技术分析器 v2.0 (增强连接版)
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                  🚀 OKX 实时K线技术分析器 v2.0 (增强版) 🚀                  ║
echo ║                      Enhanced Real-time Trading Signal System                 ║
echo ╠══════════════════════════════════════════════════════════════════════════════╣
echo ║                                                                              ║
echo ║  � 连接优化特性:                                                             ║
echo ║  • 智能重连机制 - 指数退避算法，自动恢复连接                                  ║
echo ║  • 连接健康检查 - 实时监控连接状态                                            ║
echo ║  • Ping保活机制 - 防止连接超时断开                                           ║
echo ║  • 网络诊断功能 - 启动前检测网络连通性                                        ║
echo ║                                                                              ║
echo ║  📊 技术指标 (实时计算):                                                      ║
echo ║  • MACD - 平滑异同平均线                                                     ║
echo ║  • KDJ - 随机指标                                                            ║
echo ║  • RSI - 相对强弱指数                                                        ║
echo ║  • Williams %%R - 威廉指标                                                    ║
echo ║  • BBI - 多空指标                                                            ║
echo ║  • ZLMM - 零滞后动量指标                                                     ║
echo ║                                                                              ║
echo ║  🎯 实时信号系统:                                                             ║
echo ║  • 🔴 红色向上箭头: 六指标确认买入信号                                        ║
echo ║  • 🟡 黄色信号柱: 买入信号确认                                                ║
echo ║  • 🔻 绿色向下箭头: 多维度卖出信号                                            ║
echo ║  • 🟣 洋红色背景: 推荐持有期间                                                ║
echo ║                                                                              ║
echo ║  🔍 连接监控:                                                                 ║
echo ║  • 连接状态: 实时显示WebSocket连接状态                                        ║
echo ║  • 详情按钮: 查看详细连接信息                                                 ║
echo ║  • 自动诊断: 启动时进行网络连通性测试                                         ║
echo ║  • 重连统计: 显示重连次数和成功率                                             ║
echo ║                                                                              ║
echo ║  � 使用建议:                                                                 ║
echo ║  • 确保网络连接稳定                                                          ║
echo ║  • 关闭VPN或代理软件 (如非必要)                                               ║
echo ║  • 允许防火墙通过Python程序                                                  ║
echo ║  • 选择活跃交易对以获得更好的数据流                                           ║
echo ║                                                                              ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.
echo 🔍 正在进行连接预检查...

REM 检查网络连通性
echo 📡 测试与OKX服务器的连接...
ping -n 2 ws.okx.com > nul
if errorlevel 1 (
    echo ❌ 网络连接测试失败！
    echo � 请检查:
    echo    1. 网络连接是否正常
    echo    2. DNS设置是否正确
    echo    3. 防火墙或代理设置
    echo.
    pause
    exit /b 1
) else (
    echo ✅ 网络连接测试通过
)

echo.
echo �🔥 正在启动实时K线分析器...
echo 💡 提示: 程序启动后点击"开始实时分析"开始接收实时数据
echo 🔍 如遇连接问题，请点击"详情"按钮查看连接状态
echo ⚠️  网络提示: 需要稳定的网络连接以确保实时数据接收
echo ⚠️  风险提示: 实时信号仅供参考，请结合多种分析方法谨慎决策！
echo.
timeout /t 3 /nobreak > nul

cd /d "%~dp0"
python okx_realtime_analyzer.py

if errorlevel 1 (
    echo.
    echo ❌ 程序运行出错！
    echo 💡 常见问题解决:
    echo.
    echo 🔧 依赖问题:
    echo    pip install websocket-client requests pandas numpy matplotlib
    echo.
    echo 🌐 网络问题:
    echo    1. 检查网络连接稳定性
    echo    2. 尝试关闭VPN或代理
    echo    3. 检查防火墙设置
    echo    4. 确认DNS设置正确
    echo.
    echo 🔥 防火墙问题:
    echo    允许Python程序访问网络
    echo    添加程序到防火墙白名单
    echo.
    echo � OKX服务问题:
    echo    1. OKX可能正在维护
    echo    2. 尝试稍后重试
    echo    3. 检查OKX官方公告
    echo.
    pause
) else (
    echo.
    echo ✅ 程序正常结束
    echo 📊 感谢使用OKX实时K线技术分析器！
    echo 🔗 如有问题，请查看连接详情或重新启动程序
    echo.
    timeout /t 2 /nobreak > nul
)
