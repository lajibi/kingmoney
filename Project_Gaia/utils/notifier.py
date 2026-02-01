"""
Telegram 通知系统
支持 Markdown 格式消息推送
"""

import asyncio
import os
from datetime import datetime
from typing import Dict, Optional

from telegram import Bot
from telegram.constants import ParseMode
from utils.logger import GaiaLogger


class TelegramNotifier:
    """Telegram 通知器"""

    def __init__(self, token: str, chat_id: str, base_url: Optional[str] = None):
        """
        初始化通知器

        Args:
            token: Telegram Bot Token
            chat_id: 接收消息的 Chat ID
            base_url: Telegram API 代理地址 (可选)
        """
        self.logger = GaiaLogger("Notifier")

        # 如果提供了 base_url 且不为空,则使用代理,否则使用默认 API 地址
        if base_url and base_url.strip():
            self.logger.info(f"📡 使用 Telegram API 代理: {base_url}")
            self.bot = Bot(token=token, base_url=base_url)
        else:
            self.bot = Bot(token=token)

        self.chat_id = chat_id

    async def send_alert(self, alert: Dict, analysis: str):
        """
        发送告警消息

        Args:
            alert: 告警数据
            analysis: AI 分析结果
        """
        try:
            # 构建 Markdown 格式消息
            emoji = "🔴" if alert['volatility'] < 0 else "🟢"
            direction = "下跌" if alert['volatility'] < 0 else "上涨"

            message = f"""
{emoji} *{alert['name']} 异常波动*

━━━━━━━━━━━━━━━

📊 *当前价格*: `{alert['current_price']}`
📈 *波动幅度*: {alert['volatility']:+.2f}%
🔔 *告警级别*: {self._get_level_emoji(alert['level'])}
⏰ *触发时间*: {alert['timestamp'].strftime('%H:%M:%S')}

━━━━━━━━━━━━━━━

🤖 *AI 分析*:

{analysis}

━━━━━━━━━━━━━━━

📌 *操作建议*:
{self._extract_suggestion(analysis)}

⚠️ *风险提示*: 市场有风险，投资需谨慎
"""

            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN_V2
            )

            self.logger.info(f"告警已发送: {alert['symbol']}")

        except Exception as e:
            self.logger.error(f"发送告警失败: {e}")

    async def send_daily_report(self, report: str):
        """
        发送每日复盘报告

        Args:
            report: 报告内容
        """
        try:
            message = f"""
📋 *每日市场复盘报告*

━━━━━━━━━━━━━━━

📅 报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}

━━━━━━━━━━━━━━━

{report}

━━━━━━━━━━━━━━━

✨ 盖亚计划 - 凡人财务自由防御系统
"""

            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN_V2
            )

            self.logger.info("每日报告已发送")

        except Exception as e:
            self.logger.error(f"发送每日报告失败: {e}")

    async def send_heartbeat(self):
        """发送心跳消息 (用于健康检查)"""
        try:
            message = f"""
💓 *系统运行正常*

━━━━━━━━━━━━━━━

🕐 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
✅ 盖亚系统持续监控中

━━━━━━━━━━━━━━━
"""

            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN_V2
            )

        except Exception as e:
            self.logger.error(f"发送心跳失败: {e}")

    async def send_error(self, error_msg: str):
        """
        发送错误消息

        Args:
            error_msg: 错误信息
        """
        try:
            message = f"""
❌ *系统异常*

━━━━━━━━━━━━━━━

⚠️ {error_msg}

⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

━━━━━━━━━━━━━━━
"""

            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN_V2
            )

        except Exception as e:
            self.logger.error(f"发送错误消息失败: {e}")

    def _get_level_emoji(self, level: str) -> str:
        """
        获取告警级别的 emoji

        Args:
            level: 告警级别

        Returns:
            emoji 字符串
        """
        level_map = {
            'low': '🟢 低',
            'medium': '🟡 中',
            'high': '🔴 高'
        }
        return level_map.get(level.lower(), '⚪ 未知')

    def _extract_suggestion(self, analysis: str) -> str:
        """
        从分析结果中提取操作建议

        Args:
            analysis: AI 分析文本

        Returns:
            操作建议文本
        """
        # 简单的关键词匹配
        analysis_lower = analysis.lower()

        if '建议买入' in analysis or '推荐买入' in analysis or '可以考虑买入' in analysis:
            return '📈 考虑买入'
        elif '建议卖出' in analysis or '推荐卖出' in analysis or '可以考虑卖出' in analysis:
            return '📉 考虑卖出'
        elif '持有' in analysis or '继续持有' in analysis:
            return '🤝 继续持有'
        elif '观望' in analysis or '建议观望' in analysis:
            return '👀 观望等待'
        else:
            return '⚡ 根据个人情况决策'
