@echo off
setlocal enabledelayedexpansion

echo YouTube to MP3 Converter - JavaFX Application
echo ==============================================

:: Check for Java
java -version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Java is not installed or not in PATH
    echo Please install Java JDK 11 or higher
    pause
    exit /b 1
)

:: Try to find JavaFX in common locations
set JAVAFX_PATH=
for %%d in (
    "C:/Users/hosha/Documents/openjfx-21.0.7_windows-x64_bin-sdk/javafx-sdk-21.0.7/lib"
    "C:\Program Files\JavaFX\javafx-sdk-17.0.2\lib"
    "C:\Program Files\JavaFX\javafx-sdk-21.0.1\lib"
    "C:\Program Files\JavaFX\javafx-sdk-19.0.2\lib"
    "C:\javafx\lib"
    "%USERPROFILE%\javafx\lib"
) do (
    if exist "%%~d\javafx.controls.jar" (
        set JAVAFX_PATH=%%~d
        goto found_javafx
    )
)

:found_javafx
if "%JAVAFX_PATH%"=="" (
    echo ERROR: JavaFX not found in common locations
    echo Please download JavaFX SDK from https://gluonhq.com/products/javafx/
    echo And install it to one of these locations:
    echo   - C:\Program Files\JavaFX\javafx-sdk-XX.X.X\lib
    echo   - C:\javafx\lib
    echo   - %USERPROFILE%\javafx\lib
    pause
    exit /b 1
)

echo Found JavaFX at: %JAVAFX_PATH%

:: Check dependencies
echo Checking dependencies...

yt-dlp --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: yt-dlp not found. Install with: pip install yt-dlp
)

ffmpeg -version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: ffmpeg not found. Download from https://ffmpeg.org/
)

:: Compile
echo.
echo Compiling Java application...
javac --module-path "%JAVAFX_PATH%" --add-modules javafx.controls,javafx.fxml youtubeConvertMP3.java

if %ERRORLEVEL% EQU 0 (
    echo Compilation successful!
    echo.
    echo Starting application...
    java --module-path "%JAVAFX_PATH%" --add-modules javafx.controls,javafx.fxml youtubeDownloader.youtubeConvertMP3
) else (
    echo ERROR: Compilation failed!
    echo Make sure JavaFX is properly installed and accessible
    pause
)

endlocal
