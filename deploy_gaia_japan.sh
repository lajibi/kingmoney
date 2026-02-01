#!/bin/bash
# Project Gaia 部署脚本 - 日本实例 lhins-avu0wxv3

set -e

PROJECT_DIR="/root/Project_Gaia_20260130212533"
SERVICE_FILE="/etc/systemd/system/gaia.service"

echo "=========================================="
echo "开始部署 Project Gaia 到日本实例"
echo "=========================================="

# 1. 创建虚拟环境并安装依赖
echo "[1/5] 创建虚拟环境并安装依赖..."
cd $PROJECT_DIR

if [ ! -d "venv" ]; then
    echo "  创建 Python 虚拟环境..."
    python3 -m venv venv
fi

echo "  安装依赖包..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 2. 创建日志目录
echo "[2/5] 创建日志目录..."
mkdir -p $PROJECT_DIR/logs

# 3. 配置 systemd 服务
echo "[3/5] 配置 systemd 服务..."
cat > $SERVICE_FILE << 'EOF'
[Unit]
Description=Project Gaia - 财务监控系统
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/Project_Gaia_20260130212533
Environment="PATH=/root/Project_Gaia_20260130212533/venv/bin"
ExecStart=/root/Project_Gaia_20260130212533/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=append:/root/Project_Gaia_20260130212533/logs/gaia.log
StandardError=append:/root/Project_Gaia_20260130212533/logs/gaia_error.log

[Install]
WantedBy=multi-user.target
EOF

# 4. 重载 systemd 并启动服务
echo "[4/5] 配置 systemd 服务..."
systemctl daemon-reload
systemctl enable gaia
systemctl restart gaia

# 5. 等待几秒后检查服务状态
sleep 3
echo "[5/5] 检查服务状态..."
systemctl status gaia --no-pager

echo ""
echo "=========================================="
echo "✅ Project Gaia 部署完成!"
echo "=========================================="
echo ""
echo "查看日志: tail -f $PROJECT_DIR/logs/gaia.log"
echo "服务状态: systemctl status gaia"
echo "重启服务: systemctl restart gaia"
echo "停止服务: systemctl stop gaia"
echo ""
