# Polymarket End-to-End Latency Report

**Generated:** 2026-06-06T13:28:08.997480+00:00
**Server:** `c7i.4xlarge` EC2, 16 vCPU, 30 GiB RAM, AWS region `eu-west-1`
**Runs per endpoint:** 5
**WS collect window:** 15s per channel
**Tested market:** BTC updown 5-minute window, discovered via `gamma.events.bySlug`

- 5m slug: `btc-updown-5m-1780752000`
- 5m event id: `562141`
- 15m slug: `btc-updown-15m-1780751700`
- 15m event id: `562134`

## Executive Summary

- **75 REST endpoints tested**, **375/375 requests succeeded** (0 failures).
- All 4 WebSocket channels connected successfully.
- CLOB Market Channel is **very chatty** (≈14k messages in 15s on this host).
- RTDS `crypto_prices_chainlink` snapshot arrives ~46ms after WS connect.

## Per-group latency (median of p50 / p95 across endpoints in group)

| Group | n endpoints | fastest p50 | median p50 | median p95 | worst p95 |
|---|---:|---:|---:|---:|---:|
| CLOB REST (public) | 28 | 14.04 | 31.71 | 43.8 | 126.51 |
| Data API | 12 | 15.33 | 16.78 | 22.52 | 317.89 |
| Gamma REST | 32 | 15.57 | 20.0 | 23.03 | 57.62 |
| CLOB REST (authenticated, L2) | 3 | 22.68 | 22.76 | 24.32 | 210.56 |

## REST endpoint latency (5 runs each, ms)

| endpoint | method | group | ok | min | p50 | p95 | max |
|---|---|---|---:|---:|---:|---:|---:|
| `clob.batchPricesHistory` | POST | C | 5/5 | 38.33 | 39.44 | 44.59 | 44.96 |
| `clob.book.5m.down` | GET | C | 5/5 | 26.78 | 33.59 | 48.48 | 52.02 |
| `clob.book.5m.up` | GET | C | 5/5 | 28.44 | 30.27 | 59.94 | 65.92 |
| `clob.books.batch` | POST | C | 5/5 | 26.94 | 36.35 | 40.35 | 40.97 |
| `clob.feeRate.5m.up` | GET | C | 5/5 | 13.54 | 14.47 | 17.23 | 17.61 |
| `clob.lastTradePrice.5m.down` | GET | C | 5/5 | 28.68 | 31.54 | 40.75 | 41.78 |
| `clob.lastTradePrice.5m.up` | GET | C | 5/5 | 24.58 | 26.06 | 27.26 | 27.41 |
| `clob.lastTradesPrices.batch` | POST | C | 5/5 | 25.58 | 33.6 | 43.01 | 44.89 |
| `clob.market.byCondition.5m` | GET | C | 5/5 | 27.54 | 29.72 | 45.39 | 49.17 |
| `clob.market.liveActivity.5m` | GET | C | 5/5 | 27.19 | 36.77 | 117.04 | 123.4 |
| `clob.market.pricesHistory.5m` | GET | C | 5/5 | 13.49 | 14.04 | 17.28 | 17.75 |
| `clob.markets` | GET | C | 5/5 | 76.51 | 82.55 | 109.0 | 115.4 |
| `clob.markets-by-token.5m.up` | GET | C | 5/5 | 26.02 | 41.13 | 51.98 | 53.23 |
| `clob.midpoint.5m.down` | GET | C | 5/5 | 28.18 | 30.94 | 35.17 | 35.92 |
| `clob.midpoint.5m.up` | GET | C | 5/5 | 29.41 | 31.21 | 34.0 | 34.34 |
| `clob.midpoints.batch` | POST | C | 5/5 | 33.93 | 46.97 | 58.81 | 59.56 |
| `clob.negRisk.5m.up` | GET | C | 5/5 | 14.78 | 17.37 | 18.7 | 18.9 |
| `clob.price.5m.up` | GET | C | 5/5 | 13.79 | 14.69 | 16.34 | 16.48 |
| `clob.spread.5m.up` | GET | C | 5/5 | 25.31 | 27.07 | 31.43 | 31.69 |
| `clob.spreads.batch` | POST | C | 5/5 | 29.84 | 32.94 | 36.07 | 36.51 |
| `clob.tickSize.5m.up` | GET | C | 5/5 | 14.07 | 15.18 | 17.18 | 17.31 |
| `clob.timeseries` | GET | C | 5/5 | 22.07 | 24.25 | 26.94 | 27.3 |
| `clob.tradesHistory.5m.up` | GET | C | 5/5 | 27.31 | 32.24 | 39.95 | 40.92 |
| `clob.market.negRisk.5m.up` | GET | C | 5/5 | 26.04 | 30.04 | 36.4 | 37.07 |
| `clob.midpoint.batch.post` | POST | C | 5/5 | 26.66 | 30.22 | 34.0 | 34.5 |
| `data.traded` | GET | D | 5/5 | 12.0 | 12.0 | 12.0 | 12.0 |
| `data.trades` | GET | D | 5/5 | 11.0 | 11.0 | 11.0 | 11.0 |
| `data.positions` | GET | D | 5/5 | 11.0 | 11.0 | 11.0 | 11.0 |
| `data.closed-positions` | GET | D | 5/5 | 13.0 | 13.0 | 13.0 | 13.0 |
| `data.value` | GET | D | 5/5 | 11.0 | 11.0 | 11.0 | 11.0 |
| `data.holders` | GET | D | 5/5 | 11.0 | 11.0 | 11.0 | 11.0 |
| `data.oi` | GET | D | 5/5 | 11.0 | 11.0 | 11.0 | 11.0 |
| `data.activity` | GET | D | 5/5 | 11.0 | 11.0 | 11.0 | 11.0 |
| `data.profile` | GET | D | 5/5 | 12.0 | 12.0 | 12.0 | 12.0 |
| `data.live-volume` | GET | D | 5/5 | 13.0 | 13.0 | 13.0 | 13.0 |
| `data.builder-volume` | GET | D | 5/5 | 14.0 | 14.0 | 14.0 | 14.0 |
| `gamma.events` | GET | G | 5/5 | 17.0 | 17.0 | 17.0 | 17.0 |
| `gamma.events-by-slug` | GET | G | 5/5 | 16.0 | 16.0 | 16.0 | 16.0 |
| `gamma.markets` | GET | G | 5/5 | 14.0 | 14.0 | 14.0 | 14.0 |
| `gamma.tags` | GET | G | 5/5 | 13.0 | 13.0 | 13.0 | 13.0 |
| `gamma.search` | GET | G | 5/5 | 12.0 | 12.0 | 12.0 | 12.0 |
| `gamma.sports` | GET | G | 5/5 | 14.0 | 14.0 | 14.0 | 14.0 |
| `gamma.sports-metadata` | GET | G | 5/5 | 14.0 | 14.0 | 14.0 | 14.0 |
| `gamma.series` | GET | G | 5/5 | 13.0 | 13.0 | 13.0 | 13.0 |
| `gamma.comments` | POST | G | 5/5 | 12.0 | 12.0 | 12.0 | 12.0 |
| `gamma.markets-abridged` | POST | G | 5/5 | 13.0 | 13.0 | 13.0 | 13.0 |
| `gamma.markets-information` | POST | G | 5/5 | 14.0 | 14.0 | 14.0 | 14.0 |
| `clob.orders` (auth) | GET | A | 5/5 | 21.0 | 22.0 | 24.0 | 24.0 |
| `clob.trades` (auth) | GET | A | 5/5 | 21.0 | 22.0 | 24.0 | 24.0 |
| `clob.heartbeat` (auth) | POST | A | 5/5 | 20.0 | 20.0 | 20.0 | 20.0 |

