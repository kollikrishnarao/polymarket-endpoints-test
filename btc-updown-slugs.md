# BTC Up or Down 5m / 15m — slug, market discovery, and all fields

## Slug formula

```python
window_start = (unix_timestamp // duration_seconds) * duration_seconds
slug = f"btc-updown-{timeframe}-{window_start}"
```

| Timeframe | `duration_seconds` | Window | Slug example (UTC 2026-06-06 11:55:38) |
| --- | --- | --- | --- |
| `5m`  | 300 | `[T, T+300)`  | `btc-updown-5m-1780746900`  (closes 11:55:00 → no, this is a *new* window starting at 11:55:00; verified slug for 11:55–11:60) |
| `15m` | 900 | `[T, T+900)`  | `btc-updown-15m-1780746300` (closes 12:00:00) |

> Verified live at 2026-06-06 11:55:38 UTC: the active 5m window is `1780746900` and the active 15m window is `1780746300`.

## Gamma API — full market data for a slug

```
GET https://gamma-api.polymarket.com/events?slug={slug}
```

### Verified response (5m, `btc-updown-5m-1780746600`)

Top-level (`events[]`):

| Field | Value |
| --- | --- |
| `id` | `"561881"` |
| `ticker` | `"btc-updown-5m-1780746600"` |
| `slug` | `"btc-updown-5m-1780746600"` |
| `title` | `"Bitcoin Up or Down - June 6, 7:50AM-7:55AM ET"` |
| `description` | Resolves "Up" if BTC price at end ≥ price at start, else "Down". Resolution source: Chainlink BTC/USD. |
| `resolutionSource` | `"https://data.chain.link/streams/btc-usd"` |
| `startDate` | `"2026-06-05T12:14:09.509577Z"` |
| `creationDate` | `"2026-06-05T12:14:09.509564Z"` |
| `endDate` | `"2026-06-06T11:55:00Z"` (← `window_start + 300`) |
| `image` / `icon` | `https://polymarket-upload.s3.us-east-2.amazonaws.com/BTC+fullsize.png` |
| `active` | `true` |
| `closed` | `false` |
| `archived` | `false` |
| `new` | `false` |
| `featured` | `false` |
| `restricted` | `true` |
| `liquidity` | `7353.7882` |
| `volume` | `17` |
| `openInterest` | `17` |
| `createdAt` | `"2026-06-05T11:57:03.39474Z"` |
| `updatedAt` | `"2026-06-06T11:46:09.22888Z"` |
| `competitive` | `0.9999750006249843` |
| `volume24hr` | `17` |
| `volume1wk` | `17` |
| `volume1mo` | `17` |
| `volume1yr` | `17` |
| `enableOrderBook` | `true` |
| `liquidityClob` | `7353.7882` |
| `negRisk` | `false` |
| `commentCount` | `0` |
| `markets` | `[ <single market object> ]` (single-market event) |
| `series` | `[ {id:"10684", ticker:"btc-up-or-down-5m", slug:"btc-up-or-down-5m", title:"BTC Up or Down 5m", recurrence:"5m", ...} ]` |
| `tags` | Array of `{id, label, slug, ...}` for "Up or Down", "Crypto Prices", "Recurring", "Bitcoin", "5M", "Crypto" |

### Market object (the thing you'll use)

From the 5m example above (`markets[0]`):

