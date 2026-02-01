#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Bot 命令处理器 - 支持对话交互
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from core.fetcher import DataFetcher
from config.assets_loader import AssetsLoader
from core.brain_deepseek import BrainDeepSeek
from dotenv import load_dotenv

# 加载配置
load_dotenv(Path(__file__).parent / "config/.env")

# 初始化组件
loader = AssetsLoader(Path(__file__).parent / "config/assets.json")
assets = loader.get_enabled_assets()
fetcher = DataFetcher()
brain = BrainDeepSeek(api_key='sk-78a20b30abf1443e837076082e0d1727')
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

💬 对话交互：
直接向我发送任何问题，我会用 AI 回答你！
例如：
- "比特币值得投资吗？"
- "分析一下以太坊走势"
- "今天市场怎么样？"

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


async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理用户消息 - AI 对话"""
    try:
        user_message = update.message.text
        
        # 如果是命令，不处理
        if user_message.startswith('/'):
            return
        
        # 显示正在思考
        status_msg = await update.message.reply_text("🤔 正在思考...")
        
        # 获取当前市场数据作为上下文
        price_map = await fetcher.fetch_all(assets)
        context_info = "\n".join([
            f"{symbol}: {data['price']} ({data['change_24h']:+.2f}%)"
            for symbol, data in price_map.items()
        ])
        
        # AI 回答
        ai_response = await brain.chat(user_message, context_info)
        
        # 删除状态消息，发送回复
        await status_msg.delete()
        
        # 分段发送回复
        chunks = []
        current_chunk = ai_response
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
                await asyncio.sleep(0.5)
        
    except Exception as e:
        await update.message.reply_text(f"❌ 处理失败: {str(e)}")


async def main():
    """启动 bot"""
    # 注册命令处理器
    application.add_handler(CommandHandler("check", check_command))
    application.add_handler(CommandHandler("report", report_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # 注册消息处理器（处理非命令消息，用于对话）
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler))
    
    print("🤖 Bot 已启动，等待命令和对话...")
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
