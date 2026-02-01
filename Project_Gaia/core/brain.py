"""
AI 分析引擎
集成 Gemini API 进行智能研判和研报生成
"""

import os
from datetime import datetime
from typing import Dict, List, Optional

import google.generativeai as genai
from database.models import DatabaseManager
from utils.logger import GaiaLogger


class Brain:
    """盖亚大脑 - AI 分析引擎"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 AI 大脑

        Args:
            api_key: Gemini API 密钥
        """
        self.logger = GaiaLogger("Brain")
        self.memory = DatabaseManager()

        # 配置 Gemini
        if api_key:
            genai.configure(api_key=api_key)
            self.model_flash = genai.GenerativeModel('gemini-3-flash')
            self.model_pro = genai.GenerativeModel('gemini-1.5-pro')
            self.available = True
        else:
            self.logger.warning("未配置 Gemini API，AI 功能将不可用")
            self.available = False

    def _build_context(self, alert: Dict) -> str:
        """
        构建分析上下文

        Args:
            alert: 告警数据

        Returns:
            上下文字符串
        """
        # 获取历史价格数据
        price_history = self.memory.get_price_history(alert['symbol'], hours=24)

        # 获取相似的历史事件
        similar_events = self.memory.get_similar_events(
            alert['symbol'],
            alert['volatility'],
            days=30
        )

        context_parts = [
            f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"资产名称: {alert['name']} ({alert['symbol']})",
            f"当前价格: {alert['current_price']}",
            f"上一次价格: {alert['last_price']}",
            f"波动幅度: {alert['volatility']:.2%}",
            f"波动阈值: {alert['threshold']:.2%}",
            f"告警级别: {alert['level']}",
        ]

        # 添加历史价格分析
        if price_history:
            prices = [p['price'] for p in price_history[:10]]
            high_24h = max(prices)
            low_24h = min(prices)
            context_parts.append(f"\n最近24小时价格区间: {low_24h} - {high_24h}")
            context_parts.append(f"当前价格在24小时区间位置: "
                                f"{((alert['current_price'] - low_24h) / (high_24h - low_24h) * 100):.1f}%")

        # 添加相似事件对比
        if similar_events:
            context_parts.append("\n历史相似波动事件:")
            for i, event in enumerate(similar_events[:3], 1):
                context_parts.append(
                    f"  {i}. {event['timestamp'].strftime('%m-%d %H:%M')} "
                    f"波动{event['volatility']:.2%} - {event['ai_analysis'][:50]}..."
                )

        return "\n".join(context_parts)

    async def analyze(self, alert: Dict) -> str:
        """
        分析异常波动

        Args:
            alert: 告警数据

        Returns:
            分析报告 (不少于200字)
        """
        if not self.available:
            return "AI 分析服务不可用，请配置 Gemini API"

        try:
            # 构建上下文
            context = self._build_context(alert)

            # 构建分析提示词
            prompt = f"""
你是一位专业的金融分析师。请基于以下信息分析当前的市场波动情况，生成一份专业的研报。

{context}

请从以下几个维度进行分析：
1. 波动原因可能是什么？(技术面/基本面/市场情绪)
2. 当前趋势方向和强度
3. 短期和中期走势预判
4. 操作建议 (持有/买入/卖出/观望)
5. 风险提示

要求：
- 分析报告不少于200字
- 使用专业但易懂的语言
- 给出明确操作建议
- 如果有历史相似事件，请进行对比分析
"""

            # 调用 Gemini 1.5 Pro 进行深度分析
            response = await self.model_pro.generate_content_async(prompt)

            analysis = response.text
            self.logger.info(f"完成 {alert['symbol']} 的 AI 分析")

            return analysis

        except Exception as e:
            self.logger.error(f"AI 分析失败: {e}", exc_info=True)
            return f"AI 分析时发生错误: {str(e)}"

    async def generate_daily_report(self, price_data: Dict[str, Dict]) -> str:
        """
        生成每日复盘报告

        Args:
            price_data: 当前价格数据

        Returns:
            每日报告
        """
        if not self.available:
            return "每日报告生成服务不可用"

        try:
            # 汇总所有资产信息
            assets_summary = []
            for symbol, data in price_data.items():
                history = self.memory.get_price_history(symbol, hours=24)
                if history:
                    prev_price = history[0]['price']
                    change = (data['price'] - prev_price) / prev_price * 100
                    assets_summary.append(
                        f"{symbol}: {data['price']} (24h: {change:+.2f}%)"
                    )

            # 构建报告提示词
            prompt = f"""
请基于以下市场数据，生成今日市场形势预演报告。

报告时间: {datetime.now().strftime('%Y-%m-%d')}
监测资产表现:
{chr(10).join(assets_summary)}

请从以下几个方面生成报告：
1. 今日市场整体表现概述
2. 各资产走势分析
3. 重要关注点和风险提示
4. 明日市场预判
5. 操作策略建议

要求：
- 报告格式清晰，使用 Markdown 格式
- 内容全面，约300-500字
- 给出明确的市场观点
"""

            response = await self.model_flash.generate_content_async(prompt)
            report = response.text

            self.logger.info("每日报告生成完成")
            return report

        except Exception as e:
            self.logger.error(f"生成每日报告失败: {e}", exc_info=True)
            return f"生成每日报告时发生错误: {str(e)}"

    async def quick_sentiment(self, symbol: str) -> str:
        """
        快速情感分析 (使用 Gemini Flash)

        Args:
            symbol: 资产符号

        Returns:
            情感分析结果
        """
        if not self.available:
            return "快速分析不可用"

        try:
            # 获取最近的价格变化
            history = self.memory.get_price_history(symbol, hours=1)
            if len(history) < 2:
                return "数据不足"

            latest = history[0]['price']
            prev = history[-1]['price']
            change = (latest - prev) / prev * 100

            prompt = f"""
{symbol} 在过去1小时内价格从 {prev} 变为 {latest}，变动 {change:+.2f}%。

请用简短的语言判断当前市场情绪是：
- 乐观
- 谨慎乐观
- 中性
- 谨慎悲观
- 恐慌

并给出一句简短的理由（不超过50字）。
"""

            response = await self.model_flash.generate_content_async(prompt)
            return response.text

        except Exception as e:
            self.logger.error(f"快速情感分析失败: {e}")
            return "分析失败"
