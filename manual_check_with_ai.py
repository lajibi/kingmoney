#!/usr/bin/env python3
"""
手动触发资产查询并发送到 Telegram - 包含 AI 综合研判
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from core.fetcher import DataFetcher
from config.assets_loader import AssetsLoader
from utils.notifier import TelegramNotifier
from core.brain import Brain
from dotenv import load_dotenv
import os

async def manual_check():
    """手动查询所有资产并进行 AI 分析"""
    print("\n" + "="*50)
    print("📊 盖亚系统 - 手动资产查询 (含 AI 研判)")
    print(f"🕐 查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50 + "\n")

    load_dotenv(Path(__file__).parent / "config/.env")

    loader = AssetsLoader(Path(__file__).parent / "config/assets.json")
    assets = loader.get_enabled_assets()
    fetcher = DataFetcher()
    brain = Brain(os.getenv('GEMINI_API_KEY'))
    notifier = TelegramNotifier(
        token=os.getenv('TELEGRAM_BOT_TOKEN'),
        chat_id=os.getenv('TELEGRAM_CHAT_ID'),
        base_url=os.getenv('TELEGRAM_API_BASE_URL')
    )

    print(f"✅ 已加载 {len(assets)} 个监控资产")
    print("📡 正在获取数据...")

    price_map = await fetcher.fetch_all(assets)
    print(f"✅ 获取到 {len(price_map)} 个资产的数据")

    # 构建价格报告
    price_report = [
        "📊 当前市场数据",
        "",
        "━━━━━━━━━━━━━━━",
        ""
    ]

    for asset in assets:
        symbol = asset['symbol']
        data = price_map.get(symbol)
        if data and isinstance(data, dict):
            emoji = "📈" if data.get('change_24h', 0) >= 0 else "📉"
            price_report.append(f"{emoji} {asset['name']}")
            price_report.append(f"   代码: {symbol}")
            price_report.append(f"   价格: {data.get('price', 0):.2f}")
            price_report.append(f"   涨跌: {data.get('change_24h', 0):+.2f}%")
            price_report.append("")
        else:
            price_report.append(f"❌ {asset['name']} - 数据获取失败")
            price_report.append("")

    price_report.append("━━━━━━━━━━━━━━━")
    price_report_text = "\n".join(price_report)

    # 生成 AI 综合研判
    print("🤖 正在进行 AI 综合研判...")
    ai_report = await brain.generate_daily_report(price_map)
    print("✅ AI 分析完成")

    # 合并发送
    full_report = price_report_text + "\n\n" + "🤖 AI 综合研判\n\n" + ai_report + "\n\n✨ 盖亚计划"

    print("📤 正在发送 Telegram 通知...")
    try:
        await notifier.bot.send_message(chat_id=os.getenv('TELEGRAM_CHAT_ID'), text=full_report)
        print("✅ 报告已发送!")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

    await fetcher.close()

if __name__ == "__main__":
    asyncio.run(manual_check())
