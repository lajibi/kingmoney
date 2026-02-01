#!/usr/bin/env python3
"""
手动触发资产查询并发送到 Telegram
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "Project_Gaia"))

from core.fetcher import DataFetcher
from config.assets_loader import AssetsLoader
from utils.notifier import TelegramNotifier
from dotenv import load_dotenv
import os

async def manual_check():
    """手动查询所有资产并发送报告"""
    print("\n" + "="*50)
    print("📊 盖亚系统 - 手动资产查询")
    print(f"🕐 查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50 + "\n")

    # 加载配置
    load_dotenv(Path(__file__).parent / "Project_Gaia/config/.env")

    # 初始化组件
    loader = AssetsLoader(Path(__file__).parent / "Project_Gaia/config/assets.json")
    assets = loader.get_enabled_assets()
    fetcher = DataFetcher()
    notifier = TelegramNotifier(
        token=os.getenv('TELEGRAM_BOT_TOKEN'),
        chat_id=os.getenv('TELEGRAM_CHAT_ID'),
        base_url=os.getenv('TELEGRAM_API_BASE_URL')
    )

    print(f"✅ 已加载 {len(assets)} 个监控资产")

    # 抓取数据
    print("📡 正在获取数据...")
    price_data = await fetcher.fetch_all(assets)

    # 构建报告
    report_lines = [
        "📋 资产查询报告",
        "",
        f"📅 查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "━━━━━━━━━━━━━━━",
        ""
    ]

    for asset, data in zip(assets, price_data):
        if data and 'price' in data:
            emoji = "📈" if data.get('change', 0) >= 0 else "📉"
            report_lines.append(f"{emoji} {data.get('name', 'N/A')}")
            report_lines.append(f"   代码: {data.get('symbol', 'N/A')}")
            report_lines.append(f"   价格: {data.get('price', 0):.2f}")
            report_lines.append(f"   涨跌: {data.get('change', 0):+.2%}")
            report_lines.append("")
        else:
            report_lines.append(f"❌ {asset['name']} - 数据获取失败")
            report_lines.append("")

    report_lines.append("━━━━━━━━━━━━━━━")
    report_lines.append("")
    report_lines.append("✨ 盖亚计划 - 凡人财务自由防御系统")

    report = "\n".join(report_lines)

    # 发送报告
    print("📤 正在发送 Telegram 通知...")
    try:
        await notifier.bot.send_message(
            chat_id=os.getenv('TELEGRAM_CHAT_ID'),
            text=report
        )
        print("✅ 报告已发送!")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

    # 清理资源
    await fetcher.close()

if __name__ == "__main__":
    asyncio.run(manual_check())
