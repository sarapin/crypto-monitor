import asyncio
from django.conf import settings
from price_fetcher.connectors import SUPPORTED_EXCHANGES


async def all_listeners() -> None:
    """
    Launch safe loops for each enabled exchange connector.
    To include/exclude, update SUPPORTED_EXCHANGES in connectors/__init__.py
    and set settings.EXCHANGES accordingly.
    """
    tasks = []
    for key, ConnectorClass in SUPPORTED_EXCHANGES.items():
        if key in settings.EXCHANGES:
            connector = ConnectorClass()
            tasks.append(connector.safe_loop())

    if not tasks:
        raise RuntimeError("No exchange connectors enabled")

    await asyncio.gather(*tasks)


def start_all() -> None:
    """
    Entry point: run all enabled exchange connectors.
    """
    asyncio.run(all_listeners())
