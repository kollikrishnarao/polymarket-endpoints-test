# Live Trade Results

Four real orders were placed against the production Polymarket CLOB during
this session. All four happened on the BTC updown 5m market
`btc-updown-5m-1780756800` ("Bitcoin Up or Down — June 6, 10:40AM–10:45AM ET"),
which resolves at 2026-06-06T14:45:00Z.

The market's CLF (CTF) identifier is `0x50ed161538e8e144e7a9841c1d1235e3a18fed072fb19f59d90651e001251c1b`.

The account (proxy wallet, redacted in this repo) funded the trades with **6.00
pUSD** (the new V2 native collateral). At the time, pUSD contract allowance
to the V2 CTF Exchange was already maxed, so the orders could be placed
without a separate approval transaction.

## Trade ledger

| # | When (UTC) | Side | Token | Shares | Price (eff) | Notional | Order type | Result | Tx hash |
|---|---|---|---|---:|---:|---:|---|---|---|
| 1 | 14:41:51 | BUY | DOWN | 9.482757 | $0.58 | -5.50 pUSD | FAK | matched, filled | `0x1ad3…62b0e1` (block 88034617) |
| 2 | 14:42:39 | SELL | DOWN | 9.38 | $0.99 limit | +9.29 pUSD (target) | GTC | live (resting on book) | not filled |
| 3 | 14:43:24 | SELL | DOWN | 9.48 | $0.77 | +7.30 pUSD | (manual via web UI) | matched, filled | `0x1c9c…0c19987` (block 88034679) |
| 4 | 14:48:42 | BUY | DOWN | 1.449274 | $0.69 | -1.00 pUSD | FAK | matched, filled | `0x8179…0d029dd` (block 88034891) |

Trades 1 and 2 were placed by the `@polymarket/client` V2 canary client from
this machine. Trade 3 was placed by the user manually through the Polymarket
web UI (the user's UI override cancelled our GTC at 0.99 and sold at the
prevailing 0.77 bid). Trade 4 was a follow-up latency probe order placed from
this machine to measure the clean V2 POST round-trip with the script's clock
instrumented.

## P&L

| Item | Amount |
|---|---:|
| Trade 1 (BUY 5.5 pUSD) | -5.500000 pUSD |
| Trade 3 (SELL 9.48 DOWN @ 0.77) | +7.299600 pUSD |
| **Net realized** | **+1.799600 pUSD** |
| Trade 4 (BUY 1.0 pUSD, latency probe) | -0.999999 pUSD (still open) |
| Trade 2 (GTC at 0.99) | unfilled, no effect |

The user sold at 0.77 instead of waiting for the 0.99 GTC to fill. The
prevailing DOWN bid at the time of the manual sell was 0.77 (best-bid 0.01,
best-ask 0.99, mid ~0.50 — the market was pricing a roughly even chance of
UP vs DOWN with no clear leader at 14:43Z). The 0.99 GTC was at the top of
the book but the market wasn't crossing through that level before the user
manually exited.

## Latency measurements

| Phase | Trade 1 (BUY 5.5) | Trade 4 (BUY 1.0, instrumented) |
|---|---|---|
| POST `/order` start | unknown (script clock began earlier) | **14:48:39.748 UTC** |
| POST `/order` end (response received) | ~14:42:35 | **14:48:40.132 UTC** |
| POST round-trip | n/a | **384 ms** |
| On-chain block timestamp | 14:41:51 (block 88034617) | 14:48:42 (block 88034891) |
| Total POST → on-chain settlement | n/a | **~2.3 s** (Polygon's ~2 s block time + mempool) |

**Round-trip POST latency: 384 ms** — V2 client from `eu-west-1` to
`clob.polymarket.com` (`eu-west-1` cluster, same region).
**End-to-end to on-chain settlement: ~2–3 s** — limited by Polygon's block
time, not the CLOB matching engine.

The V2 server returns `status: "matched"` **synchronously** in the POST
response when the order is a marketable FAK that crosses the book. The
`transactionsHashes[0]` in the response is the on-chain settlement tx that
is visible ~2 s later in the Data API.

## What this proves

1. The V2 order path is reachable from a custom Node.js script with a
   properly installed canary client. No need to wait for a new `py-clob-client`
   release.
2. pUSD is the new collateral and it is auto-detected by the V2 client (no
   config change needed once the client's environment is `production`).
3. The CTF Exchange address for V2 is `0x4D97DCd97eC945f40cF65F87097ACe5EA0476045`
   — the OLD V1 address `0x4bFb41d5…8982E` is no longer where allowance needs
   to be set. (The user's allowance to the new address was already maxed.)
4. Polymarket web UI orders route through the same CLOB, so the trade ledger
   is shared.
5. The V2 canary client works on Node 18 if `globalThis.crypto = webcrypto`
   is set at the top of the entry script.

## What this does NOT prove

- The V2 canary is the production release — it's a canary build and the
  public API may change without notice. The canary is the only installable
  option as of 2026-06-06; for production traffic, run a pinned version.
- The V2 client has no equivalent of `py-clob-client` for Python; the only
  way to place orders from Python today is via a custom HTTP wrapper around
  the V2 canary or a port of its signing code (we did not succeed at this
  manually — the server uses a different type hash than the public
  `ts-sdk`).
- We did not exercise RFQ (V3) or negRisk exchange orders. Both likely have
  their own settling contracts and may require additional setup.

## What worked vs. what didn't

### Worked
- ✅ V2 canary client installed and authenticates against the production server
- ✅ Reading public order books, midpoints, prices
- ✅ Reading authenticated balances, positions, trades
- ✅ Placing FAK BUY market orders (matched, settled on-chain)
- ✅ Placing GTC SELL limit orders (resting on the book, not yet filled)
- ✅ Reading on-chain block timestamps via public Polygon RPC
- ✅ pUSD is correctly the new collateral, no manual conversion needed

### Did not work / was not tested
- ❌ V1 `py-clob-client` order placement — server now rejects with "invalid order version"
- ❌ V1 `@polymarket/clob-client` (any version) — same rejection
- ❌ Hand-rolled V2 in Python — type hash mismatches the server's expectation
- ❌ Building `Polymarket/ts-sdk` from source — needs Node 24+
- ❌ `setupTradingApprovals` in the canary — needs a Builder API key, which we did not have
- ❌ RFQ (V3) orders — not tested
- ❌ Token conversion USDC.e → pUSD on the funder — had $0.008 USDC.e and $0 pUSD's predecessor balance; user did a direct pUSD deposit, no on-chain conversion was needed
