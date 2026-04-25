@echo off
setlocal enabledelayedexpansion

rem Move to the directory containing the script file
cd /d "%~dp0"
echo CURRENT_DIR=%cd%

REM [NEW] Kiem tra xem thu muc config da duoc tao chua (Kien truc No-Code)
if not exist "%~dp0config\" (
    echo [ERROR] Khong tim thay thu muc 'config'!
    echo Vui long tao thu muc 'config' va de 2 file .json vao do truoc khi build.
    pause
    exit /b 1
)

REM 1) Initialize venv variable with an absolute path to avoid confusion
set "VENV_DIR="

if exist "%~dp0venv\Scripts\activate.bat" (
    set "VENV_DIR=%~dp0venv"
) else if exist "%~dp0.venv\Scripts\activate.bat" (
    set "VENV_DIR=%~dp0.venv"
)

REM 2) Check if venv was not found
if "%VENV_DIR%"=="" (
    echo [ERROR] Could not find the venv folder or .venv at: %~dp0
    echo Please check the folder structure again.
    pause
    exit /b 1
)

set "VENV_ACT=%VENV_DIR%\Scripts\activate.bat"

REM 3) Activate venv
echo Activating: %VENV_ACT%
call "%VENV_ACT%"

REM 4) Check and install dependencies
echo Checking libraries...
python -c "import pyinstaller" >nul 2>nul
if errorlevel 1 (
    echo Installing pyinstaller...
    pip install pyinstaller
)

python -c "import colorama" >nul 2>nul
if errorlevel 1 (
    echo Installing colorama...
    pip install colorama
)

REM 5) Build exe (Nang cap: Dinh kem thu muc config vao ben trong .exe)
echo Building executable with embedded config...
pyinstaller --onefile --add-data "config;config" git_feature_flow.py

echo.
echo ==============================================================
echo [SUCCESS] Build hoan tat!
echo File .exe da duoc tao trong thu muc 'dist'.
echo Thư mục 'config' da duoc dong goi an toan ben trong file .exe.
echo ==============================================================
pause
endlocal