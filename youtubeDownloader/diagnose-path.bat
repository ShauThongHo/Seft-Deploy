@echo off
echo ========================================
echo YouTube 下载路径诊断工具
echo ========================================
echo.

echo 1. 检查当前工作目录:
echo %CD%
echo.

echo 2. 检查用户主目录:
echo %USERPROFILE%
echo.

echo 3. 检查用户下载文件夹:
if exist "%USERPROFILE%\Downloads" (
    echo %USERPROFILE%\Downloads [存在]
    echo 下载文件夹内容:
    dir /b "%USERPROFILE%\Downloads" | findstr /i "\.mp3 \.m4a \.webm \.ogg \.mp4"
) else (
    echo %USERPROFILE%\Downloads [不存在]
)
echo.

echo 4. 检查当前目录下的音频文件:
dir /b *.mp3 *.m4a *.webm *.ogg *.mp4 2>nul
echo.

echo 5. 测试 yt-dlp 输出路径:
echo 运行一个简单的 yt-dlp 测试...
yt-dlp --print filename -o "%USERPROFILE%\Downloads\%%(title)s.%%(ext)s" "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
echo.

echo 6. 检查 yt-dlp 版本和配置:
yt-dlp --version
echo.

echo ========================================
echo 诊断完成
echo ========================================
pause
