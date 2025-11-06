@echo off
REM One-click launcher for Invoice Generator (Windows)
REM Place this file in the project root and double-click to run the JavaFX app.

SETLOCAL
cd /d "%~dp0"

REM Ensure dependencies are copied (will download if missing)
IF NOT EXIST "target\dependency" (
    echo Copying runtime dependencies...
    mvn -DskipTests dependency:copy-dependencies
)

REM Compile classes if missing
IF NOT EXIST "target\classes" (
    echo Compiling project...
    mvn -DskipTests compile
)

echo Starting Invoice Generator (using Maven javafx:run)...
mvn javafx:run

ENDLOCAL
pause
@echo off
chcp 65001 > nul
echo ================================
echo Starting Invoice Generator...
echo ================================
echo.

cd /d "%~dp0"
echo Current directory: %CD%
echo.

echo Checking Maven...
"C:\Program Files\Apache\maven\bin\mvn.cmd" -version
echo.

echo Building and running application...
echo.
"C:\Program Files\Apache\maven\bin\mvn.cmd" clean javafx:run

echo.
echo ================================
echo Press any key to close...
pause > nul
