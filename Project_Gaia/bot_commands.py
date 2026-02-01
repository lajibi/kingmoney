#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Bot 命令处理器
支持用户通过 Telegram 发送命令查询资产和获取 AI 研判
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from core.fetcher import DataFetcher
from config.assets_loader import AssetsLoader
from core.brain import GaiaBrain
from database.models import DatabaseManager
from dotenv import load_dotenv

# 加载配置
load_dotenv(Path(__file__).parent / "config/.env")

# 初始化组件
loader = AssetsLoader(Path(__file__).parent / "config/assets.json")
assets = loader.get_enabled_assets()
fetcher = DataFetcher()
db_manager = DatabaseManager(Path(__file__).parent / "database/gaia.db")
brain = GaiaBrain(api_key=os.getenv('GEMINI_API_KEY'), db_manager=db_manager)
base_url = os.getenv('TELEGRAM_API_BASE_URL')

# 创建 bot 应用
application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
if base_url and base_url.strip():
    application.builder.base_url = base_url


async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """手动查询资产情况"""
    chat_id = update.effective_chat.id
    
    try:
        await update.message.reply_text("🔍 正在查询资产数据...")
        
        price_map = await fetcher.fetch_all(assets)
        
        # 生成 AI 综合研判
        ai_report = await brain.generate_daily_report(price_map)
        
        # 构建报告
        report = f"📋 资产查询报告\n\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        report += "━━━━━━━━━━━━━━━\n\n"
        
        for asset in assets:
            symbol = asset['symbol']
            data = price_map.get(symbol)
            if data and isinstance(data, dict):
                emoji = "📈" if data.get('change_24h', 0) >= 0 else "📉"
                report += f"{emoji} {asset['name']}\n"
                report += f"   代码: {symbol}\n"
                report += f"   价格: {data.get('price', 0):.2f}\n"
                report += f"   涨跌: {data.get('change_24h', 0):+.2f}%\n\n"
            else:
                report += f"❌ {asset['name']} - 数据获取失败\n\n"
        
        report += "━━━━━━━━━━━━━━━\n\n✨ 盖亚计划\n\n"
        report += "🤖 AI 综合研判\n"
        report += "━" * 25 + "\n\n"
        report += ai_report
        report += "\n\n" + "━" * 25
        
        # 分段发送
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
            await update.message.reply_text(chunk)
            if i < len(chunks):
                await asyncio.sleep(1)
                
    except Exception as e:
        await update.message.reply_text(f"❌ 查询失败: {str(e)}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """显示帮助信息"""
    help_text = """📖 盖亚计划命令帮助

可用命令:
/check - 查询当前所有资产情况（含 AI 综合研判）
/report - 同 /check 命令
/help - 显示此帮助信息

━━━━━━━━━━━━━━━

💡 提示：
- 系统会自动监控资产，触发告警时推送通知
- 每日 22:30 自动发送复盘报告
- 使用 /check 可随时手动查询最新情况
"""
    await update.message.reply_text(help_text)


async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """生成 AI 综合研判报告（同 check 命令）"""
    await check_command(update, context)


async def main():
    """启动 bot"""
    # 注册命令处理器
    application.add_handler(CommandHandler("check", check_command))
    application.add_handler(CommandHandler("report", report_command))
    application.add_handler(CommandHandler("help", help_command))
    
    print("🤖 Bot 已启动，等待命令...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    # 保持运行
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        print("\n⌨️ 收到中断信号，正在停止 bot...")
    finally:
        await fetcher.close()


if __name__ == "__main__":
    asyncio.run(main())
