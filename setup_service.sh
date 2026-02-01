#!/bin/bash
# 创建 systemd 服务文件
cat > /etc/systemd/system/gaia.service << 'EOF'
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

systemctl daemon-reload
systemctl enable gaia
systemctl start gaia
systemctl status gaia
