@echo off
echo Compiling Java application...
javac --module-path "C:\Program Files\JavaFX\javafx-sdk-17.0.2\lib" --add-modules javafx.controls,javafx.fxml youtubeConvertMP3.java

if %ERRORLEVEL% EQU 0 (
    echo Compilation successful. Running application...
    java --module-path "C:\Program Files\JavaFX\javafx-sdk-17.0.2\lib" --add-modules javafx.controls,javafx.fxml youtubeDownloader.youtubeConvertMP3
) else (
    echo Compilation failed!
    pause
)
