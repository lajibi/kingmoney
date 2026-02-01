#!/bin/bash
# Project Gaia - 启动脚本

echo "🌍 盖亚计划启动中..."

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python 版本: $python_version"

# 检查依赖
echo "📦 检查依赖..."
pip3 install -r requirements.txt

# 运行系统
echo "🚀 启动盖亚系统..."
python3 main.py
