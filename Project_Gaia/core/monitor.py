"""
监控与波动检测模块
计算波动率、管理冷却期、触发告警逻辑
"""

import time
from datetime import datetime
from typing import Dict, List, Optional

from database.models import DatabaseManager


class Monitor:
    """智能监控器"""

    def __init__(self, assets: List[Dict], config: Dict):
        """
        初始化监控器

        Args:
            assets: 资产配置列表
            config: 系统配置
        """
        self.assets = {asset['symbol']: asset for asset in assets}
        self.config = config
        self.db = DatabaseManager()

        # 记录上次价格和最后一次告警时间
        self.last_prices = {}
        self.last_alert_time = {}

        # 冷却期配置 (秒)
        self.cooldown_period = config.get('AI_COOLDOWN_PERIOD', 1800)

    def calculate_volatility(self, current_price: float, last_price: float) -> float:
        """
        计算波动率

        Args:
            current_price: 当前价格
            last_price: 上次价格

        Returns:
            波动率 (百分比)
        """
        if last_price == 0:
            return 0.0
        return (current_price - last_price) / last_price

    def check_threshold(self, symbol: str, volatility: float) -> bool:
        """
        检查是否超过阈值

        Args:
            symbol: 资产符号
            volatility: 波动率

        Returns:
            是否超过阈值
        """
        asset = self.assets.get(symbol)
        if not asset:
            return False

        threshold = asset.get('threshold', 0.05)
        return abs(volatility) >= threshold

    def is_in_cooldown(self, symbol: str, volatility: float) -> bool:
        """
        检查是否在冷却期

        Args:
            symbol: 资产符号
            volatility: 当前波动率

        Returns:
            是否在冷却期
        """
        last_alert = self.last_alert_time.get(symbol)
        if not last_alert:
            return False

        # 获取上次告警时的波动率
        last_alert_data = self.db.get_last_alert(symbol)
        if not last_alert_data:
            return False

        last_volatility = last_alert_data.get('volatility', 0)

        # 如果当前波动翻倍，则强制触发
        if abs(volatility) >= abs(last_volatility) * 2:
            return False

        # 检查冷却时间
        elapsed = time.time() - last_alert
        return elapsed < self.cooldown_period

    async def check_volatility(self, price_data: Dict[str, Dict]) -> List[Dict]:
        """
        检查所有资产的波动情况

        Args:
            price_data: 当前价格数据

        Returns:
            触发告警的资产列表
        """
        alerts = []

        for symbol, data in price_data.items():
            try:
                current_price = data['price']
                last_price = self.last_prices.get(symbol, current_price)

                # 计算波动率
                volatility = self.calculate_volatility(current_price, last_price)

                # 检查是否超过阈值
                if self.check_threshold(symbol, volatility):
                    # 检查冷却期
                    if not self.is_in_cooldown(symbol, volatility):
                        # 触发告警
                        alert = {
                            'symbol': symbol,
                            'name': self.assets[symbol]['name'],
                            'current_price': current_price,
                            'last_price': last_price,
                            'volatility': volatility,
                            'timestamp': datetime.now(),
                            'level': self.assets[symbol].get('level', 'medium'),
                            'threshold': self.assets[symbol].get('threshold', 0.05)
                        }

                        alerts.append(alert)

                        # 更新最后告警时间
                        self.last_alert_time[symbol] = time.time()

                        # 保存到数据库
                        self.db.save_price(
                            symbol=symbol,
                            price=current_price,
                            volume=data.get('volume_24h', 0)
                        )

                # 更新上次价格
                self.last_prices[symbol] = current_price

                # 保存价格到数据库 (每次都保存用于历史分析)
                self.db.save_price(
                    symbol=symbol,
                    price=current_price,
                    volume=data.get('volume_24h', 0)
                )

            except Exception as e:
                print(f"监控资产 {symbol} 时出错: {e}")

        return alerts

    def reset_cooldown(self, symbol: str):
        """
        重置某个资产的冷却期

        Args:
            symbol: 资产符号
        """
        if symbol in self.last_alert_time:
            del self.last_alert_time[symbol]
