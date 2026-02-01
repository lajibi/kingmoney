#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动查询资产情况 - 支持 AI 综合研判
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from core.fetcher import DataFetcher
from config.assets_loader import AssetsLoader
from core.brain import GaiaBrain
from database.models import DatabaseManager
from dotenv import load_dotenv
import os


async def manual_check():
    print("Starting manual check...")
    load_dotenv(Path(__file__).parent / "config/.env")
    
    loader = AssetsLoader(Path(__file__).parent / "config/assets.json")
    assets = loader.get_enabled_assets()
    fetcher = DataFetcher()
    
    print(f"Fetching data for {len(assets)} assets...")
    price_map = await fetcher.fetch_all(assets)
    print(f"Got data for {len(price_map)} assets")
    
    # 初始化 AI brain 并生成综合研判
    db_manager = DatabaseManager(Path(__file__).parent / "database/gaia.db")
    brain = GaiaBrain(api_key=os.getenv('GEMINI_API_KEY'), db_manager=db_manager)
    
    print("Generating AI comprehensive analysis...")
    ai_report = await brain.generate_daily_report(price_map)
    
    # 构建报告
    report = "📋 资产查询报告\n\n"
    report += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    report += "━━━━━━━━━━━━━━━\n\n"
    
    for asset in assets:
        symbol = asset['symbol']
        data = price_map.get(symbol)
        print(f"Asset: {asset['name']}, Data exists: {data is not None}")
        
        if data and isinstance(data, dict):
            emoji = "📈" if data.get('change_24h', 0) >= 0 else "📉"
            report += f"{emoji} {asset['name']}\n"
            report += f"   代码: {symbol}\n"
            report += f"   价格: {data.get('price', 0):.2f}\n"
            report += f"   涨跌: {data.get('change_24h', 0):+.2f}%\n\n"
        else:
            report += f"❌ {asset['name']} - 数据获取失败\n\n"
    
    report += "━━━━━━━━━━━━━━━\n\n"
    report += "✨ 盖亚计划\n\n"
    
    # 添加 AI 综合研判
    report += "🤖 AI 综合研判\n"
    report += "━" * 25 + "\n\n"
    report += ai_report
    report += "\n\n" + "━" * 25
    
    print(f"Report length: {len(report)}")
    print("Sending report...")
    
    # 通过 Telegram 发送报告
    from telegram import Bot
    
    base_url = os.getenv('TELEGRAM_API_BASE_URL')
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    try:
        if base_url and base_url.strip():
            bot = Bot(token=token, base_url=base_url)
        else:
            bot = Bot(token=token)
        
        # 分段发送，避免超长消息
        chunks = []
        current_chunk = report
        while len(current_chunk) > 4000:
            split_pos = current_chunk.rfind('\n', 0, 4000)
            if split_pos == -1:
                split_pos = 4000
            chunks.append(current_chunk[:split_pos])
            current_chunk = current_chunk[split_pos:]
        chunks.append(current_chunk)
        
        for i, chunk in enumerate(chunks, 1):
            await bot.send_message(chat_id=chat_id, text=chunk)
            if i < len(chunks):
                await asyncio.sleep(1)
        
        print("✅ Report sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send report: {e}")
        print("\n" + "=" * 60)
        print("REPORT CONTENT:")
        print("=" * 60)
        print(report)
    
    await fetcher.close()


if __name__ == "__main__":
    asyncio.run(manual_check())
