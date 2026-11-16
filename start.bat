@echo off
chcp 65001 >nul
title 黑苹果工具包 v2.0
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo [!] 没有找到 Python。
    echo.
    echo     请先安装 Python 3.9 或更新版本：
    echo     https://www.python.org/downloads/
    echo.
    echo     安装时务必勾选 "Add python.exe to PATH"
    echo.
    pause
    exit /b 1
)

:menu
cls
echo ==============================================
echo   黑苹果工具包 v2.0
echo ==============================================
echo.
echo   [1] 环境自检          检查 Python、路径、文件完整性
echo   [2] 硬件判定          告诉我这台机器能不能装
echo   [3] 生成 EFI          启动 OpCore-Simplify
echo   [4] BIOS 清单         按品牌列必改项
echo   [5] 故障速查          按现象查
echo   [0] 退出
echo.
set /p CHOICE=请选择：

if "%CHOICE%"=="1" goto env
if "%CHOICE%"=="2" goto check
if "%CHOICE%"=="3" goto efi
if "%CHOICE%"=="4" goto bios
if "%CHOICE%"=="5" goto trouble
if "%CHOICE%"=="0" exit /b 0
goto menu

:env
cls
python "scripts\check_env.py"
echo.
pause
goto menu

:check
cls
echo 输入你的硬件，能填多少填多少，不知道的直接回车跳过。
echo.
set /p CPU=CPU 型号（如 i5-10210U）：
set /p GPU=显卡型号（如 UHD 620；有独显再写一个）：
set /p WIFI=无线网卡（如 AX201）：
set /p STORAGE=存储模式（nvme / sata / vmd / raid）：
echo.
python -m hk check --cpu "%CPU%" --gpu "%GPU%" --wifi "%WIFI%" --storage "%STORAGE%"
echo.
set /p PLAN=要不要顺便生成安装计划？(y/n)
if /i "%PLAN%"=="y" (
    python -m hk plan --cpu "%CPU%" --gpu "%GPU%" --wifi "%WIFI%" --storage "%STORAGE%"
)
echo.
pause
goto menu

:efi
cls
echo [*] 启动 OpCore-Simplify...
echo     菜单里选 E 导出硬件报告，再按提示操作。
echo.
cd /d "%~dp0tools\OpCore-Simplify"
python OpCore-Simplify.py
cd /d "%~dp0"
echo.
pause
goto menu

:bios
cls
set /p VENDOR=品牌（lenovo / dell / hp / asus / msi / gigabyte / supermicro）：
python -m hk bios --vendor "%VENDOR%"
echo.
pause
goto menu

:trouble
cls
set /p KW=现象关键词（如 黑屏 / 禁行 / 没声音，直接回车看全部）：
python -m hk troubleshoot %KW%
echo.
pause
goto menu
