# price_fetcher/connectors/base_connector.py

import asyncio
import logging
import ssl
from abc import ABC, abstractmethod

logger = logging.getLogger("price_fetcher.connectors")


class ExchangeConnector(ABC):
    """
    Base class for WebSocket‐based exchange connectors.
    Subclasses must set:
      - NAME: str
      - WS_ENDPOINT: str
    and override:
      - @staticmethod _normalize_pair(raw: str) -> str
      - async def _connect_and_listen(self) -> None
    """

    RESTART_DELAY: int = 5  # seconds to wait before reconnecting after an error

    NAME: str
    WS_ENDPOINT: str

    @staticmethod
    @abstractmethod
    def _normalize_pair(raw: str) -> str:
        """
        Convert a raw symbol from the exchange into normalized "BASE_QUOTE" form.
        Must be overridden by subclasses.
        """
        ...

    @abstractmethod
    async def _connect_and_listen(self) -> None:
        """
        Must be overridden by subclasses:
          - Connect to WebSocket (self.WS_ENDPOINT)
          - Subscribe if needed
          - Iterate incoming messages
          - Parse each message and update cache
        """
        ...

    @staticmethod
    def _make_ssl_context():
        return ssl.create_default_context()

    async def safe_loop(self) -> None:
        """
        Public method: continuously attempt to connect and listen,
        restarting on any exception after RESTART_DELAY seconds.
        """
        while True:
            try:
                logger.info(f"[{self.NAME}] Connecting to {self.WS_ENDPOINT}")
                await self._connect_and_listen()
            except Exception as e:
                logger.exception(
                    f"[{self.NAME}] Error: {e}. Reconnecting in {self.RESTART_DELAY}s"
                )
                await asyncio.sleep(self.RESTART_DELAY)
