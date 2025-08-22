# price_fetcher/cache.py

from __future__ import annotations
import threading
from copy import deepcopy
from collections import defaultdict
from decimal import Decimal
from typing import Dict, TypeAlias, Optional

# Type aliases for clarity
ExchangeName: TypeAlias = str
PairName:     TypeAlias = str
Price:        TypeAlias = Decimal   # ← now using Decimal instead of float


class PriceCache:
    """
    Thread-safe in-memory cache for the latest average prices:
      {
        'binance': { 'BTC_USDT': Decimal('12345.67'), … },
        'kraken':  { 'BTC_USDT': Decimal('12355.00'), … },
        …
      }
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # defaultdict(dict) automatically creates an empty dict for a new exchange
        self._data: Dict[ExchangeName, Dict[PairName, Price]] = defaultdict(dict)

    def update(self, exchange: ExchangeName, pair: PairName, price: Price) -> None:
        """
        Store or overwrite the Decimal price for (exchange, pair).
        Uses a lock to avoid race conditions during concurrent updates.
        """
        with self._lock:
            self._data[exchange][pair] = price

    def get_all(self) -> Dict[ExchangeName, Dict[PairName, Price]]:
        """
        Return a deep copy of the entire cache (so no external code can mutate the original).
        """
        with self._lock:
            return deepcopy(self._data)

    def get_by_exchange(self, exchange: ExchangeName) -> Dict[PairName, Price]:
        """
        Return a shallow copy of all pairs for the given exchange,
        or an empty dict if that exchange is not present.
        """
        with self._lock:
            return dict(self._data.get(exchange, {}))

    def get_price(self, exchange: ExchangeName, pair: PairName) -> Optional[Price]:
        """
        Return the price for (exchange, pair), or None if not found.
        """
        with self._lock:
            return self._data.get(exchange, {}).get(pair)


# Single global instance of the cache for the entire app
price_cache = PriceCache()
