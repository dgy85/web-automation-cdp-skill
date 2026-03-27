@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set DEBUG_PORT=9222
set PROFILE_DIR=%TEMP%\chrome-cdp-profile

if "%~1"=="stop" goto do_stop
if "%~1"=="status" goto do_status
if "%~1"=="-s" goto do_stop
if "%~1"=="--stop" goto do_stop

REM =====start=====
REM check if chrome is running via cdp
powershell -Command "Invoke-WebRequest -Uri 'http://127.0.0.1:%DEBUG_PORT%/json' -TimeoutSec 3 -ErrorAction SilentlyContinue" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [INFO] CDP Chrome already running，port: %DEBUG_PORT%
    echo [INFO] WebSocket: ws://127.0.0.1:%DEBUG_PORT%
    echo [INFO] HTTP: http://127.0.0.1:%DEBUG_PORT%/json
    exit /b 0
)

REM find Chrome
set CHROME_PATH=
where chrome 2>nul >nul
if %ERRORLEVEL% equ 0 (
    for /f "delims=" %%i in ('where chrome') do (
        set CHROME_PATH=%%i
        goto :found_chrome
    )
)

if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set CHROME_PATH=%ProgramFiles%\Google\Chrome\Application\chrome.exe
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set CHROME_PATH=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe

:found_chrome
if "%CHROME_PATH%"=="" (
    echo [ERROR] Chrome/Chromium Not Found
    exit /b 1
)

echo [INFO] Start CDP PORT: %DEBUG_PORT%

REM Start Chrome
start "" "%CHROME_PATH%" --remote-debugging-port=%DEBUG_PORT% --user-data-dir="%PROFILE_DIR%" --no-first-run --no-default-browser-check --disable-popup-blocking --disable-infobars --disable-dev-shm-usage --disable-gpu --window-size=1280,720 --remote-allow-origins=* --new-window

timeout /t 3 /nobreak >nul

REM valid
powershell -Command "Invoke-WebRequest -Uri 'http://127.0.0.1:%DEBUG_PORT%/json' -TimeoutSec 5 -ErrorAction SilentlyContinue" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [SUCCESS] CDP Chrome Started，Port: %DEBUG_PORT%
    echo [INFO] WebSocket: ws://127.0.0.1:%DEBUG_PORT%
    echo [INFO] HTTP: http://127.0.0.1:%DEBUG_PORT%/json
    echo [INFO] exec "chrome-cdp.bat stop"
) else (
    echo [ERROR] Fail to start Chrome
    exit /b 1
)
exit /b 0

:do_stop
REM ===== STOP =====
powershell -Command "Invoke-WebRequest -Uri 'http://127.0.0.1:%DEBUG_PORT%/json' -TimeoutSec 3 -ErrorAction SilentlyContinue" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [INFO] CDP Chrome Not Running
    exit /b 0
)

echo [INFO] Kill CDP Chrome...
for /f "tokens=2 delims=:, " %%a in ('netstat -ano ^| findstr ":%DEBUG_PORT% "') do (
    taskkill /F /PID %%a >nul 2>&1
)

timeout /t 1 /nobreak >nul
powershell -Command "Invoke-WebRequest -Uri 'http://127.0.0.1:%DEBUG_PORT%/json' -TimeoutSec 3 -ErrorAction SilentlyContinue" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [SUCCESS] CDP Chrome closed
) else (
    echo [WARN] try to kill process...
    taskkill /F /IM chrome.exe >nul 2>&1
    echo [FINISHED] Process chrome exited
)
exit /b 0

:do_status
REM ===== Status =====
powershell -Command "Invoke-WebRequest -Uri 'http://127.0.0.1:%DEBUG_PORT%/json' -TimeoutSec 3 -ErrorAction SilentlyContinue" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [RUNNING] CDP Chrome，Port: %DEBUG_PORT%
    exit /b 0
) else (
    echo [FAIL] CDP Chrome
    exit /b 1
)