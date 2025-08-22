# price_fetcher/services.py

from decimal import Decimal
from typing import Dict, Optional
from rest_framework.exceptions import ParseError, NotFound
from price_fetcher.cache import price_cache


def fetch_prices(
    exchange: Optional[str] = None,
    pair: Optional[str] = None
) -> Dict[str, Dict[str, Decimal]]:
    """
    Return a slice of price_cache based on (exchange, pair):
      1) No exchange and no pair → return all prices.
      2) Exchange only           → return all pairs for that exchange.
      3) Pair only               → return that pair across all exchanges.
      4) Both exchange and pair  → return that pair on that exchange.

    Raises:
      - ParseError (400) if the exchange is unknown.
      - NotFound (404) if the pair is missing.
    """
    # 1) No filters → full cache
    if not exchange and not pair:
        return price_cache.get_all()

    # 2) Only exchange → all pairs for that exchange (or 400 if unknown)
    if exchange and not pair:
        data = price_cache.get_by_exchange(exchange)
        if not data:
            raise ParseError(f"Unknown exchange '{exchange}'.")
        return {exchange: data}

    # 3) Only pair → that pair on every exchange that has it (or 404 if none)
    if pair and not exchange:
        all_data = price_cache.get_all()
        result = {
            ex: {pair: pairs_map[pair]}
            for ex, pairs_map in all_data.items()
            if pair in pairs_map
        }
        if not result:
            raise NotFound(f"Pair '{pair}' not found on any exchange.")
        return result

    # 4) Both exchange and pair → that price on that exchange (or 400/404 as needed)
    if exchange and pair:
        data = price_cache.get_by_exchange(exchange)
        if not data:
            raise ParseError(f"Unknown exchange '{exchange}'.")
        price = data.get(pair)
        if price is None:
            raise NotFound(f"Pair '{pair}' not found on {exchange}.")
        return {exchange: {pair: price}}

    # (Technically unreachable)
    raise ParseError("Bad request parameters.")