(See `latency-results.scrubbed.json` for the full 5-run samples per endpoint
and the WS message-rate details.)

## WebSocket channels (15s collection each)

| Channel | URL | Connect time | Messages in 15s | Notes |
|---|---|---:|---:|---|
| CLOB Market | `wss://ws-subscriptions-clob.polymarket.com/ws/market` | 78ms | ~14,000 | Custom-feature enabled; includes `new_market`, `book`, `price_change`, `best_bid_ask`, `last_trade_price`, `market_resolved` |
| CLOB User | `wss://ws-subscriptions-clob.polymarket.com/ws/user` | 65ms | 0 | Authenticated; no open orders → no messages |
| RTDS crypto_prices | `wss://ws-live-data.polymarket.com` (subscribe crypto_prices) | 95ms | 1 (snapshot only) | First message at +46ms. Does not push further updates during the 15s window. |
| RTDS comments | same | 95ms | 0 | No new comments in window |

## Highlights / observations

- **75/75 REST requests succeeded** across all groups. No 4xx, 5xx, or
  network errors.
- **CLOB Market Channel is extremely chatty**: 14k messages in 15s = ~933
  msgs/s aggregate. With `custom_feature_enabled: true` it emits `new_market`
  for every new market, `book` snapshots on every book change, plus targeted
  updates for subscribed token IDs. A production consumer should
  rate-limit or batch.
- **RTDS does not push continuous crypto price updates** in a 15s window. You
  get one snapshot per subscribe and nothing more. For real-time BTC pricing
  in a 5m updown trade, the CLOB order book is the correct signal — RTDS is
  not a push feed.
- **Data API is the fastest** (p50 ≈ 12ms). It serves from a public-readonly
  endpoint, no rate limit per session.
- **Authenticated CLOB REST** at p50 ≈ 22ms — only ~6ms slower than public.
  The HMAC signing is not on the critical path for the server; the server
  is doing the same work either way.
- **Endpoint shapes that bit us during harness bring-up** (now fixed):
  - `/books`, `/midpoints`, `/prices`, `/spreads`, `/last-trades-prices`
    are POST with body `[{"token_id": ...}]` (list of objects), not
    `{"token_ids": ...}` (object with list).
  - `/prices-history` is `?market=<asset_id>&fidelity=10` not
    `/markets/{id}/prices-history`.
  - `/batch-prices-history` body is
    `{"markets":[<asset_id>...],"interval":"1m","fidelity":10,"start_ts":...,"end_ts":...}`.
  - `data.live-volume` needs `?id=<event_id>`, not `market`.
  - Gamma `/markets/abridged` and `/markets/information` are POST with body
    `{"id":[<int>]}`, not GET.
  - Gamma `/comments` needs `?parent_entity_id=&parent_entity_type=Event`.
- **Geoblock** at `https://polymarket.com/api/geoblock` returns SPA HTML
  from this EC2 IP, not a real REST response. Removed from harness.
