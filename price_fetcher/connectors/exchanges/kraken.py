import asyncio
import json
import logging
from decimal import Decimal
from typing import Any, Dict

import requests
import websockets

from price_fetcher.connectors.base_connector import ExchangeConnector
from price_fetcher.cache import price_cache

logger = logging.getLogger(__name__)

KRAKEN_ASSET_PAIRS_URL = "https://api.kraken.com/0/public/AssetPairs"


class KrakenConnector(ExchangeConnector):
    NAME = "kraken"
    WS_ENDPOINT = "wss://ws.kraken.com/"
    BATCH_SIZE = 30           # how many pairs to subscribe to in one WS connection


    @staticmethod
    def _normalize_pair(raw: str) -> str:
        """
        Convert Kraken’s raw pair format into BASE_QUOTE, e.g.:
          "XBT/USDT" -> "BTC_USDT"
          "ETH/USD"  -> "ETH_USD"
        Replace leading "XBT" with "BTC" for consistency.
        """
        p = raw.replace("/", "_").upper()
        if p.startswith("XBT_"):
            p = p.replace("XBT", "BTC", 1)
        return p

    async def _connect_and_listen(self) -> None:
        # 1) Fetch all asset pairs from Kraken’s REST API
        try:
            logger.info("Fetching asset pairs from Kraken REST API")
            response = requests.get(KRAKEN_ASSET_PAIRS_URL, timeout=10)
            response.raise_for_status()
        except Exception as e:
            logger.error("Failed to fetch asset pairs: %s", e)
            return

        raw_data = response.json().get("result", {})
        total_pairs = len(raw_data)
        logger.info("Retrieved %d asset pairs from Kraken", total_pairs)

        # 2) Build a map: normalized_name -> original wsname string
        reverse_map: Dict[str, str] = {
            self._normalize_pair(v["wsname"]): v["wsname"]
            for v in raw_data.values()
            if v.get("wsname")
        }
        normalized_count = len(reverse_map)
        logger.info("Built reverse map for %d normalized pairs", normalized_count)

        # 3) Split the full list of wsname values into batches of size BATCH_SIZE
        wsnames = list(reverse_map.values())
        batches = [
            wsnames[i : i + self.BATCH_SIZE]
            for i in range(0, len(wsnames), self.BATCH_SIZE)
        ]
        logger.info("Split into %d batches (batch size: %d)", len(batches), self.BATCH_SIZE)

        # 4) For each batch, start a separate listener task
        tasks = []
        for idx, batch in enumerate(batches, start=1):
            logger.info("Scheduling listener for batch #%d (%d pairs)", idx, len(batch))
            tasks.append(asyncio.create_task(self._listen_batch(batch, idx)))

        # 5) Wait for all batch-listener tasks (they run indefinitely)
        await asyncio.gather(*tasks)

    async def _listen_batch(self, batch: list[str], batch_index: int) -> None:
        """
        For a given batch of wsname strings:
          - Open a WS connection
          - Subscribe to ticker updates for that batch
          - Process incoming messages and update price_cache
          - On ConnectionClosedError or any other exception, wait and reconnect
        """
        subscribe_msg = {
            "event": "subscribe",
            "pair": batch,
            "subscription": {"name": "ticker"},
        }

        while True:
            try:
                ssl_ctx = self._make_ssl_context()
                logger.info("Batch #%d: connecting to WS endpoint", batch_index)
                async with websockets.connect(
                    self.WS_ENDPOINT,
                    ssl=ssl_ctx,
                    ping_interval=20,  # send a ping every 20 seconds
                    ping_timeout=20,   # wait up to 20 seconds for a pong
                ) as ws:
                    logger.info("Batch #%d: WS connection established", batch_index)
                    logger.debug("Batch #%d: subscribing to %d pairs", batch_index, len(batch))
                    await ws.send(json.dumps(subscribe_msg))
                    logger.info("Batch #%d: sent subscribe message", batch_index)

                    async for raw_msg in ws:
                        data: Any = json.loads(raw_msg)

                        # skip subscriptionStatus or heartbeat messages
                        if isinstance(data, dict) and data.get("event") in (
                            "subscriptionStatus",
                            "heartbeat",
                        ):
                            continue

                        # ticker messages come as [chanID, payload, "ticker", "PAIRNAME"]
                        if (
                            isinstance(data, list)
                            and len(data) >= 4
                            and data[2] == "ticker"
                        ):
                            payload = data[1]
                            raw_pair = data[3]  # e.g. "XBT/USDT"
                            bid_str = payload.get("b", ["0"])[0]
                            ask_str = payload.get("a", ["0"])[0]

                            # convert bid/ask to Decimal; skip on error
                            try:
                                bid = Decimal(bid_str)
                                ask = Decimal(ask_str)
                            except (ValueError, ArithmeticError):
                                continue

                            avg_price = (bid + ask) / Decimal("2")
                            normalized = self._normalize_pair(raw_pair)
                            price_cache.update(self.NAME, normalized, avg_price)

            except websockets.exceptions.ConnectionClosedError as e:
                logger.warning(
                    "Batch #%d: connection closed unexpectedly: %s. Reconnecting in %d sec",
                    batch_index,
                    e,
                    self.RESTART_DELAY,
                )
                await asyncio.sleep(self.RESTART_DELAY)
                continue

            except Exception as e:
                logger.error(
                    "Batch #%d: unexpected error in WS listener: %s. Reconnecting in %d sec",
                    batch_index,
                    e,
                    self.RESTART_DELAY,
                )
                await asyncio.sleep(self.RESTART_DELAY)
                continue

            else:
                # Rare case: WS closed without exception
                logger.info(
                    "Batch #%d: WS listener ended cleanly. Reconnecting in %d sec",
                    batch_index,
                    self.RESTART_DELAY,
                )
                await asyncio.sleep(self.RESTART_DELAY)
                continue
