"""
日志记录器
记录系统运行状态和异常信息
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class GaiaLogger:
    """盖亚系统日志记录器"""

    def __init__(self, name: str):
        """
        初始化日志记录器

        Args:
            name: 记录器名称
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # 避免重复添加 handler
        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self):
        """配置日志处理器"""
        try:
            # 日志目录
            project_root = Path(__file__).parent.parent.parent
            log_dir = project_root / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)

            # 文件处理器 - 详细日志
            log_file = log_dir / f"gaia_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))

            # 控制台处理器 - 只显示重要信息
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            ))

            # 添加处理器
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

        except Exception as e:
            print(f"日志初始化失败: {e}")

    def debug(self, message: str):
        """调试级别日志"""
        self.logger.debug(message)

    def info(self, message: str):
        """信息级别日志"""
        self.logger.info(message)

    def warning(self, message: str):
        """警告级别日志"""
        self.logger.warning(message)

    def error(self, message: str, exc_info: bool = False):
        """错误级别日志"""
        self.logger.error(message, exc_info=exc_info)

    def critical(self, message: str, exc_info: bool = False):
        """严重错误级别日志"""
        self.logger.critical(message, exc_info=exc_info)

    @staticmethod
    def cleanup_old_logs(log_dir: Path, days: int = 7):
        """
        清理旧日志文件

        Args:
            log_dir: 日志目录
            days: 保留最近多少天的日志
        """
        try:
            if not log_dir.exists():
                return

            cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)

            for log_file in log_dir.glob("gaia_*.log"):
                if log_file.stat().st_mtime < cutoff_date:
                    log_file.unlink()
                    print(f"已删除旧日志: {log_file}")

        except Exception as e:
            print(f"清理日志失败: {e}")
