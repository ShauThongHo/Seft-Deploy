@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo   音频路由器 Audio Router
echo ========================================
echo.
echo 正在启动应用程序...
echo Starting application...
echo.
C:\Users\hosha\AppData\Local\Programs\Python\Python311\python.exe MultiIO.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 错误: 应用程序异常退出
    echo Error: Application exited abnormally
    pause
)
