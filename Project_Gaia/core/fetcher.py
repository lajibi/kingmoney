"""
数据抓取引擎
支持 ccxt (加密货币) 和 yfinance (股票/商品) 异步抓取
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional

import ccxt.async_support as ccxt
import yfinance as yf


class DataFetcher:
    """多源数据抓取引擎"""

    def __init__(self):
        """初始化抓取器"""
        self.exchanges = {}
        self._init_exchanges()

    def _init_exchanges(self):
        """初始化交易所实例"""
        # 支持的主流交易所
        supported_exchanges = [
            'binance', 'okx', 'bybit', 'huobi', 'kucoin',
            'coinbase', 'kraken', 'gate', 'mexc'
        ]

        for exchange_name in supported_exchanges:
            try:
                # 创建异步交易所实例
                exchange_class = getattr(ccxt, exchange_name)
                self.exchanges[exchange_name] = exchange_class({
                    'enableRateLimit': True,  # 启用速率限制
                    'options': {
                        'defaultType': 'spot',  # 现货交易
                    }
                })
            except Exception as e:
                pass

    async def fetch_crypto_price(self, exchange_name: str, symbol: str) -> Optional[Dict]:
        """
        抓取加密货币价格

        Args:
            exchange_name: 交易所名称
            symbol: 交易对符号 (如 BTC/USDT)

        Returns:
            价格数据字典
        """
        try:
            exchange = self.exchanges.get(exchange_name)
            if not exchange:
                raise ValueError(f"不支持的交易所: {exchange_name}")

            # 获取当前行情
            ticker = await exchange.fetch_ticker(symbol)

            # CCXT 的 change 是绝对价格变化,percentage 才是百分比
            current_price = float(ticker['last'])
            change_percentage = float(ticker.get('percentage', 0))

            return {
                'symbol': symbol,
                'price': current_price,
                'change_24h': change_percentage,
                'high_24h': float(ticker['high']),
                'low_24h': float(ticker['low']),
                'volume_24h': float(ticker['baseVolume']),
                'timestamp': datetime.now(),
                'source': exchange_name
            }

        except Exception as e:
            print(f"抓取加密货币价格失败 {exchange_name} {symbol}: {e}")
            return None

    def fetch_traditional_price(self, symbol: str) -> Optional[Dict]:
        """
        抓取传统金融资产价格 (股票、商品等)

        Args:
            symbol: 资产符号 (如 GC=F, ^GSPC)

        Returns:
            价格数据字典
        """
        try:
            # 同步抓取 (yfinance 不支持异步)
            # 获取2天数据以计算相对于前一日的涨跌幅
            ticker = yf.Ticker(symbol)
            info = ticker.history(period="2d")

            if info.empty or len(info) < 1:
                raise ValueError(f"无法获取数据: {symbol}")

            latest = info.iloc[-1]

            # 计算涨跌幅: 如果有前一日数据,使用前一日收盘价;否则使用当日开盘价
            if len(info) >= 2:
                prev_close = info.iloc[-2]['Close']
                change_24h = (latest['Close'] - prev_close) / prev_close if prev_close != 0 else 0
            else:
                # 如果只有1天数据,使用开盘价计算当日涨跌
                change_24h = (latest['Close'] - latest['Open']) / latest['Open'] if latest['Open'] != 0 else 0

            return {
                'symbol': symbol,
                'price': float(latest['Close']),
                'change_24h': float(change_24h),
                'high_24h': float(latest['High']),
                'low_24h': float(latest['Low']),
                'volume_24h': float(latest['Volume']) if 'Volume' in latest else 0,
                'timestamp': datetime.now(),
                'source': 'yfinance'
            }

        except Exception as e:
            print(f"抓取传统资产价格失败 {symbol}: {e}")
            return None

    async def fetch_asset(self, asset: Dict) -> Optional[Dict]:
        """
        根据资产配置抓取数据

        Args:
            asset: 资产配置字典

        Returns:
            价格数据字典
        """
        source = asset.get('source', '').lower()
        symbol = asset['symbol']

        if source in self.exchanges:
            # 加密货币 - 异步抓取
            return await self.fetch_crypto_price(source, symbol)
        elif source == 'yfinance':
            # 传统资产 - 在线程池中同步执行
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                self.fetch_traditional_price,
                symbol
            )
        else:
            raise ValueError(f"不支持的数据源: {source}")

    async def fetch_all(self, assets: List[Dict]) -> Dict[str, Dict]:
        """
        并发抓取所有资产数据

        Args:
            assets: 资产配置列表

        Returns:
            符号到价格数据的映射
        """
        # 创建所有抓取任务
        tasks = [self.fetch_asset(asset) for asset in assets]

        # 并发执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 组织结果
        price_data = {}
        for asset, result in zip(assets, results):
            if isinstance(result, Exception):
                print(f"抓取失败 {asset['symbol']}: {result}")
                continue
            if result:
                price_data[result['symbol']] = result

        return price_data

    async def close(self):
        """关闭所有交易所连接"""
        for exchange in self.exchanges.values():
            await exchange.close()
