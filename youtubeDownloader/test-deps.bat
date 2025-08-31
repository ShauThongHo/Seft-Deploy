@echo off
echo 测试依赖项...
echo.

echo 测试 yt-dlp:
yt-dlp --version 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✅ yt-dlp 可用
) else (
    echo ❌ yt-dlp 不可用
)

echo.
echo 测试 ffmpeg:
ffmpeg -version 2>nul | findstr "ffmpeg version"
if %ERRORLEVEL% EQU 0 (
    echo ✅ ffmpeg 可用
) else (
    echo ❌ ffmpeg 不可用
)

echo.
echo 测试完成。
pause
