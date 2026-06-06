# Polymarket RTDS Deep Dive — Research Notes

Verified against:

- Official docs: <https://docs.polymarket.com/market-data/websocket/rtds>
- Official TypeScript client: <https://github.com/Polymarket/real-time-data-client> (v1.4.2, main)
  - `src/client.ts` — connection, subscribe, unsubscribe, ping
  - `src/model.ts` — message envelope + auth interfaces
  - `examples/quick-connection.ts` — exhaustive example showing every topic the server actually exposes
- Related channels: CLOB Market Channel (`/ws/market`) and CLOB User Channel (`/ws/user`)
- Live probes run from this machine against the production WebSocket
- Gamma API: `https://gamma-api.polymarket.com` (raw responses saved in `raw-responses/`)

## What's in this folder

| File | Purpose |
| --- | --- |
| `README.md` | This file — top-level index |
| `endpoints-and-auth.md` | Every WebSocket + REST endpoint, full auth reference |
| `topics-and-schemas.md` | Every RTDS topic, type, filter, payload field, with verified examples |
| `clob-channels.md` | The separate CLOB Market and User WebSocket channels (orderbook / my orders) |
| `btc-updown-slugs.md` | Slug computation logic, market discovery, live examples, all Gamma fields |
| `field-reference.md` | One flat table of every field we can read across all surfaces |
| `probe_rtds.py` | Reproducible live probe used to verify the docs |
| `probe-output.txt` | Last probe run output (captured here for the record) |
| `raw-responses/` | Raw JSON from Gamma API for two live BTC updown markets |

## TL;DR

Polymarket exposes **three WebSocket services** relevant to BTC updown markets:

1. **RTDS** — `wss://ws-live-data.polymarket.com`
   - Topics: `activity` (trades, orders_matched), `comments` (4 types), `crypto_prices` (Binance), `crypto_prices_chainlink` (Chainlink), `equity_prices` (Pyth), `clob_market`, `clob_user`
   - Auth: optional per-subscription `gamma_auth` (wallet address) or `clob_auth` (api key/secret/passphrase)
   - Use for: **price feeds** and **trades-by-market-slug**
2. **CLOB Market Channel** — `wss://ws-subscriptions-clob.polymarket.com/ws/market`
   - Subscribe with `assets_ids` (CLOB token IDs)
   - Use for: **order book, price changes, last trade price, market resolved** — the actual orderbook feed for a given BTC updown market
3. **CLOB User Channel** — `wss://ws-subscriptions-clob.polymarket.com/ws/user`
   - Auth: `apiKey` / `secret` / `passphrase` (Polymarket L2 API creds, not the RTDS clob_auth)
   - Use for: **your own orders and fills**

Plus the REST Gamma API for market discovery:
- `GET https://gamma-api.polymarket.com/events?slug=btc-updown-5m-{window_start}` (or 15m)
- Returns full event + market + token IDs + current order book snapshot

## BTC 5m / 15m slug formula (verified live)

```text
window_start = (unix_timestamp // duration_seconds) * duration_seconds
slug          = f"btc-updown-{timeframe}-{window_start}"
```

| Timeframe | duration | Window | Example slug (verified 2026-06-06 11:55 UTC) |
| --- | --- | --- | --- |
| `5m`  | 300 | `[T, T+300)`   | `btc-updown-5m-1780746900` |
| `15m` | 900 | `[T, T+900)`   | `btc-updown-15m-1780746300` |

Slug encodes the **window start** (UTC, wall-clock aligned). The market closes at `window_start + duration`. Polymarket's `title` field shows local ET.

See `btc-updown-slugs.md` for the full breakdown, raw Gamma responses, and how to map a slug → `conditionId` → `clobTokenIds` (the asset IDs you need for the CLOB Market Channel).

## Quick-start subscribe recipes (verified working)

```json
// 1. Live BTC price (Binance)
{ "action": "subscribe", "subscriptions": [
  { "topic": "crypto_prices", "type": "update",
    "filters": "{\"symbol\":\"btcusdt\"}" }
]}

// 2. Live BTC price (Chainlink — the official resolution source for the updown markets)
{ "action": "subscribe", "subscriptions": [
  { "topic": "crypto_prices_chainlink", "type": "*",
    "filters": "{\"symbol\":\"btc/usd\"}" }
]}

// 3. Live trades for the current 15m BTC updown market
{ "action": "subscribe", "subscriptions": [
  { "topic": "activity", "type": "trades",
    "filters": "{\"market_slug\":\"btc-updown-15m-1780746300\"}" }
]}

// 4. Order book for the current 5m BTC updown market (use the CLOB Market Channel)
{ "type": "market",
  "assets_ids": ["67071665839488671370169924316014377405300227564973706709770836468869822866478",
                 "47803269540111157841465055883460329571923227317267950048388577272019549042821"],
  "custom_feature_enabled": true }
```

## Discrepancies caught between docs and reality

These are the gotchas that actually matter when you go to implement:

1. **`crypto_prices` filter is JSON, not CSV.** The docs example shows `filters: "solusdt,btcusdt,ethusdt"`. The server rejects this with:
   > `value does not match regex pattern "[{\[]{1}([,:{}\[\]0-9.\-+Eaeflnr-u \n\r\t]|".*?")+[}\]]{1}"`
   Use `{"symbol":"btcusdt"}` instead. Same for the symbol list — wrap it in JSON.
2. **`crypto_prices_chainlink` snapshot comes back as `topic: "crypto_prices"`.** Both Binance and Chainlink subscription paths emit initial backfills with `topic: "crypto_prices"`. The `payload.symbol` field disambiguates (`btcusdt` vs `btc/usd`). The README's "messages hierarchy" table lists two separate topics, but the actual server behavior appears to merge them under `crypto_prices` for snapshots.
3. **Initial dump shape != update shape.** The docs only show the *update* payload (`{symbol, timestamp, value}`). The *initial dump* (sent once per subscription) uses `type: "subscribe"` with `payload: {symbol, data: [{timestamp, value}, ...]}` — a 2-minute backfill of ~50–120 ticks.
4. **`connection_id` is `null` in actual messages.** The TS model has it as required, but live messages have `connection_id: null`. Don't trust it.
5. **The docs page only documents 3 topics; the actual server exposes 7+.** The docs page (`/market-data/websocket/rtds`) is incomplete. The README's messages-hierarchy table (and the `examples/quick-connection.ts` file in the client repo) reveal the full set, including `activity` (with `trades` and `orders_matched`), `clob_market`, and `clob_user`.
6. **Two distinct auth surfaces for the CLOB.** RTDS uses a `clob_auth` block (key/secret/passphrase) inside each subscription. The CLOB User Channel uses a different envelope (`{"auth":{"apiKey","secret","passphrase"},"markets":[...],"type":"user"}`).

See the individual topic files for the full per-field breakdown.
