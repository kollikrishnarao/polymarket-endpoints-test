# CLOB Market and User Channels

These are **separate WebSockets from RTDS** at `wss://ws-subscriptions-clob.polymarket.com`. Use them when you need order book data or your own order updates — RTDS does not give you an order book for the BTC updown markets; you need the CLOB Market Channel.

---

## Market Channel

**Endpoint:** `wss://ws-subscriptions-clob.polymarket.com/ws/market`

### Subscribe

```json
{
  "type": "market",
  "assets_ids": ["<token_id_1>", "<token_id_2>"],
  "custom_feature_enabled": true
}
```

- `assets_ids` is a JSON array of CLOB token IDs.
- `custom_feature_enabled: true` unlocks `best_bid_ask`, `new_market`, and `market_resolved`.
- Public, no auth.

### Envelope

Every message is a flat JSON object with an `event_type` field — no separate `topic` envelope.

### `book`

Sent on first subscribe to a market, and after any trade that changes the book.

```json
{
  "event_type": "book",
  "asset_id": "65818619657568813474341868652308942079804919287380422192892211131408793125422",
  "market": "0xbd31dc8a20211944f6b70f31557f1001557b59905b7738480ca09bd4532f84af",
  "bids": [
    { "price": ".48", "size": "30" },
    { "price": ".49", "size": "20" },
    { "price": ".50", "size": "15" }
  ],
  "asks": [
    { "price": ".52", "size": "25" },
    { "price": ".53", "size": "60" },
    { "price": ".54", "size": "10" }
  ],
  "timestamp": "123456789000",
  "hash": "0x0...."
}
```

| Field | Type | Notes |
| --- | --- | --- |
| `asset_id` | string | CLOB token ID (the "Up" or "Down" leg) |
| `market` | string | Condition ID |
| `bids` | array of `{price, size}` | Best first, descending |
| `asks` | array of `{price, size}` | Best first, ascending |
| `timestamp` | string (ms) | |
| `hash` | string | Order book hash for integrity |

> ⚠ Prices and sizes are **strings**, not numbers. Convert before math: `float(price) * float(size)`.

### `price_change`

Emitted when a new order is placed or cancelled.

```json
{
  "market": "0x5f65177b394277fd294cd75650044e32ba009a95022d88a0c1d565897d72f8f1",
  "price_changes": [
    {
      "asset_id": "71321045679252212594626385532706912750332728571942532289631379312455583992563",
      "price": "0.5",
      "size": "200",
      "side": "BUY",
      "hash": "56621a121a47ed9333273e21c83b660cff37ae50",
      "best_bid": "0.5",
      "best_ask": "1"
    }
  ],
  "timestamp": "1757908892351",
  "event_type": "price_change"
}
```

| Field | Type | Notes |
| --- | --- | --- |
| `market` | string | Condition ID |
| `price_changes` | array | One entry per changed level |
| `price_changes[].asset_id` | string | CLOB token ID |
| `price_changes[].price` | string | |
| `price_changes[].size` | string | `"0"` means level removed from book |
| `price_changes[].side` | string | `"BUY"` or `"SELL"` |
| `price_changes[].hash` | string | Order hash |
| `price_changes[].best_bid` | string | Best bid after this change |
| `price_changes[].best_ask` | string | Best ask after this change |
| `timestamp` | string (ms) | |

### `tick_size_change`

```json
{
  "event_type": "tick_size_change",
  "asset_id": "65818619657568813474341868652308942079804919287380422192892211131408793125422",
  "market": "0xbd31dc8a20211944f6b70f31557f1001557b59905b7738480ca09bd4532f84af",
  "old_tick_size": "0.01",
  "new_tick_size": "0.001",
  "timestamp": "100000000"
}
```

Emitted when a market's tick size flips between `0.01` ↔ `0.001` (happens automatically when the price moves beyond 0.96 or below 0.04).

### `last_trade_price`

```json
{
  "asset_id": "114122071509644379678018727908709560226618148003371446110114509806601493071694",
  "event_type": "last_trade_price",
  "fee_rate_bps": "0",
  "market": "0x6a67b9d828d53862160e470329ffea5246f338ecfffdf2cab45211ec578b0347",
  "price": "0.456",
  "side": "BUY",
  "size": "219.217767",
  "timestamp": "1750428146322"
}
```

