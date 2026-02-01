#!/bin/bash
# Project Gaia 部署脚本 - 日本实例 lhins-avu0wxv3
# 使用 ubuntu 用户登录,通过 sudo 执行管理操作

set -e

PROJECT_DIR="/root/Project_Gaia_20260130212533"
SERVICE_FILE="/etc/systemd/system/gaia.service"

echo "=========================================="
echo "开始部署 Project Gaia 到日本实例"
echo "=========================================="

# 1. 检查项目目录
echo "[1/7] 检查项目目录..."
sudo ls -la $PROJECT_DIR
echo "  ✓ 项目目录存在"

# 2. 创建虚拟环境
echo "[2/7] 创建 Python 虚拟环境..."
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo "  创建虚拟环境..."
    sudo python3 -m venv $PROJECT_DIR/venv
else
    echo "  虚拟环境已存在,跳过创建"
fi

# 3. 安装依赖
echo "[3/7] 安装 Python 依赖包..."
sudo $PROJECT_DIR/venv/bin/pip install --upgrade pip
sudo $PROJECT_DIR/venv/bin/pip install -r $PROJECT_DIR/requirements.txt
echo "  ✓ 依赖安装完成"

# 4. 创建日志目录
echo "[4/7] 创建日志目录..."
sudo mkdir -p $PROJECT_DIR/logs
echo "  ✓ 日志目录已创建"

# 5. 验证配置文件
echo "[5/7] 验证配置文件..."
echo "  环境变量配置:"
sudo cat $PROJECT_DIR/config/.env | grep -E "TELEGRAM|GEMINI"
echo "  ✓ 配置文件验证完成"

# 6. 配置 systemd 服务
echo "[6/7] 配置 systemd 服务..."
sudo bash -c "cat > $SERVICE_FILE << 'EOF'
[Unit]
Description=Project Gaia - 财务监控系统
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR
Environment=\"PATH=$PROJECT_DIR/venv/bin\"
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=append:$PROJECT_DIR/logs/gaia.log
StandardError=append:$PROJECT_DIR/logs/gaia_error.log

[Install]
WantedBy=multi-user.target
EOF"
echo "  ✓ 服务文件已创建"

# 7. 启动服务
echo "[7/7] 启动 Gaia 服务..."
sudo systemctl daemon-reload
sudo systemctl enable gaia
sudo systemctl restart gaia

sleep 3
echo ""
echo "=========================================="
echo "✅ Project Gaia 部署完成!"
echo "=========================================="
echo ""
echo "服务状态:"
sudo systemctl status gaia --no-pager -l
echo ""
echo "=========================================="
echo "常用命令:"
echo "=========================================="
echo "查看服务状态: sudo systemctl status gaia"
echo "查看实时日志: sudo tail -f $PROJECT_DIR/logs/gaia.log"
echo "重启服务: sudo systemctl restart gaia"
echo "停止服务: sudo systemctl stop gaia"
echo "查看错误日志: sudo tail -f $PROJECT_DIR/logs/gaia_error.log"
echo ""
