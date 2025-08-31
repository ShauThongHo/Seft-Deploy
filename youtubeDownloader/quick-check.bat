@echo off
echo ==========================================
echo 快速检查下载文件
echo ==========================================
echo.

echo 1. 下载文件夹中的所有音频/视频文件:
echo ==========================================
for %%f in ("%USERPROFILE%\Downloads\*.mp4" "%USERPROFILE%\Downloads\*.m4a" "%USERPROFILE%\Downloads\*.webm" "%USERPROFILE%\Downloads\*.ogg" "%USERPROFILE%\Downloads\*.mp3" "%USERPROFILE%\Downloads\*.wav") do (
    if exist "%%f" (
        echo 📁 %%~nxf
        echo    大小: %%~zf bytes
        echo    修改时间: %%~tf
        echo.
    )
)

echo.
echo 2. 最近5分钟内修改的所有文件:
echo ==========================================
forfiles /p "%USERPROFILE%\Downloads" /m *.* /d +0 /c "cmd /c echo 📄 @file - @fsize bytes - @fdate @ftime" 2>nul

echo.
echo 3. 文件夹总览:
echo ==========================================
echo 下载文件夹位置: %USERPROFILE%\Downloads
dir "%USERPROFILE%\Downloads" /q | find "个文件"

echo.
echo 4. 可能的音频文件 (包括隐藏和系统文件):
echo ==========================================
dir "%USERPROFILE%\Downloads\*.*" /a /b | findstr /i "\.mp4$ \.m4a$ \.webm$ \.ogg$ \.mp3$ \.wav$"

echo.
echo ==========================================
echo 检查完成！
echo ==========================================
echo.
echo 如果看到文件但无法播放，可能是:
echo 1. 文件损坏 (大小为0或很小)
echo 2. 格式不支持
echo 3. 下载未完成
echo.
pause
