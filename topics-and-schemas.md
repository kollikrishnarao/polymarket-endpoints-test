# RTDS Topics, Types, Filters, and Schemas

All topics share one envelope (verified):

```json
{
  "topic": "string",
  "type": "string",
  "timestamp": 1780746942953,
  "payload": { ... },
  "connection_id": null
}
```

- `topic` — string identifier of the stream.
- `type` — message kind. For live ticks it's `update`. For initial backfill it's `subscribe`.
- `timestamp` — Unix **milliseconds** when the server emitted the message.
- `payload` — event-specific data. Shape depends on `topic` + `type`.
- `connection_id` — TS interface marks this required, but live messages have it `null`. Don't rely on it.

---

## `crypto_prices` — Binance

**Subscription:**
```json
{ "action":"subscribe", "subscriptions":[
  { "topic":"crypto_prices", "type":"update",
    "filters": "{\"symbol\":\"btcusdt\"}" }
]}
```

- **Filter** must be a JSON-encoded string. Accepted shapes (verified by regex from the server's error message):
  - `{"symbol":"btcusdt"}` — single
  - `["btcusdt","ethusdt"]` — array
  - Empty string `""` or omitted = receive **all** symbols.
- **No auth.**

**Symbols supported (Binance, lowercase concatenated):**
`btcusdt`, `ethusdt`, `solusdt`, `xrpusdt`, `dogeusdt` (per docs; `dogeusdt` is in the README filter list but not the docs page symbol table).

**Live tick payload (`type: "update"`):**

| Field | Type | Notes |
| --- | --- | --- |
| `symbol` | string | Echo of the filter symbol, e.g. `btcusdt` |
| `timestamp` | number (ms) | When the price was recorded |
| `value` | number | Price in quote currency (USDT) |

Example (from docs):
```json
{ "topic":"crypto_prices", "type":"update", "timestamp":1753314088421,
  "payload":{ "symbol":"btcusdt", "timestamp":1753314088395, "value":67234.50 } }
```

**Initial backfill payload (`type: "subscribe"`, sent once per subscribed symbol):**

| Field | Type | Notes |
| --- | --- | --- |
| `symbol` | string | Same as filter |
| `data` | array | ~2 minutes of backfill, ~50–120 ticks, 1-second spacing |

Example (verified live):
```json
{ "topic":"crypto_prices", "type":"subscribe", "timestamp":1780746942953,
  "payload":{ "symbol":"btcusdt",
              "data":[
                {"timestamp":1780746823000,"value":60906},
                {"timestamp":1780746824000,"value":60906},
                ... ~120 entries ...
              ] } }
```

---

## `crypto_prices_chainlink` — Chainlink

**Subscription:**
```json
{ "action":"subscribe", "subscriptions":[
  { "topic":"crypto_prices_chainlink", "type":"*",
    "filters": "{\"symbol\":\"btc/usd\"}" }
]}
```

- **No auth.** (The docs tip about getting a "sponsored Chainlink API key" is for the underlying data feed Polymarket uses, not for RTDS access.)
- Use `type: "*"` or `type: "update"`.
- **Filter** must be JSON, e.g. `{"symbol":"btc/usd"}` or `["btc/usd","eth/usd"]`. Empty string = all.

**Symbols supported (Chainlink, slash-separated):**
`btc/usd`, `eth/usd`, `sol/usd`, `xrp/usd`.

**Live tick payload (`type: "update"`):**

| Field | Type | Notes |
| --- | --- | --- |
| `symbol` | string | e.g. `btc/usd` |
| `timestamp` | number (ms) | |
| `value` | number | Full-precision price |

> **This is the price source used to resolve BTC updown markets.** Polymarket's resolution source is the Chainlink BTC/USD data stream: <https://data.chain.link/streams/btc-usd>.

**Initial backfill payload (`type: "subscribe"`):** same shape as Binance, but with `symbol: "btc/usd"`. Verified live: ~57 entries in the last 2 minutes.

> **Note from live probe:** the chainlink backfill is emitted with `topic: "crypto_prices"`, not `crypto_prices_chainlink`. The `symbol` field (`btc/usd` vs `btcusdt`) disambiguates. Live update messages may also come through under `crypto_prices` — verify by `symbol`, not by topic.

---

## `equity_prices` — Pyth (stocks, ETFs, forex, commodities)

**Subscription:**
```json
{ "action":"subscribe", "subscriptions":[
  { "topic":"equity_prices", "type":"*",
    "filters": "{\"symbol\":\"AAPL\"}" }
]}
```

- **No auth.**
- Use `type: "*"` to also receive the initial 2-minute snapshot (`type: "subscribe"`).

**Live tick payload (`type: "update"`):**

| Field | Type | Notes |
| --- | --- | --- |
| `symbol` | string | Always **lowercase** on the wire, even if you filtered with uppercase |
| `value` | number | Float price |
| `full_accuracy_value` | string | Same value at full precision (avoid float loss) |
| `timestamp` | number (ms) | Price measurement time |
| `received_at` | number (ms) | Server ingest time. Only present when non-zero. |
| `is_carried_forward` | boolean | `true` when the underlying market session is closed and this is the last-known price. Only present when `true`. |

**Initial snapshot payload (`type: "subscribe"`):**
```json
{ "topic":"equity_prices", "type":"subscribe", "timestamp":...,
  "payload":{ "symbol":"aapl",
              "data":[
                {"timestamp":1711382280000,"value":198.30},
                {"timestamp":1711382281000,"value":198.32},
                ... ~120 entries ...
              ] } }
```

**Supported symbols:**

| Class | Symbols |
| --- | --- |
| Stocks | `AAPL`, `TSLA`, `MSFT`, `GOOGL`, `AMZN`, `META`, `NVDA`, `NFLX`, `PLTR`, `OPEN`, `RKLB`, `ABNB`, `COIN`, `HOOD` |
| ETFs | `QQQ`, `SPY`, `EWY`, `VXX` |
| Forex | `EURUSD`, `GBPUSD`, `USDCAD`, `USDJPY`, `USDKRW` |
| Metals | `XAUUSD`, `XAGUSD` |
| Commodities | `WTI`, `CC`, `NGD` |

For equity updown markets, Polymarket provides a separate REST helper for the "price-to-beat" reference:
```
GET https://polymarket.com/api/equity/price-to-beat/{slug}
```

---

## `activity` — trades tape

**Subscription:**
```json
{ "action":"subscribe", "subscriptions":[
  { "topic":"activity", "type":"trades",
    "filters": "{\"market_slug\":\"btc-updown-15m-1780746300\"}" }
]}
```

- **No auth.**
- Two types: `trades` and `orders_matched` (they share the same payload schema).
- **Filter** must be JSON, with one of:
  - `{"market_slug": "btc-updown-15m-1780746300"}` — **use this for the BTC updown markets**
  - `{"event_slug": "<event-level slug>"}`
- You can pass both as an array in filters? No — single object. If you need a multi-market fan-out, send multiple subscription entries.

**Payload (per Trade / orders_matched event):**

| Field | Type | Notes |
| --- | --- | --- |
| `asset` | string | ERC1155 token ID of the conditional token that traded |
| `bio` | string | Trader bio (may be empty) |
| `conditionId` | string | CTF condition ID of the market (= the `conditionId` from Gamma) |
| `eventSlug` | string | Slug of the parent event (usually the same as market slug for these single-market events) |
| `icon` | string | URL to market icon image |
| `name` | string | Display name of the trader |
| `outcome` | string | Human-readable outcome — for BTC updown: `"Up"` or `"Down"` |
| `outcomeIndex` | integer | `0` or `1` (matches `clobTokenIds` order) |
| `price` | float | Trade price in $[0, 1] |
| `profileImage` | string | URL to trader profile image (may be empty) |
| `proxyWallet` | string | Trader's Polygon proxy wallet address |
| `pseudonym` | string | Generated anonymous handle |
| `side` | string | `"BUY"` or `"SELL"` |
| `size` | integer | Number of shares |
| `slug` | string | Slug of the market — `btc-updown-15m-1780746300` |
| `timestamp` | integer (seconds? ms?) | **Verified to be Unix seconds** in payload (NOTE: the README documents it ambiguously; check against the CLOB User Channel `last_update` which is also seconds) |
| `title` | string | Title of the event |
| `transactionHash` | string | Polygon tx hash of the trade settlement |

> ⚠ **Timestamp units**: RTDS envelope `timestamp` is **ms**. Activity `payload.timestamp` is **seconds**. The CLOB Market Channel `last_trade_price.timestamp` and the User Channel `trade.timestamp` / `last_update` / `matchtime` are also **seconds**. Watch for this when correlating.

> ⚠ The `ts` / `timestamp` inconsistency between envelope and payload is a footgun. Always check the magnitude — `1.78e12` is ms (now), `1.78e9` is seconds.

---

## `comments` — comment + reaction stream

**Subscription:**
```json
{ "action":"subscribe", "subscriptions":[
  { "topic":"comments", "type":"*",
    "filters": "{\"parentEntityID\":18396,\"parentEntityType\":\"Event\"}" }
]}
```

- **No auth for the standard events.** `gamma_auth` is needed only for *user-specific* comment streams (the docs mention this but don't elaborate).
- **Filter** must be JSON: `{"parentEntityID": <id>, "parentEntityType": "Event" | "Series"}`. Empty = receive all comments site-wide.
- Types: `comment_created`, `comment_removed`, `reaction_created`, `reaction_removed`.

### `comment_created` payload

| Field | Type | Notes |
| --- | --- | --- |
| `body` | string | Comment text |
| `createdAt` | string | ISO 8601 timestamp |
| `id` | string | Unique comment ID (numeric as string) |
| `parentCommentID` | string | Parent comment ID for replies; empty/null for top-level |
| `parentEntityID` | number | Event or Series ID this comment belongs to |
| `parentEntityType` | string | `"Event"` or `"Series"` (the docs page also shows `"Market"` in one example) |
| `profile` | object | See below |
| `reactionCount` | number | Current reactions |
| `replyAddress` | string | Polygon address for replies (can differ from `userAddress`) |
| `reportCount` | number | Current reports |
| `userAddress` | string | Polygon address of the author |

**Profile sub-object:**

| Field | Type | Notes |
| --- | --- | --- |
| `baseAddress` | string | Profile address |
| `displayUsernamePublic` | boolean | |
| `name` | string | Display name |
| `proxyWallet` | string | Proxy wallet address used for trading |
| `pseudonym` | string | Anonymous handle |

The README's `Comment` schema additionally lists `updatedAt` (last update timestamp) — emitted but not documented in the docs page.

### `comment_removed`, `reaction_created`, `reaction_removed`

Same envelope, slimmed-down payloads. The `Reaction` schema (per README):

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Unique reaction ID |
| `commentID` | number | ID of the comment |
| `reactionType` | string | e.g. `like` |
| `icon` | string | Icon URL |
| `userAddress` | string | Reactor's address |
| `createdAt` | string | ISO 8601 |

---

## `clob_market` — market-level CLOB updates (in RTDS)

**Subscription** (per `examples/quick-connection.ts`):
```json
{ "action":"subscribe", "subscriptions":[
  { "topic":"clob_market", "type":"*" }
]}
```

- **No auth.**
- The example shows an array filter:
  `filters: "[\"71321045679252212594626385532706912750332728571942532289631379312455583992563\"]"`
  i.e. an array of CLOB token IDs.
- The README doesn't document this topic. The example in the repo is the only authoritative reference. Payload schema is **not** documented — treat it as opaque and verify against the CLOB Market Channel events in `clob-channels.md`, which use the same data.

> ⚠ Treat `clob_market` (RTDS) as legacy. For the BTC updown markets, prefer the CLOB Market Channel (`/ws/market`) which has full, stable, documented schemas.

---

## `clob_user` — user-level CLOB updates (in RTDS)

**Subscription:**
```json
{ "action":"subscribe", "subscriptions":[
  { "topic":"clob_user", "type":"*",
    "clob_auth": { "key":"...", "secret":"...", "passphrase":"..." } }
]}
```

- **Requires `clob_auth` with the L2 API key, secret, and passphrase** (Polymarket's HMAC-SHA256 credentials).
- The README does not document the message schema for this topic. The CLOB User Channel (`/ws/user`) at `wss://ws-subscriptions-clob.polymarket.com/ws/user` documents the equivalent events (`trade`, `order` with statuses `MATCHED`/`MINED`/`CONFIRMED`/`RETRYING`/`FAILED`/`PLACEMENT`/`UPDATE`/`CANCELLATION`) — same semantics, different envelope.

> ⚠ Prefer the CLOB User Channel over RTDS `clob_user`. It has documented schemas and a stable envelope.
