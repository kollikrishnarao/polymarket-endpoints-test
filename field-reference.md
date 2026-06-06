# Field Reference — every field we can read

Flat list of every field across the three Polymarket WebSocket channels + the Gamma REST API. All times are Unix epoch unless otherwise noted; **watch the units** (ms vs seconds — see notes column).

## RTDS envelope (every message)

| Field | Type | Units | Notes |
| --- | --- | --- | --- |
| `topic` | string | — | One of: `crypto_prices`, `crypto_prices_chainlink`, `equity_prices`, `activity`, `comments`, `clob_market`, `clob_user` |
| `type` | string | — | `update` (live tick), `subscribe` (initial backfill), or event name (`comment_created`, `reaction_created`, `trades`, `orders_matched`, etc.) |
| `timestamp` | number | **ms** | Server emit time |
| `payload` | object | — | Per-topic shape |
| `connection_id` | string? | — | TS interface says required, server sends `null` |

## RTDS payload — `crypto_prices` and `crypto_prices_chainlink`

| Field | Type | Where | Notes |
| --- | --- | --- | --- |
| `symbol` | string | both | Binance: `btcusdt`. Chainlink: `btc/usd` |
| `timestamp` | number | live update | **ms** |
| `value` | number | live update | Price in quote currency |
| `symbol` | string | initial backfill | same |
| `data` | array | initial backfill | `[{timestamp(ms), value}]`, 1-second spacing, ~2 min |

## RTDS payload — `equity_prices`

| Field | Type | Where | Notes |
| --- | --- | --- | --- |
| `symbol` | string | both | Always lowercase on the wire |
| `value` | number | live update | Float price |
| `full_accuracy_value` | string | live update | Full-precision price (avoid float loss) |
| `timestamp` | number (ms) | live update | |
| `received_at` | number (ms) | live update | Only present when non-zero |
| `is_carried_forward` | boolean | live update | Only present when `true` (market closed, value is last-known) |
| `data` | array | initial backfill | `[{timestamp(ms), value}]` |

## RTDS payload — `activity` (trades / orders_matched)

| Field | Type | Notes |
| --- | --- | --- |
| `asset` | string | ERC1155 token ID |
| `bio` | string | Trader bio (may be empty) |
| `conditionId` | string | CTF condition ID |
| `eventSlug` | string | Event slug |
| `icon` | string | Market icon URL |
| `name` | string | Trader display name |
| `outcome` | string | `"Up"` / `"Down"` for the BTC updown markets |
| `outcomeIndex` | integer | `0` or `1` |
| `price` | float | $[0, 1] |
| `profileImage` | string | URL or empty |
| `proxyWallet` | string | Polygon address |
| `pseudonym` | string | Anonymous handle |
| `side` | string | `"BUY"` / `"SELL"` |
| `size` | integer | Shares |
| `slug` | string | Market slug |
| `timestamp` | integer | **seconds** (⚠ different from envelope `timestamp`) |
| `title` | string | Event title |
| `transactionHash` | string | Polygon tx hash |

## RTDS payload — `comments`

| Field | Type | Notes |
| --- | --- | --- |
| `body` | string | Comment text |
| `createdAt` | string | ISO 8601 |
| `id` | string | Comment ID |
| `parentCommentID` | string | Parent comment ID; empty/null for top-level |
| `parentEntityID` | number | Event or Series ID |
| `parentEntityType` | string | `"Event"` / `"Series"` / `"Market"` |
| `profile.baseAddress` | string | |
| `profile.displayUsernamePublic` | boolean | |
| `profile.name` | string | |
| `profile.proxyWallet` | string | |
| `profile.pseudonym` | string | |
| `reactionCount` | number | |
| `replyAddress` | string | Polygon address for replies |
| `reportCount` | number | |
| `userAddress` | string | Polygon address of author |
| `updatedAt` | string (in README schema) | ISO 8601 |

Reactions: `id`, `commentID` (number), `reactionType`, `icon`, `userAddress`, `createdAt`.

## CLOB Market Channel — all event types

Envelope is flat. `timestamp` is **ms** as a **string**.

| event_type | Fields |
| --- | --- |
| `book` | `asset_id`, `market` (conditionId), `bids[]:{price,size}`, `asks[]:{price,size}`, `timestamp`, `hash` |
| `price_change` | `market`, `price_changes[]:{asset_id, price, size, side, hash, best_bid, best_ask}`, `timestamp` |
| `tick_size_change` | `asset_id`, `market`, `old_tick_size`, `new_tick_size`, `timestamp` |
| `last_trade_price` | `asset_id`, `fee_rate_bps`, `market`, `price`, `side`, `size`, `timestamp` |
| `best_bid_ask` (custom_feature) | `market`, `asset_id`, `best_bid`, `best_ask`, `spread`, `timestamp` |
| `new_market` (custom_feature) | `id`, `question`, `market`, `slug`, `description`, `assets_ids[]`, `outcomes[]`, `event_message{...}`, `timestamp`, `tags[]`, `condition_id`, `active`, `clob_token_ids[]`, `sports_market_type`, `line`, `game_start_time`, `order_price_min_tick_size`, `group_item_title`, `taker_base_fee`, `fees_enabled`, `fee_schedule{exponent, rate, taker_only, rebate_rate}` |
| `market_resolved` (custom_feature) | same as `new_market` plus `winning_asset_id`, `winning_outcome` |

> All numeric price/size fields are **strings**.

## CLOB User Channel — all event types

Envelope is flat. All timestamps are **seconds** as **strings**.