| Field | Type | Notes |
| --- | --- | --- |
| `asset_id` | string | |
| `fee_rate_bps` | string | Fee in basis points |
| `market` | string | Condition ID |
| `price` | string | |
| `side` | string | `"BUY"` / `"SELL"` (taker side) |
| `size` | string | |
| `timestamp` | string (**ms**) | |

> ⚠ This is the most useful single event for tracking trade flow on a market: it tells you every print, the side, size, and price.

### `best_bid_ask` (requires `custom_feature_enabled: true`)

```json
{
  "event_type": "best_bid_ask",
  "market": "0x0005c0d312de0be897668695bae9f32b624b4a1ae8b140c49f08447fcc74f442",
  "asset_id": "85354956062430465315924116860125388538595433819574542752031640332592237464430",
  "best_bid": "0.73",
  "best_ask": "0.77",
  "spread": "0.04",
  "timestamp": "1766789469958"
}
```

| Field | Type | Notes |
| --- | --- | --- |
| `market` | string | Condition ID |
| `asset_id` | string | |
| `best_bid` | string | |
| `best_ask` | string | |
| `spread` | string | `best_ask - best_bid` |
| `timestamp` | string (ms) | |

### `new_market` (requires `custom_feature_enabled: true`)

Emitted when a new market is created on the platform.

```json
{
  "id": "1031769",
  "question": "Will NVIDIA (NVDA) close above $240 end of January?",
  "market": "0x311d0c4b6671ab54af4970c06fcf58662516f5168997bdda209ec3db5aa6b0c1",
  "slug": "nvda-above-240-on-january-30-2026",
  "description": "...",
  "assets_ids": ["...","..."],
  "outcomes": ["Yes", "No"],
  "event_message": { "id": "...", "ticker": "...", "slug": "...", "title": "...", "description": "..." },
  "timestamp": "1766790415550",
  "event_type": "new_market",
  "tags": ["stocks"],
  "condition_id": "0x311d0c4b6671ab54af4970c06fcf58662516f5168997bdda209ec3db5aa6b0c1",
  "active": true,
  "clob_token_ids": ["...","..."],
  "sports_market_type": "",
  "line": "",
  "game_start_time": "",
  "order_price_min_tick_size": "0.01",
  "group_item_title": "NVDA above $240",
  "taker_base_fee": "0",
  "fees_enabled": true,
  "fee_schedule": {
    "exponent": "2", "rate": "0.02", "taker_only": true, "rebate_rate": "0"
  }
}
```

### `market_resolved` (requires `custom_feature_enabled: true`)

```json
{
  "id": "1031769",
  "question": "Will NVIDIA (NVDA) close above $240 end of January?",
  "market": "0x311d0c4b6671ab54af4970c06fcf58662516f5168997bdda209ec3db5aa6b0c1",
  "slug": "nvda-above-240-on-january-30-2026",
  "description": "...",
  "assets_ids": ["...","..."],
  "outcomes": ["Yes", "No"],
  "winning_asset_id": "76043073756653678226373981964075571318267289248134717369284518995922789326425",
  "winning_outcome": "Yes",
  "event_message": { ... },
  "timestamp": "1766790415550",
  "event_type": "market_resolved"
}
```

---

## User Channel

**Endpoint:** `wss://ws-subscriptions-clob.polymarket.com/ws/user`

### Subscribe

```json
{
  "auth": {
    "apiKey": "<your-api-key>",
    "secret": "<your-api-secret>",
    "passphrase": "<your-passphrase>"
  },
  "markets": ["0x<condition_id>"],
  "type": "user"
}
```

- L2 API credentials (HMAC-SHA256). Derive with `@polymarket/clob-client-v2` / `py-clob-client-v2` using an L1 EIP-712 wallet signature.
- Filter `markets` to specific condition IDs. Omit to receive updates for all your markets.

### Envelope

Each message has a `type` field at the top level (e.g. `"TRADE"`, `"PLACEMENT"`).

### `trade` (event_type=trade, type=TRADE)

