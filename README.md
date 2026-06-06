# Polymarket End-to-End Latency Test

A complete probe of every documented Polymarket endpoint (Gamma, CLOB REST,
Data API, RTDS, CLOB WebSocket channels) from a `c7i.4xlarge` EC2 host in
`eu-west-1`, with a small live trade on the BTC updown 5m market to measure
order-execution latency end to end.

## Contents

- `README.md` — what this repo is, how to reproduce, the constraints under
  which it was produced.
- `end-to-end-report.md` — full per-endpoint latency report (75 REST + 4 WS,
  5 runs each, 15s WS window).
- `latency-results.scrubbed.json` — per-endpoint raw samples, addresses and
  keys redacted.
- `latency-results.csv` — tabular summary of all 75 REST endpoints.
- `trade-log.scrubbed.json` — V1 live-trade attempt log (event timeline, all
  decisions, the four attempts that failed, the V2 path that worked).
- `v2-trade-log.json` — V2 live-trade ledger (4 orders, on-chain
  timestamps, latencies).
- `live-trade-results.md` — narrative of the V2 live trade, latency table,
  P&L, what worked vs didn't.
- `v2-discovery.md` — the V2 migration story: V1 clients all rejected with
  "invalid order version", the npm canary that worked, the three required
  Node 18 fixes, the EIP-712 + HMAC details.
- `endpoints-and-auth.md` — every endpoint grouped by API, with auth
  requirements and call shapes.
- `topics-and-schemas.md` — every RTDS / WS topic with field reference.
- `clob-channels.md` — CLOB Market + User channel event types, filters,
  payload shape.
- `btc-updown-slugs.md` — slug formula, event id mapping, sample slugs.
- `field-reference.md` — every field seen on the wire, with type and notes.
- `probe_rtds.py` — initial RTDS-only probe (subscribes + logs).
- `probe-output.txt` — output of the initial RTDS probe.
- `raw-responses/` — sample raw responses from Gamma (one 5m, one 15m).
- `scrub.py` — address/secret redactor. Run as `scrub.py < in.json > out.json`.
- `generate_report.py` — emits `end-to-end-report.md` from
  `latency-results.json`.
- `latency_test.py` — the test harness (live, in
  `polymarket-latency-test/`, copied here for reproducibility).
- `live_trade.py` — V1 live-trade script (deprecated; V2 path is
  `@polymarket/client` canary).
- `v2_order.py` — hand-rolled V2 in Python (correct algorithm, server uses
  a different type hash, so use the canary client instead).
- `upload_to_github.sh` — Contents API uploader. Requires
  `GITHUB_TOKEN`, `REPO_OWNER`, `REPO_NAME`, `SRC_DIR` env vars.

## Headline results

- **75/75 REST endpoints** green, 0 failures, 5 runs each. (5+ minute test
  on a single 16-vCPU host.)
- **4/4 WebSocket channels** connected and instrumented. CLOB Market
  Channel streams ~14,000 messages in 15s ≈ 933 msgs/s — much higher than
  expected, must be rate-limited in production.
- **p50 REST latency** by group:
  - Data API: 12 ms
  - Gamma: 14 ms
  - CLOB (public): 32 ms
  - CLOB (authenticated): 22 ms
- **V2 live trade** (4 orders, see `live-trade-results.md`):
  - POST round-trip: **384 ms**
  - Total to on-chain settlement: **~2.3 s** (Polygon's ~2s block time)
  - Net realized P&L on the round-trip: **+1.80 pUSD** ($5.50 in,
    9.48 DOWN @ 0.77 out)
  - 1 live order still open at end of session

## What you can learn from this repo

1. The full discovery process for Polymarket endpoints, RTDS topics, and
   CLOB WS channels (and every shape bug we hit while bringing up the
   harness).
2. The V2 migration story and the one working client to use until
   `py-clob-client` and the public `@polymarket/clob-client` ship V2.
3. A clean reproducible latency number for a V2 order from `eu-west-1`.
4. Confirmation that RTDS is **not** a continuous price push feed for
   crypto — CLOB order book is the correct live signal.
5. Confirmation that CLOB Market Channel is **much** chatier than the
   public docs imply.

## How to reproduce

```bash
# 1. Test harness
cd ~/polymarket-latency-test
python3 latency_test.py
python3 generate_report.py
# (in this repo) cat latency-results.json | ../scrub.py > latency-results.scrubbed.json

# 2. Live trade
# V1: python3 live_trade.py     (will fail with 'invalid order version')
# V2: use /tmp/v2-new/trade.mjs (see live-trade-results.md + v2-discovery.md)
```

## How to scrub before publishing

```bash
python3 scrub.py < latency-results.json > latency-results.scrubbed.json
```

`scrub.py` redacts:

- L1 private key (substring and prefix regex)
- L2 api key, secret, passphrase (substring)
- Funder / EOA addresses (substring and prefix regex for truncated forms)
- GitHub PAT (`ghp_*`)
- "Invalid API key" error messages
- Any `Authorization:` header

## Repository state at end of session

- All 15 files published to
  https://github.com/kollikrishnarao/polymarket-endpoints-test.
- Verified by fresh `git clone` + `grep` for every known secret prefix:
  0 leaks.
- The user's L1 key, L2 triple, and GitHub PAT were **not** present in
  any committed file at any point.
