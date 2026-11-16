@echo off
chcp 65001 >nul
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo [!] 没有找到 Python。安装时务必勾选 "Add python.exe to PATH"
    echo     https://www.python.org/downloads/
    pause
    exit /b 1
)

if "%~1"=="" (
    echo 用法示例：
    echo    hk check --cpu i5-10210U --gpu "UHD 620" --gpu MX250 --wifi AX201 --storage nvme
    echo    hk plan  --platform laptop --cpu i5-10210U --gpu "UHD 620"
    echo    hk bios  --vendor lenovo
    echo    hk troubleshoot 黑屏
    echo.
    echo 完整说明见 docs/08-cli.md
    pause
    exit /b 0
)

python -m hk %*
echo.
pause
