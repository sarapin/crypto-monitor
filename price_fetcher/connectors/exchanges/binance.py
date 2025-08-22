# price_fetcher/connectors/binance.py

import json
import logging
from decimal import Decimal
import websockets
from typing import Any

from price_fetcher.connectors.base_connector import ExchangeConnector
from price_fetcher.cache import price_cache

logger = logging.getLogger(__name__)


class BinanceConnector(ExchangeConnector):
    NAME: str = "binance"
    WS_ENDPOINT: str = "wss://stream.binance.com:9443/ws/!ticker@arr"

    @staticmethod
    def _normalize_pair(raw: str) -> str:
        """
        Convert a raw Binance symbol (e.g. "BTCUSDT" or "ETHBTC")
        into normalized "BASE_QUOTE" form (e.g. "BTC_USDT" or "ETH_BTC").
        """
        s = raw.upper()
        if s.endswith("USDT"):
            base, quote = s[:-4], s[-4:]
        else:
            base, quote = s[:-3], s[-3:]
        return f"{base}_{quote}"

    async def _connect_and_listen(self) -> None:
        """
        Subscribe to Binance’s “all‐tickers” WebSocket stream.
        Each incoming message is a JSON array of objects:
          { "s": symbol, "b": bid, "a": ask, … }
        For each object, compute average price = (bid + ask) / 2,
        normalize the symbol, and update the shared price cache using Decimal.
        """
        ssl_ctx = self._make_ssl_context()
        try:
            logger.info("Connecting to Binance WS endpoint")
            async with websockets.connect(self.WS_ENDPOINT, ssl=ssl_ctx) as ws:
                logger.info("Connected to Binance WS")
                async for raw_msg in ws:
                    data: Any = json.loads(raw_msg)  # list of ticker objects
                    for item in data:
                        symbol = item.get("s", "")
                        bid_str = item.get("b", "0")
                        ask_str = item.get("a", "0")
                        try:
                            bid = Decimal(bid_str)
                            ask = Decimal(ask_str)
                        except (ValueError, ArithmeticError):
                            # skip invalid numbers without spamming logs
                            continue

                        avg_price = (bid + ask) / Decimal("2")
                        pair = self._normalize_pair(symbol)
                        price_cache.update(self.NAME, pair, avg_price)

        except websockets.exceptions.ConnectionClosedError as e:
            logger.warning("Binance WS connection closed unexpectedly: %s", e)
        except Exception as e:
            logger.error("Unexpected error in Binance WS listener: %s", e)
        else:
            logger.info("Binance WS listener exited cleanly")
