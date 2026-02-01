"""
数据库模型和管理
使用 SQLite 存储价格历史和事件日志
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from utils.logger import GaiaLogger


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: Optional[Path] = None):
        """
        初始化数据库

        Args:
            db_path: 数据库文件路径，默认为 database/gaia_main.db
        """
        if db_path is None:
            # 默认路径
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / "database" / "gaia_main.db"

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.logger = GaiaLogger("Database")
        self._init_db()

    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # 支持字典式访问
        return conn

    def _init_db(self):
        """初始化数据库表结构"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 创建价格历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    price REAL NOT NULL,
                    volume REAL,
                    timestamp DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 创建事件日志表 (存储 AI 分析结果)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS event_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    price REAL NOT NULL,
                    volatility REAL NOT NULL,
                    alert_level TEXT,
                    ai_analysis TEXT,
                    news_summary TEXT,
                    timestamp DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 创建索引优化查询性能
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_price_symbol_time
                ON price_history(symbol, timestamp DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_event_symbol_time
                ON event_log(symbol, timestamp DESC)
            """)

            conn.commit()

    def save_price(self, symbol: str, price: float, volume: float = 0):
        """
        保存价格数据

        Args:
            symbol: 资产符号
            price: 当前价格
            volume: 交易量
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO price_history (symbol, price, volume, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (symbol, price, volume, datetime.now()))
                conn.commit()
        except Exception as e:
            self.logger.error(f"保存价格数据失败: {e}")

    def save_event(self, event: Dict, analysis: str, news_summary: str = ""):
        """
        保存事件日志

        Args:
            event: 事件数据
            analysis: AI 分析结果
            news_summary: 新闻摘要
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO event_log
                    (symbol, price, volatility, alert_level, ai_analysis, news_summary, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    event['symbol'],
                    event['current_price'],
                    event['volatility'],
                    event.get('level', 'medium'),
                    analysis,
                    news_summary,
                    event['timestamp']
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"保存事件日志失败: {e}")

    def get_price_history(self, symbol: str, hours: int = 24) -> List[Dict]:
        """
        获取价格历史

        Args:
            symbol: 资产符号
            hours: 获取最近几小时的数据

        Returns:
            价格历史列表
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM price_history
                    WHERE symbol = ? AND timestamp >= datetime('now', '-{} hours')
                    ORDER BY timestamp DESC
                """.format(hours), (symbol,))

                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"获取价格历史失败: {e}")
            return []

    def get_last_alert(self, symbol: str) -> Optional[Dict]:
        """
        获取某资产最后的告警记录

        Args:
            symbol: 资产符号

        Returns:
            告警数据
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM event_log
                    WHERE symbol = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, (symbol,))

                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            self.logger.error(f"获取最后告警失败: {e}")
            return None

    def get_similar_events(self, symbol: str, volatility: float, days: int = 30) -> List[Dict]:
        """
        查找相似的历史事件 (波动率相近)

        Args:
            symbol: 资产符号
            volatility: 当前波动率
            days: 查找最近多少天

        Returns:
            相似事件列表
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM event_log
                    WHERE symbol = ?
                      AND abs(volatility) >= ?
                      AND timestamp >= datetime('now', '-{} days')
                    ORDER BY timestamp DESC
                    LIMIT 5
                """.format(days), (symbol, abs(volatility) * 0.8))

                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"查找相似事件失败: {e}")
            return []

    def cleanup_old_data(self, days: int = 90):
        """
        清理旧数据

        Args:
            days: 保留最近多少天的数据
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM price_history
                    WHERE timestamp < datetime('now', '-{} days')
                """.format(days))

                cursor.execute("""
                    DELETE FROM event_log
                    WHERE timestamp < datetime('now', '-{} days')
                """.format(days))

                conn.commit()
                self.logger.info(f"已清理 {days} 天前的旧数据")
        except Exception as e:
            self.logger.error(f"清理旧数据失败: {e}")
