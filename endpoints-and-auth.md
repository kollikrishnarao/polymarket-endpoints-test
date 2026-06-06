# Endpoints & Authentication

Polymarket's real-time + REST surface for market data.

## 1. RTDS (Real-Time Data Socket)

```
wss://ws-live-data.polymarket.com
```

- No connection-level auth — you connect anonymously, then pass auth per-subscription.
- Sends `PING` (plain text) every ~5s to keep the connection alive. Server replies `pong` (plain text, ignored by the official client).
- Auto-reconnect on drop is the default in the official client.
- One envelope format for every message; see `topics-and-schemas.md`.

### Subscribe / Unsubscribe

```json
{
  "action": "subscribe",
  "subscriptions": [
    {
      "topic": "<topic>",
      "type": "<message_type_or_*>",
      "filters": "<optional JSON-encoded filter string>",
      "clob_auth":  { "key": "...", "secret": "...", "passphrase": "..." },
      "gamma_auth": { "address": "0x..." }
    }
  ]
}
```

- `filters` must be a **JSON-encoded string** (not an object). Empty string = no filter (receive everything on that topic).
- `clob_auth` and `gamma_auth` are mutually optional; only some topics need them.
- Unsubscribe uses the same envelope with `action: "unsubscribe"`. You can add/remove subscriptions without disconnecting.

### Per-topic auth requirements

| Topic                     | Type             | Auth required | Notes |
| ------------------------- | ---------------- | ------------- | ----- |
| `crypto_prices`           | `update`         | none          | Binance feed |
| `crypto_prices_chainlink` | `update` / `*`   | none          | Chainlink feed (official resolution source) |
| `equity_prices`           | `update` / `*`   | none          | Pyth feed |
| `activity`                | `trades`         | none          | All-public trade tape; filter by `event_slug` or `market_slug` |
| `activity`                | `orders_matched` | none          | Same filter; payload identical to `trades` |
| `comments`                | `comment_created` / `comment_removed` | none | Filter by `parentEntityID` + `parentEntityType` |
| `comments`                | `reaction_created` / `reaction_removed` | none | Same filter |
| `clob_market`             | `*`              | none          | Filter by array of CLOB token IDs |
| `clob_user`               | `*`              | **`clob_auth`** | Per-user order/trade feed |

## 2. CLOB Market Channel (different WebSocket, NOT RTDS)

```
wss://ws-subscriptions-clob.polymarket.com/ws/market
```

Public. Subscribe with:

```json
{
  "type": "market",
  "assets_ids": ["<token_id_1>", "<token_id_2>"],
  "custom_feature_enabled": true
}
```

- `assets_ids` is a JSON array of CLOB token IDs (the `clobTokenIds` from Gamma). For a 2-outcome market you typically pass both.
- `custom_feature_enabled: true` unlocks `best_bid_ask`, `new_market`, and `market_resolved` events.
- The envelope here is **flat** — each message has an `event_type` field rather than `topic`/`type`. See `clob-channels.md`.

## 3. CLOB User Channel (different WebSocket, NOT RTDS)

```
wss://ws-subscriptions-clob.polymarket.com/ws/user
```

Authenticated. Subscribe with:

```json
{
  "auth": {
    "apiKey": "<polymarket api key>",
    "secret": "<polymarket api secret>",
    "passphrase": "<polymarket api passphrase>"
  },
  "markets": ["0x<condition_id>"],
  "type": "user"
}
```

- L2 API credentials (HMAC-SHA256). Derive once with L1 EIP-712 wallet signature via `@polymarket/clob-client-v2` / `py-clob-client-v2`.
- Different envelope: `type` field names the event (`TRADE`, `PLACEMENT`, `UPDATE`, `CANCELLATION`, `MATCHED`, `MINED`, `CONFIRMED`, `FAILED`, `RETRYING`).
- See `clob-channels.md`.

## 4. Gamma API (REST — for market discovery)

```
https://gamma-api.polymarket.com
```

Public, no auth. Used to resolve a slug → full market + token IDs.

```bash
# Find the current 5m BTC updown market
curl 'https://gamma-api.polymarket.com/events?slug=btc-updown-5m-1780746900'

# Or, more robustly, look up the series and walk events
curl 'https://gamma-api.polymarket.com/series/10684'   # BTC Up or Down 5m
curl 'https://gamma-api.polymarket.com/events?series_id=10684&active=true&closed=false'
```

Other useful endpoints:

- `GET /markets/{id}` — single market by numeric ID
- `GET /events?active=true&closed=false&series_id=10684&limit=20` — list active markets in a series
- `GET /markets?condition_ids=0x...` — by condition ID
- `GET /public-search?q=bitcoin` — text search

## 5. CLOB REST (for one-shot order book snapshot)

```
https://clob.polymarket.com
```

- `GET /book?token_id=...` — current order book snapshot (use this to seed before the WS sends its first `book` event)
- `GET /midpoint?token_id=...` — current midpoint price
- `GET /price?token_id=...&side=buy|sell` — best bid / best ask
- `GET /trades?asset_id=...&limit=...` — recent trades
- `GET /markets/{condition_id}` — full CLOB market info (tick size, fees, etc.)

## 6. Geoblock (optional, for client-side gating)

```
GET https://polymarket.com/api/geoblock
```

Returns `{ blocked, ip, country, region }`. Some countries are blocked from order placement; some are "close-only". Useful before you attempt any trade.

## Error envelope (RTDS-specific)

When the server rejects a subscription, you get a single JSON frame:

```json
{ "body": { "message": "invalid Subscriptions.Subscriptions[0]: embedded message failed validation | caused by: invalid Subscription.Filters: value does not match regex pattern ..." }, "statusCode": 400 }
```

`statusCode` is a number. The connection is **not** closed on a bad subscription — only the bad sub is rejected.
