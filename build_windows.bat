@echo off
REM Build script for Windows platform
REM 用于构建Windows平台的可执行文件

echo ========================================
echo 邮件用户代理 - Windows构建脚本
echo ========================================
echo.

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

echo Python版本:
python --version
echo.

REM 安装PyInstaller
echo 正在安装PyInstaller...
pip install pyinstaller

REM 检查tkinter
echo.
echo 检查tkinter...
python -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo 警告: 未找到tkinter，请重新安装Python并确保包含tkinter
    pause
    exit /b 1
)

REM 清理旧的构建文件
echo.
echo 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec

REM 构建可执行文件
echo.
echo 正在构建Windows可执行文件...
pyinstaller --onefile --windowed --name EmailClient-Windows main.py

REM 检查构建结果
if exist "dist\EmailClient-Windows.exe" (
    echo.
    echo ========================================
    echo 构建成功！
    echo ========================================
    echo 可执行文件位置: dist\EmailClient-Windows.exe
    echo.
    echo 使用方法: 双击 dist\EmailClient-Windows.exe 运行
    echo.
) else (
    echo.
    echo ========================================
    echo 构建失败！
    echo ========================================
    echo 请检查错误信息
    pause
    exit /b 1
)

pause
