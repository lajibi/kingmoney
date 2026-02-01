"""
资产配置加载器
"""

import json
from pathlib import Path
from typing import Dict, List


class AssetsLoader:
    """资产配置加载器"""

    def __init__(self, config_path: Path):
        """
        初始化加载器

        Args:
            config_path: assets.json 文件路径
        """
        self.config_path = config_path
        self.assets = self._load_config()

    def _load_config(self) -> List[Dict]:
        """加载资产配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                assets = json.load(f)
            return assets
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {e}")

    def get_enabled_assets(self) -> List[Dict]:
        """
        获取所有启用的资产

        Returns:
            启用的资产列表
        """
        return [asset for asset in self.assets if asset.get('enabled', True)]

    def get_asset_by_symbol(self, symbol: str) -> Dict:
        """
        根据符号获取资产配置

        Args:
            symbol: 资产符号

        Returns:
            资产配置字典
        """
        for asset in self.assets:
            if asset['symbol'] == symbol:
                return asset
        raise KeyError(f"未找到资产: {symbol}")

    def reload(self):
        """重新加载配置"""
        self.assets = self._load_config()
