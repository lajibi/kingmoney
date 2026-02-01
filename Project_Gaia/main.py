"""
Project Gaia - 盖亚计划
凡人财务自由防御系统

主程序入口 - 负责系统初始化和主循环调度
"""

import asyncio
import json
import os
import sys
from datetime import datetime, time
from pathlib import Path
from typing import Dict, List, Optional

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.assets_loader import AssetsLoader
from core.fetcher import DataFetcher
from core.monitor import Monitor
from core.brain import Brain
from utils.logger import GaiaLogger
from utils.notifier import TelegramNotifier


class GaiaSystem:
    """盖亚系统核心控制器"""

    def __init__(self):
        """初始化系统组件"""
        self.logger = GaiaLogger("GaiaSystem")
        self.logger.info("🌍 盖亚计划启动中...")

        # 加载配置
        self.config = self._load_config()
        self.assets = self._load_assets()

        # 初始化核心组件
        self.fetcher = DataFetcher()
        self.monitor = Monitor(self.assets, self.config)
        self.brain = Brain(self.config.get('GEMINI_API_KEY'))
        self.notifier = TelegramNotifier(
            token=self.config.get('TELEGRAM_BOT_TOKEN'),
            chat_id=self.config.get('TELEGRAM_CHAT_ID'),
            base_url=self.config.get('TELEGRAM_API_BASE_URL')
        )

        # 系统状态
        self.running = True
        self.last_daily_report = None

        self.logger.info(f"✅ 系统初始化完成，监控 {len(self.assets)} 个资产")

    def _load_config(self) -> Dict:
        """加载环境变量配置"""
        from dotenv import load_dotenv

        env_path = PROJECT_ROOT / "config" / ".env"
        load_dotenv(env_path)

        config = {
            'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
            'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN'),
            'TELEGRAM_CHAT_ID': os.getenv('TELEGRAM_CHAT_ID'),
            'MONITOR_INTERVAL': int(os.getenv('MONITOR_INTERVAL', 60)),
            'AI_COOLDOWN_PERIOD': int(os.getenv('AI_COOLDOWN_PERIOD', 1800)),
            'DAILY_REPORT_TIME': os.getenv('DAILY_REPORT_TIME', '22:30'),
            'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO')
        }

        # 验证关键配置
        missing_keys = [k for k, v in config.items() if not v and k in ['GEMINI_API_KEY', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']]
        if missing_keys:
            self.logger.warning(f"⚠️ 缺少配置项: {', '.join(missing_keys)}")

        return config

    def _load_assets(self) -> List[Dict]:
        """加载资产配置"""
        try:
            loader = AssetsLoader(PROJECT_ROOT / "config" / "assets.json")
            assets = loader.get_enabled_assets()
            self.logger.info(f"📊 已加载 {len(assets)} 个监控资产")
            return assets
        except Exception as e:
            self.logger.error(f"❌ 加载资产配置失败: {e}")
            raise

    async def fetch_and_monitor(self):
        """抓取数据并执行监控逻辑"""
        try:
            # 异步抓取所有资产数据
            price_data = await self.fetcher.fetch_all(self.assets)

            # 执行监控分析
            alerts = await self.monitor.check_volatility(price_data)

            # 如果有触发告警，进行 AI 分析
            if alerts:
                self.logger.info(f"🚨 检测到 {len(alerts)} 个异常波动")
                for alert in alerts:
                    await self._handle_alert(alert)

        except Exception as e:
            self.logger.error(f"❌ 监控循环异常: {e}", exc_info=True)

    async def _handle_alert(self, alert: Dict):
        """处理告警事件"""
        try:
            asset_symbol = alert['symbol']
            current_price = alert['current_price']
            volatility = alert['volatility']

            self.logger.info(f"🔔 处理告警: {asset_symbol} 波动 {volatility:.2%}")

            # 调用 AI 分析
            analysis = await self.brain.analyze(alert)

            # 发送通知
            await self.notifier.send_alert(alert, analysis)

            # 记录事件
            self.brain.memory.log_event(alert, analysis)

        except Exception as e:
            self.logger.error(f"❌ 处理告警失败: {e}", exc_info=True)

    async def generate_daily_report(self):
        """生成每日复盘报告"""
        try:
            now = datetime.now()
            report_time = datetime.strptime(self.config['DAILY_REPORT_TIME'], "%H:%M").time()

            # 检查是否到了报告时间且今天还没发送过
            if now.time() >= report_time and (self.last_daily_report is None or
                                              self.last_daily_report.date() != now.date()):

                self.logger.info("📋 生成每日复盘报告...")

                # 获取所有资产的历史数据
                price_data = await self.fetcher.fetch_all(self.assets)

                # 生成报告
                report = await self.brain.generate_daily_report(price_data)

                # 发送报告
                await self.notifier.send_daily_report(report)

                self.last_daily_report = now
                self.logger.info("✅ 每日复盘报告已发送")

        except Exception as e:
            self.logger.error(f"❌ 生成每日报告失败: {e}", exc_info=True)

    async def main_loop(self):
        """主循环 - 持续监控和调度"""
        self.logger.info("🔄 主循环启动")

        try:
            while self.running:
                # 执行监控
                await self.fetch_and_monitor()

                # 检查是否需要生成每日报告
                await self.generate_daily_report()

                # 等待下一个轮询周期
                interval = self.config.get('MONITOR_INTERVAL', 60)
                await asyncio.sleep(interval)

        except KeyboardInterrupt:
            self.logger.info("⌨️ 收到中断信号，系统正在关闭...")
        except Exception as e:
            self.logger.error(f"❌ 主循环异常: {e}", exc_info=True)
        finally:
            self.logger.info("👋 盖亚系统已停止")

    async def run(self):
        """运行系统"""
        try:
            await self.main_loop()
        except Exception as e:
            self.logger.critical(f"💥 系统崩溃: {e}", exc_info=True)
            raise


async def main():
    """程序入口"""
    try:
        system = GaiaSystem()
        await system.run()
    except Exception as e:
        print(f"系统启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
