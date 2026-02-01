@echo off
REM Project Gaia - Windows 启动脚本

echo 🌍 盖亚计划启动中...

REM 检查 Python 版本
python --version

REM 检查依赖
echo 📦 检查依赖...
pip install -r requirements.txt

REM 运行系统
echo 🚀 启动盖亚系统...
python main.py

pause
