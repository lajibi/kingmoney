"""AI 分析引擎 - DeepSeek 版本"""

import os
from datetime import datetime
from typing import Dict, List, Optional
from openai import OpenAI
from database.models import DatabaseManager
from utils.logger import GaiaLogger


class BrainDeepSeek:
    """盖亚大脑 - DeepSeek AI 分析引擎"""

    def __init__(self, api_key: Optional[str] = None):
        """初始化 AI 大脑"""
        self.logger = GaiaLogger("Brain")
        self.memory = DatabaseManager()

        if api_key:
            self.client = OpenAI(
                api_key=api_key,
                base_url='https://api.deepseek.com'
            )
            self.model_chat = 'deepseek-chat'
            self.model_reasoner = 'deepseek-reasoner'
            self.available = True
            self.logger.info("✅ DeepSeek AI 引擎初始化成功")
        else:
            self.logger.warning("未配置 DeepSeek API，AI 功能将不可用")
            self.available = False

    async def analyze(self, alert: Dict) -> str:
        """分析异常波动"""
        if not self.available:
            return "AI 分析服务不可用"

        try:
            context = self._build_context(alert)
            prompt = f"""你是一位专业的金融分析师。请基于以下信息分析当前的市场波动情况。

{context}

请从以下几个方面进行分析：
1. 波动原因可能是什么？(技术面/基本面/市场情绪)
2. 当前趋势方向和强度
3. 短期和中期走势预判
4. 操作建议 (持有/买入/卖出/观望)
5. 风险提示

要求：分析报告不少于200字，使用专业但易懂的语言，给出明确操作建议。
"""

            response = self.client.chat.completions.create(
                model=self.model_reasoner,
                messages=[{'role': 'user', 'content': prompt}],
                max_tokens=800
            )

            analysis = response.choices[0].message.content
            self.logger.info(f"完成 {alert['symbol']} 的 AI 分析")
            return analysis

        except Exception as e:
            self.logger.error(f"AI 分析失败: {e}")
            return f"AI 分析时发生错误: {str(e)}"

    async def generate_daily_report(self, price_data: Dict[str, Dict]) -> str:
        """生成每日复盘报告"""
        if not self.available:
            return "每日报告生成服务不可用"

        try:
            assets_summary = []
            for symbol, data in price_data.items():
                change_pct = data.get('change_24h', 0) * 100 if isinstance(data.get('change_24h'), float) else data.get('change_24h', 0)
                assets_summary.append(
                    f"{symbol}: {data['price']} (24h: {change_pct:+.2f}%)"
                )

            prompt = f"""请基于以下市场数据，生成今日市场形势预演报告。

报告时间: {datetime.now().strftime('%Y-%m-%d')}
监测资产表现:
{chr(10).join(assets_summary)}

请从以下几个方面生成报告：
1. 今日市场整体表现概述
2. 各资产走势分析
3. 重要关注点和风险提示
4. 明日市场预判
5. 操作策略建议

要求：报告格式清晰，使用 Markdown 格式，内容全面约300-500字，给出明确的市场观点。
"""

            response = self.client.chat.completions.create(
                model=self.model_chat,
                messages=[{'role': 'user', 'content': prompt}],
                max_tokens=1000
            )

            report = response.choices[0].message.content
            self.logger.info("每日报告生成完成")
            return report

        except Exception as e:
            self.logger.error(f"生成每日报告失败: {e}")
            return f"生成每日报告时发生错误: {str(e)}"

    def _build_context(self, alert: Dict) -> str:
        """构建分析上下文"""
        context_parts = [
            f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"资产名称: {alert['name']} ({alert['symbol']})",
            f"当前价格: {alert['current_price']}",
            f"波动幅度: {alert['volatility']:.2%}",
            f"告警级别: {alert['level']}",
        ]
        return "\n".join(context_parts)

    async def quick_sentiment(self, symbol: str) -> str:
        """快速情感分析"""
        if not self.available:
            return "快速分析不可用"
        try:
            response = self.client.chat.completions.create(
                model=self.model_chat,
                messages=[{'role': 'user', 'content': f"{symbol} 当前市场情绪如何？请用简短语言判断。"}],
                max_tokens=100
            )
            return response.choices[0].message.content
        except Exception as e:
            return "分析失败"
