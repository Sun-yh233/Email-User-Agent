#!/bin/bash
# Build script for Linux platform
# 用于构建Linux平台的可执行文件

echo "========================================"
echo "邮件用户代理 - Linux构建脚本"
echo "========================================"
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

echo "Python版本:"
python3 --version
echo ""

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo "错误: 未找到pip3，请先安装pip3"
    exit 1
fi

# 安装PyInstaller
echo "正在安装PyInstaller..."
pip3 install pyinstaller

# 检查tkinter
echo ""
echo "检查tkinter..."
python3 -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "警告: 未找到tkinter，请安装:"
    echo "  Ubuntu/Debian: sudo apt-get install python3-tk"
    echo "  CentOS/RHEL: sudo yum install python3-tkinter"
    echo "  Fedora: sudo dnf install python3-tkinter"
    exit 1
fi

# 清理旧的构建文件
echo ""
echo "清理旧的构建文件..."
rm -rf build dist *.spec

# 构建可执行文件
echo ""
echo "正在构建Linux可执行文件..."
pyinstaller --onefile --windowed --name EmailClient-Linux main.py

# 检查构建结果
if [ -f "dist/EmailClient-Linux" ]; then
    echo ""
    echo "========================================"
    echo "构建成功！"
    echo "========================================"
    echo "可执行文件位置: dist/EmailClient-Linux"
    echo ""
    echo "使用方法:"
    echo "  chmod +x dist/EmailClient-Linux"
    echo "  ./dist/EmailClient-Linux"
    echo ""
    
    # 自动添加执行权限
    chmod +x dist/EmailClient-Linux
    echo "已自动添加执行权限"
else
    echo ""
    echo "========================================"
    echo "构建失败！"
    echo "========================================"
    echo "请检查错误信息"
    exit 1
fi