| Field | Value |
| --- | --- |
| `id` | `"2443216"` (numeric market ID) |
| `question` | `"Bitcoin Up or Down - June 6, 7:50AM-7:55AM ET"` |
| `conditionId` | `"0x9d27e999c555d8e7cdf06cd6a501e8162ccdd2e623edaad093da759d1c31adf5"` |
| `slug` | `"btc-updown-5m-1780746600"` |
| `resolutionSource` | `"https://data.chain.link/streams/btc-usd"` |
| `endDate` | `"2026-06-06T11:55:00Z"` |
| `liquidity` | `"7520.8608"` (string!) |
| `startDate` | `"2026-06-05T11:57:55.174031Z"` (this is when the market actually started trading; the **window** start is `2026-06-06T11:50:00Z` from `eventStartTime`) |
| `outcomes` | `'["Up", "Down"]'` (stringified JSON) |
| `outcomePrices` | `'["0.755", "0.245"]'` (stringified JSON, in $[0,1]) |
| `volume` | `"17"` |
| `active` | `true` |
| `closed` | `false` |
| `questionID` | `"0x11741e4adbe3c22b7d8c61b795ad743ef15f42db2b8c1f3c97a49e8a83d818c3"` |
| `enableOrderBook` | `true` |
| `orderPriceMinTickSize` | `0.01` |
| `orderMinSize` | `5` |
| `volumeNum` / `liquidityNum` | `17` / `7520.8608` (numeric forms of `volume` / `liquidity`) |
| `endDateIso` / `startDateIso` | `"2026-06-06"` / `"2026-06-05"` |
| `hasReviewedDates` | `true` |
| `volume24hr` … `volume1yr` | numeric, all `17` for this fresh market |
| `clobTokenIds` | `'["67071665839488671370169924316014377405300227564973706709770836468869822866478", "47803269540111157841465055883460329571923227317267950048388577272019549042821"]'` (stringified JSON array — **the asset IDs you need for the CLOB Market Channel**) |
| `volume24hrClob` … `volumeClob` | numeric CLOB-side volume rollups |
| `liquidityClob` | `7520.8608` |
| `makerBaseFee` / `takerBaseFee` | `1000` (bps) |
| `acceptingOrders` | `true` |
| `negRisk` | `false` |
| `ready` / `funded` | `false` / `false` |
| `acceptingOrdersTimestamp` | `"2026-06-05T11:57:07Z"` |
| `cyom` | `false` (Create-Your-Own-Market) |
| `competitive` | `0.9999750006249843` |
| `pagerDutyNotificationEnabled` | `false` |
| `approved` | `true` |
| `rewardsMinSize` | `50` |
| `rewardsMaxSpread` | `4.5` |
| `spread` | `0.01` |
| `bestBid` / `bestAsk` | `0.5` / `0.51` (snapshot at fetch time) |
| `automaticallyActive` | `true` |
| `clearBookOnStart` | `false` |
| `showGmpSeries` / `showGmpOutcome` | `false` / `false` |
| `manualActivation` | `false` |
| `negRiskOther` | `false` |
| `umaResolutionStatuses` | `"[]"` (UMA oracle statuses, empty until resolution) |
| `pendingDeployment` / `deploying` | `false` / `false` |
| `rfqEnabled` | `false` (Request-For-Quote) |
| `eventStartTime` | `"2026-06-06T11:50:00Z"` ← **this is the actual window start for the slug `1780746600`** |
| `holdingRewardsEnabled` | `false` |
| `feesEnabled` | `true` |
| `requiresTranslation` | `false` |
| `makerRebatesFeeShareBps` | `10000` |
| `feeType` | `"crypto_fees_v2"` |
| `feeSchedule` | `{exponent: 1, rate: 0.07, takerOnly: true, rebateRate: 0.2}` |

### 15m example differences (verified `btc-updown-15m-1780746300`)

Same shape, plus a couple of fields the 5m market didn't have (because it has more trading activity):

- `oneHourPriceChange`: `-0.01`
- `lastTradePrice`: `0.5`

> The 15m market has a `recurrence: "15m"` series (id 10192, slug `btc-up-or-down-15m`, created 2025-08-09), while the 5m series is id 10684 (created 2025-11-21). Both are `seriesType: "single"`.

## How to use this in code

```python
import time, requests

def current_btc_updown_slugs():
    now = int(time.time())
    return {
        "5m":  f"btc-updown-5m-{(now // 300) * 300}",
        "15m": f"btc-updown-15m-{(now // 900) * 900}",
    }

def fetch_market(slug):
    r = requests.get("https://gamma-api.polymarket.com/events",
                     params={"slug": slug})
    events = r.json()
    if not events:
        return None
    return events[0]  # event with the single market inside

m = fetch_market(current_btc_updown_slugs()["5m"])
market = m["markets"][0]
condition_id    = market["conditionId"]
clob_token_ids  = json.loads(market["clobTokenIds"])  # ["up_token", "down_token"]
tick_size       = market["orderPriceMinTickSize"]
fee_schedule    = market["feeSchedule"]
# Use clob_token_ids as assets_ids on the CLOB Market Channel for order book + last trade.
# Use condition_id as the filter on the CLOB User Channel (or in the User Channel subscribe).
# Use market["slug"] as the filter on RTDS activity/trades for the public trade tape.
```

## What you get from each channel for a BTC updown market

| Need | Use | Notes |
| --- | --- | --- |
| Discover the current market (token IDs, fee schedule, current prices) | Gamma REST `GET /events?slug=...` | One-shot, public |
| Live BTC price (Binance reference) | RTDS `crypto_prices` filter `{"symbol":"btcusdt"}` | Sub-second updates |
| Live BTC price (Chainlink = official resolution source) | RTDS `crypto_prices_chainlink` filter `{"symbol":"btc/usd"}` | Sub-second updates |
| Public trade tape (trader, side, size, price, tx hash) | RTDS `activity` `type:"trades"` filter `{"market_slug":<slug>}` | One event per fill |
| Order book snapshot + L2 deltas | CLOB Market Channel subscribe with `assets_ids` | Best source for live book |
| Last trade price (just price/side/size, no trader info) | CLOB Market Channel `last_trade_price` event | Cleaner than activity for prints |
| Best bid/ask ticks | CLOB Market Channel `best_bid_ask` event | Need `custom_feature_enabled: true` |
| My own orders and fills | CLOB User Channel with L2 API creds | Per-market filter via `markets` |
| Comments on the event | RTDS `comments` filter `{"parentEntityID":<event_id>,"parentEntityType":"Event"}` | |
