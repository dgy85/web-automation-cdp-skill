@echo off
chcp 65001 >nul
REM 启动带远程调试端口的 Chrome (Windows 版本)

set DEBUG_PORT=9222
if not "%DEBUG_PORT%"=="" set DEBUG_PORT=%DEBUG_PORT%
set USER_DATA_DIR=%TEMP%\chrome-cdp-profile

REM 杀掉已有的 chrome 进程
tasklist /FI "IMAGENAME eq chrome.exe" 2>nul | findstr /I "chrome.exe" >nul
if %ERRORLEVEL% equ 0 (
    echo 杀掉已有 Chrome 进程...
    taskkill /F /IM chrome.exe 2>nul
    timeout /t 2 /nobreak >nul
)

REM 查找 Chrome
set CHROME_PATH=
where chrome 2>nul >nul
if %ERRORLEVEL% equ 0 (
    for /f "delims=" %%i in ('where chrome') do (
        set CHROME_PATH=%%i
        goto :found_chrome
    )
)

REM 尝试常见路径
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set CHROME_PATH=%ProgramFiles%\Google\Chrome\Application\chrome.exe
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set CHROME_PATH=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe

:found_chrome
if "%CHROME_PATH%"=="" (
    echo [错误] 未找到 Chrome/Chromium
    exit /b 1
)

echo [信息] 启动 Chrome，调试端口: %DEBUG_PORT%
echo [信息] Chrome 路径: %CHROME_PATH%

REM 启动 Chrome (添加 --remote-allow-origins=* 解决 CDP WebSocket 跨域问题)
start "" "%CHROME_PATH%" --remote-debugging-port=%DEBUG_PORT% --remote-allow-origins=* --user-data-dir="%USER_DATA_DIR%" --no-first-run --no-default-browser-check --disable-popup-blocking --disable-infobars --disable-dev-shm-usage --disable-gpu --window-size=1280,720 --headless=new

timeout /t 3 /nobreak >nul

REM 检查是否启动成功
powershell -Command "Invoke-WebRequest -Uri 'http://127.0.0.1:%DEBUG_PORT%/json' -TimeoutSec 5 -ErrorAction SilentlyContinue" 2>nul
if %ERRORLEVEL% equ 0 (
    echo [成功] Chrome 已启动，调试端口: %DEBUG_PORT%
    echo [信息] WebSocket: ws://127.0.0.1:%DEBUG_PORT%
    echo [信息] HTTP: http://127.0.0.1:%DEBUG_PORT%/json
) else (
    echo [错误] Chrome 启动失败
    exit /b 1
)