```markdown
# Crypto Monitor

**Test task for Back-End Developer position**

A lightweight **Django API service** that retrieves real-time crypto prices from multiple exchanges (**Binance, Kraken**) via **WebSockets**.  
No DB. No REST calls at request time. Docker-ready.

---

## Features
- **WebSocket collectors**: subscribe to all pairs from Binance & Kraken.  
- **Normalized pairs**: unify tickers (e.g., `XBT` → `BTC`, `BTC/USDT` → `BTC_USDT`).  
- **Mid-price calculation**: `(bid + ask) / 2`.  
- **In-memory cache** only, no persistence.  
- **Filters**:
  - `exchange` *(optional)* → all pairs from one exchange.
  - `pair` *(optional)* → one pair.
  - No filters → all pairs from all exchanges.

---

## API
```

GET /api/prices/

```

### Query params
- `exchange` → `binance` | `kraken`  
- `pair` → normalized name, e.g. `BTC_USDT`

### Example
```

/api/prices/                     # all pairs from all exchanges
/api/prices/?exchange=binance    # all pairs from Binance
/api/prices/?exchange=kraken\&pair=BTC\_USDT

````

Response sample:
```json
{
  "pair": "BTC_USDT",
  "sources": [
    { "exchange": "binance", "price": 64123.12 },
    { "exchange": "kraken", "price": 64125.44 }
  ],
  "aggregate": { "method": "mean", "price": 64124.28 }
}
````

---

## Run with Docker

```bash
docker build -t crypto-monitor .
docker run -p 8000:8000 crypto-monitor
```

API available at: [http://localhost:8000/api/prices/](http://localhost:8000/api/prices/)

```
```