| type | Fields |
| --- | --- |
| `TRADE` (event_type=trade) | `id`, `asset_id`, `market`, `side`, `price`, `size`, `outcome`, `maker_orders[]:{asset_id, matched_amount, order_id, outcome, owner, price}`, `taker_order_id`, `status` (`MATCHED`/`MINED`/`CONFIRMED`/`RETRYING`/`FAILED`), `matchtime`, `timestamp`, `last_update`, `owner`, `trade_owner` |
| `PLACEMENT` / `UPDATE` / `CANCELLATION` (event_type=order) | `id`, `asset_id`, `market`, `side`, `outcome`, `price`, `original_size`, `size_matched`, `timestamp`, `owner`, `order_owner`, `associate_trades` (array or null) |

## Gamma REST `GET /events?slug=...` — event level

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Event ID |
| `ticker` | string | Same as slug for these markets |
| `slug` | string | The query slug |
| `title` | string | Local-time formatted |
| `description` | string | Resolution logic |
| `resolutionSource` | string | Chainlink URL for crypto markets |
| `startDate` | string | ISO 8601 |
| `creationDate` | string | ISO 8601 |
| `endDate` | string | ISO 8601 = `window_start + duration` |
| `image` / `icon` | string | URL |
| `active` | boolean | |
| `closed` | boolean | |
| `archived` | boolean | |
| `new` / `featured` | boolean | |
| `restricted` | boolean | True for crypto updown markets |
| `liquidity` | number | USDC |
| `volume` | number | USDC |
| `openInterest` | number | USDC |
| `createdAt` / `updatedAt` | string | ISO 8601 |
| `competitive` | number | |
| `volume24hr` / `volume1wk` / `volume1mo` / `volume1yr` | number | USDC |
| `enableOrderBook` | boolean | |
| `liquidityClob` | number | |
| `negRisk` | boolean | |
| `commentCount` | number | |
| `markets[]` | array | The single market (these are single-market events) |
| `series[]` | array | `{id, ticker, slug, title, seriesType, recurrence, active, ...}` |
| `tags[]` | array | `{id, label, slug, ...}` |

## Gamma REST `events[].markets[]` — market level

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Market ID |
| `question` | string | Same as event title |
| `conditionId` | string | **The key for CLOB lookups** |
| `slug` | string | |
| `resolutionSource` | string | |
| `endDate` | string | ISO 8601 |
| `liquidity` | string | ⚠ string! |
| `startDate` | string | ISO 8601 — when first traded |
| `image` / `icon` | string | |
| `description` | string | |
| `outcomes` | string | Stringified JSON: `'["Up", "Down"]'` |
| `outcomePrices` | string | Stringified JSON: `'["0.755", "0.245"]'` |
| `volume` | string | ⚠ string |
| `active` / `closed` / `new` / `featured` / `archived` / `restricted` | boolean | |
| `marketMakerAddress` | string | Empty for these |
| `createdAt` / `updatedAt` | string | ISO 8601 |
| `groupItemThreshold` | string | `"0"` |
| `questionID` | string | 0x... |
| `enableOrderBook` | boolean | |
| `orderPriceMinTickSize` | number | `0.01` for these |
| `orderMinSize` | number | `5` |
| `volumeNum` / `liquidityNum` | number | Numeric forms |
| `endDateIso` / `startDateIso` | string | Date only |
| `hasReviewedDates` | boolean | |
| `volume24hr` / `volume1wk` / `volume1mo` / `volume1yr` | number | |
| `clobTokenIds` | string | Stringified JSON: `'["...","..."]'` — **the asset IDs for the CLOB Market Channel** |
| `volume24hrClob` / `volume1wkClob` / `volume1moClob` / `volume1yrClob` / `volumeClob` / `liquidityClob` | number | CLOB-side rollups |
| `makerBaseFee` / `takerBaseFee` | number | bps |
| `acceptingOrders` | boolean | |
| `negRisk` | boolean | |
| `ready` / `funded` | boolean | |
| `acceptingOrdersTimestamp` | string | ISO 8601 |
| `cyom` | boolean | Create-Your-Own-Market |
| `competitive` | number | |
| `pagerDutyNotificationEnabled` | boolean | |
| `approved` | boolean | |
| `rewardsMinSize` | number | |
| `rewardsMaxSpread` | number | |
| `spread` | number | |
| `bestBid` / `bestAsk` | number | Snapshot at fetch time |
| `oneHourPriceChange` | number | Only on older markets |
| `lastTradePrice` | number | Only on older markets |
| `automaticallyActive` | boolean | |
| `clearBookOnStart` | boolean | |
| `showGmpSeries` / `showGmpOutcome` | boolean | GMP = group market placeholder |
| `manualActivation` | boolean | |
| `negRiskOther` | boolean | |
| `umaResolutionStatuses` | string | Stringified JSON array |
| `pendingDeployment` / `deploying` | boolean | |
| `rfqEnabled` | boolean | |
| `eventStartTime` | string | ISO 8601 = **the actual window start** (the slug's epoch in human form) |
| `holdingRewardsEnabled` | boolean | |
| `feesEnabled` | boolean | |
| `requiresTranslation` | boolean | |
| `makerRebatesFeeShareBps` | number | |
| `feeType` | string | `"crypto_fees_v2"` for these |
| `feeSchedule` | object | `{exponent, rate, taker_only, rebate_rate}` — see below |
| `feeSchedule.exponent` | number | |
| `feeSchedule.rate` | number | e.g. `0.07` |
| `feeSchedule.takerOnly` | boolean | |
| `feeSchedule.rebateRate` | number | e.g. `0.2` |
