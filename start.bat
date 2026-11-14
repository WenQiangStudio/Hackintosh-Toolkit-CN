@echo off
chcp 65001 >nul
title 黑苹果工具包
cd /d "%~dp0"

echo ==============================================
echo   黑苹果工具包 - 开始
echo ==============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [!] 没有找到 Python。
    echo.
    echo     请先安装 Python 3.8 或更新版本：
    echo     https://www.python.org/downloads/
    echo.
    echo     安装时务必勾选 "Add python.exe to PATH"
    echo.
    pause
    exit /b 1
)

echo [*] 正在检查环境...
echo.
python "scripts\check_env.py"
echo.

set /p GO=按回车继续生成 EFI，或直接关掉窗口退出...
if "%GO%"=="" goto build
goto :eof

:build
echo.
echo [*] 启动 OpCore-Simplify...
echo     菜单里选 E 导出硬件报告，再按提示操作。
echo.
cd /d "%~dp0tools\OpCore-Simplify"
python OpCore-Simplify.py
pause
