from .exchanges.binance import BinanceConnector
from .exchanges.kraken import KrakenConnector

# To include or exclude specific exchanges, adjust this mapping:
SUPPORTED_EXCHANGES = {
    "binance": BinanceConnector,
    "kraken":  KrakenConnector,
}