```json
{
  "asset_id": "52114319501245915516055106046884209969926127482827954674443846427813813222426",
  "event_type": "trade",
  "id": "28c4d2eb-bbea-40e7-a9f0-b2fdb56b2c2e",
  "last_update": "1672290701",
  "maker_orders": [
    {
      "asset_id": "52114319501245915516055106046884209969926127482827954674443846427813813222426",
      "matched_amount": "10",
      "order_id": "0xff354cd7ca7539dfa9c28d90943ab577a9a4eac34b9b37a757d7b32bdfb11790b",
      "outcome": "YES",
      "owner": "9180014b-33c8-9240-a14b-bd743ef15f42db2b8c1f3c97a49e8a83d818c3",
      "price": "0.57"
    }
  ],
  "market": "0xbd31dc8a20211944f6b70f31557f1001557b59905b7738480ca09bd4532f84af",
  "matchtime": "1672290701",
  "outcome": "YES",
  "owner": "9180014b-33c8-9240-a14b-bd743ef15f42db2b8c1f3c97a49e8a83d818c3",
  "price": "0.57",
  "side": "BUY",
  "size": "10",
  "status": "MATCHED",
  "taker_order_id": "0x06bc63e346ed4ceddce9efd6b3af37c8f8f440c92fe7da6b2d0f9e4ccbc50c42",
  "timestamp": "1672290701",
  "trade_owner": "9180014b-33c8-9240-a14b-bd743ef15f42db2b8c1f3c97a49e8a83d818c3",
  "type": "TRADE"
}
```

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Trade UUID |
| `asset_id` | string | |
| `market` | string | Condition ID |
| `side` | string | Taker side |
| `price` / `size` | string | |
| `outcome` | string | `"YES"` / `"NO"` / `"Up"` / `"Down"` |
| `maker_orders` | array | Each entry: `{asset_id, matched_amount, order_id, outcome, owner, price}` |
| `taker_order_id` | string | |
| `status` | string | See below |
| `matchtime` / `timestamp` / `last_update` | string (seconds) | All three are seconds-since-epoch |
| `owner` | string | API key owner UUID |
| `trade_owner` | string | Same as owner in most cases |

**Trade status flow:**

```
MATCHED → MINED → CONFIRMED
    ↓        ↑
RETRYING ───┘
    ↓
  FAILED
```

| Status | Terminal | Meaning |
| --- | --- | --- |
| `MATCHED` | no | Operator matched, sent to executor |
| `MINED` | no | On-chain tx observed, no finality yet |
| `CONFIRMED` | yes | Strong finality, trade settled |
| `RETRYING` | no | Reverted/reorged, operator resubmitting |
| `FAILED` | yes | Permanent failure |

### `order` (event_type=order)

```json
{
  "asset_id": "52114319501245915516055106046884209969926127482827954674443846427813813222426",
  "associate_trades": null,
  "event_type": "order",
  "id": "0xff354cd7ca7539dfa9c28d90943ab577a9a4eac34b9b37a757d7b32bdfb11790b",
  "market": "0xbd31dc8a20211944f6b70f31557f1001557b59905b7738480ca09bd4532f84af",
  "order_owner": "9180014b-33c8-9240-a14b-bd743ef15f42db2b8c1f3c97a49e8a83d818c3",
  "original_size": "10",
  "outcome": "YES",
  "owner": "9180014b-33c8-9240-a14b-bd743ef15f42db2b8c1f3c97a49e8a83d818c3",
  "price": "0.57",
  "side": "SELL",
  "size_matched": "0",
  "timestamp": "1672290687",
  "type": "PLACEMENT"
}
```

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Order ID (bytes32 hex) |
| `asset_id` | string | |
| `market` | string | Condition ID |
| `side` | string | |
| `outcome` | string | |
| `price` | string | |
| `original_size` | string | |
| `size_matched` | string | Running matched size |
| `type` | string | `"PLACEMENT"` / `"UPDATE"` / `"CANCELLATION"` |
| `timestamp` | string (seconds) | |
| `owner` / `order_owner` | string | API key UUID |
| `associate_trades` | array or null | Trade IDs that filled this order |
