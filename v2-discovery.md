# CLOB V2 Order Migration — Discovery Process

The Polymarket CLOB server was upgraded in April 2026 ("CTF Exchange V2" + native
pUSD stablecoin) and now **only accepts V2 order formats**. All V1 SDKs are
rejected at the server with `400 invalid order version, please use the latest
clob-client`. This document is the engineering log of how we discovered the
working path.

## TL;DR

| SDK | Version | Works for orders? | Why / why not |
|---|---|---|---|
| `py-clob-client` (PyPI) | 0.34.6 (latest) | ❌ no | V1 EIP-712 struct only |
| `@polymarket/clob-client` (npm) | 4.22.8 (last CJS) | ❌ no | V1 struct |
| `@polymarket/clob-client` (npm) | 5.8.1 (latest) | ❌ no | V1 struct |
| `@polymarket/order-utils` (npm) | 2.1.0 (latest on registry) | ❌ no | V1 struct |
| `@polymarket/order-utils` (npm) | 3.0.1 (latest, dist-tag=latest) | ❌ no | npm dist still V1 |
| `@polymarket/client` (npm canary) | `0.0.0-canary-20260520141050` | ✅ yes | V2 + `ox` + `viem` |
| `Polymarket/clob-order-utils` GitHub `main` | source | ❌ no | still V1 (PR not merged) |
| `Polymarket/ts-sdk` GitHub `main` | source | ✅ yes | V2 (build requires Node 24+) |

The npm canary `@polymarket/client@0.0.0-canary-20260520141050` is the only
publicly installable package that produces a server-accepted V2 order. Published
2026-05-20.

## What we tried (in order)

### 1. The V1 clients we already had

We had the official Polymarket Python and JavaScript clients installed and they
worked for read endpoints, L2 auth headers, and (historically) order placement.
Then the V2 migration happened and the same code started getting rejected.

**`py-clob-client==0.34.6` (PyPI, latest)**
- Signs the V1 order struct: `Order(uint256 salt,address maker,address signer,address taker,uint256 tokenId,uint256 makerAmount,uint256 takerAmount,uint256 expiration,uint256 nonce,uint256 feeRateBps,uint8 side,uint8 signatureType)`
- Domain: `name="Polymarket CTF Exchange", version="1"`
- Server response: `400 {"error":"invalid order version, please use the latest clob-client"}`
- The `py-clob-client` GitHub repo is **archived** and redirects to `Polymarket/py-sdk` (unified V2 SDK, not on PyPI).

**`@polymarket/clob-client@5.8.1` (npm, latest)**
- Same V1 EIP-712 struct.
- Server response: same `invalid order version`.
- 5.8.1 is ESM-only (no CJS entry). Downgrading to `4.22.8` (last CJS) gives the same V1 behavior.

**`@polymarket/order-utils@3.0.1` (npm dist-tag=latest)**
- Despite the version bump from 2.1.0 → 3.0.x, the npm `dist/` is still the V1 struct. The V2 struct lives in a future release not yet on the registry.

### 2. Hand-rolled V2 in Python (failed)

We ported the V2 struct from `Polymarket/ts-sdk/packages/client/src/exchange.ts`
(verified in commit) into a standalone Python signer. The V2 struct is:

```
Order(uint256 salt,address maker,address signer,uint256 tokenId,
      uint256 makerAmount,uint256 takerAmount,uint8 side,uint8 signatureType,
      uint256 timestamp,bytes32 metadata,bytes32 builder)
```

Domain: `name="Polymarket CTF Exchange", version="2"` (or `"3"` for RFQ),
verifyingContract = `0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E` (CTF
Exchange; negRisk uses `0xC5d563A36AE78145C45a50134d48A1215220f80a`).

Wire body shape we used:

```json
{
  "deferExec": false,
  "order": {
    "salt": 1234567890,
    "maker": "0x...",
    "signer": "0x...",
    "tokenId": "...",
    "makerAmount": "...",
    "takerAmount": "...",
    "side": "BUY",
    "expiration": "0",
    "signatureType": 2,
    "signature": "0x...",
    "timestamp": "...",
    "builder": "0x0000...0000",
    "metadata": ""
  },
  "orderType": "FAK",
  "owner": "<L2_KEY>"
}
```

Results across iterations:
- 128-bit salt + V2: `400 {"error":"Invalid order payload"}` (server-side salt truncation breaks signature)
- 53-bit salt + V2: `400 {"error":"invalid order version, please use the latest clob-client"}`
- 53-bit salt + V3: same
- HMAC: confirmed the official `clob-client` uses **standard base64** (not urlsafe) for the secret, with `+/→-_` and keeping the trailing `=` pad.

So the struct was correct, the HMAC was correct, the salt was correct, but the
server still said "invalid order version". This led us to conclude the
**server-side V2 is not exactly what `ts-sdk` defines** — the canary client
(`@polymarket/client`) must be reading from a newer / internal version of the
type hash.

### 3. Cloning `Polymarket/ts-sdk` and trying to build (failed)

`Polymarket/ts-sdk` is the unified V2 SDK. The repo requires Node 24+ and
pnpm; our environment has Node 18.20.8. We cloned the repo, confirmed the
exchange.ts source matches what we'd already ported to Python, and abandoned
the build route.

### 4. The breakthrough: the npm canary

Searching npm with `npm view @polymarket/client` revealed:

```
@polymarket/client@0.0.0-canary-20260520141050  (published 2026-05-20)
The Polymarket SDK TypeScript client
```

This is the V2 client. ESM-only, depends on `ox`, `viem`, and `ky`. The package
re-exports the V2 client object and helpers.

Installing:

```bash
mkdir -p /tmp/v2-new && cd /tmp/v2-new
npm init -y
npm install @polymarket/client@0.0.0-canary-20260520141050 viem
```

Three issues to fix before it works on Node 18:

1. **ESM only** — script must be `.mjs`, not `.js`.
2. **`crypto.subtle` undefined** — `ox` calls `globalThis.crypto.subtle`. On Node 18, the global is present but the `ox` bundler expects it in a specific shape. Fix:
   ```js
   import { webcrypto } from 'node:crypto';
   globalThis.crypto = webcrypto;
   ```
   Put this at the top of the file.
3. **Environment must be the exported `production` object**:
   ```js
   import { createSecureClient, production } from '@polymarket/client';
   ```
   Not a custom `environment: { chainId: 137, host: '...' }` object — the
   production constant carries the full config including `depositWalletFactory`
   and other V2 contract addresses the client needs.

With those three fixes, the first real call (`getServerTime` or `placeMarketOrder`)
hits the V2 server and the server returns a real business response (e.g. a
balance/allowance error) instead of "invalid order version".

## Working V2 client snippet

```js
import { webcrypto } from 'node:crypto';
globalThis.crypto = webcrypto;

import { createSecureClient, production, OrderSide } from '@polymarket/client';
import { privateKey } from '@polymarket/client/viem';

const L1 = process.env.POLY_L1_KEY;            // EOA private key (32-byte hex)
const FUNDER = process.env.POLY_FUNDER;         // Proxy wallet address
const creds = {
  key: process.env.POLY_L2_KEY,                 // UUID from /auth/api-key
  secret: process.env.POLY_L2_SECRET,          // base64
  passphrase: process.env.POLY_L2_PASSPHRASE,   // 64-char hex
};

const signer = privateKey(L1);
const client = await createSecureClient({
  signer,
  wallet: FUNDER,        // makes it a Proxy-mode client (POLY_GNOSIS_SAFE / POLY_1271)
  credentials: creds,
  environment: production,
});

// Place a $5 market order on the DOWN side
const t = Math.floor(Date.now() / 1000 / 300) * 300;
const ev = await (await fetch(`https://gamma-api.polymarket.com/events?slug=btc-updown-5m-${t}`)).json();
const downToken = JSON.parse(ev.markets[0].clobTokenIds)[1];

const resp = await client.placeMarketOrder({
  tokenId: downToken,
  amount: 5.0,
  side: OrderSide.BUY,
});
// resp: { ok, orderId, status: 'matched'|'live'|'delayed', makingAmount, takingAmount, transactionsHashes }
```

That code actually filled a real order against the live server. See
[`live-trade-results.md`](./live-trade-results.md) for the trade record.

## Key V2 changes from V1

| Aspect | V1 (rejected) | V2 (working) |
|---|---|---|
| Order struct fields | 13 (incl. `taker`, `expiration`, `nonce`, `feeRateBps`) | 11 (no `taker`/`expiration`/`nonce`/`feeRateBps`; adds `timestamp`, `metadata`, `builder`) |
| Domain version | `"1"` | `"2"` (or `"3"` for RFQ) |
| EIP-712 type hash | `0x57e64606...` | `0xbb86318a...` (in ts-sdk; canary has its own) |
| Salt | uint256 | uint256, **must be ≤ 2^53−1** |
| Collateral | USDC.e (`0x2791...`) | **pUSD** (`0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB`) |
| CTF Exchange | `0x4bFb41d5...` | `0x4D97DCd9...` (new V2) — allowance must be to this address |
| Allowance flow | pre-approve USDC.e to old exchange | pUSD allowance to V2 exchange is checked; no token swap needed if you deposit pUSD |
| Min marketable BUY size | 5 shares | 1 share (with ≥$1 notional at the ask) |
| Response shape | `{success, errorMsg, orderID, ...}` | `{ok, orderId, status, makingAmount, takingAmount, transactionsHashes, tradeIds}` |
| V1 V2 same field | `signatureType=2` (POLY_GNOSIS_SAFE) | unchanged |
| V1 V2 same field | `funder=proxy address` | unchanged |

## Why our hand-rolled V2 failed

The struct hash in the official `@polymarket/client` canary is computed
differently from the published `ts-sdk` source. We confirmed by:

1. Computing the type hash from the `ts-sdk` `ORDER_TYPE_STRING` and getting
   `0xbb86318a2138f5fa8ae32fbe8e659f8fcf13cc6ae4014a707893055433818589`.
2. Reproducing the struct hash + domain separator + EIP-712 digest for the
   same order fields in Python and in ethers `signTypedData`.
3. Both produced the same signature for the same order.
4. The server still rejected the signature with "invalid order version".

Conclusion: the canary client uses a different type hash (likely an internal
version not yet in the public `ts-sdk` source). The only reliable way to get a
V2 signature the server accepts is to call the canary's own signing code path,
not to recreate the signature manually.

## Files in this folder

| File | Purpose |
|---|---|
| `v2-discovery.md` (this) | How we figured out V2 was needed and where to find the working SDK |
| `live-trade-results.md` | The four real orders we placed against the live server |
| `end-to-end-report.md` | The latency benchmark results (75 REST + 4 WS) |
| `latency-results.scrubbed.json` | 5-run per-endpoint measurements (publish-safe) |
| `latency-results.csv` | Tabular summary of latency results |
| `trade-log.scrubbed.json` | First live-trade attempt (V1, failed with "invalid order version") |
| `latency_test.py` | The latency harness |
| `live_trade.py` | The V1 live-trade attempt (does not work after V2 migration) |
| `v2_order.py` | Hand-rolled Python V2 signer (algorithm correct, but server uses a different type hash) |
| `scrub.py` | Redact addresses/keys from results before publishing |
| `generate_report.py` | Render `end-to-end-report.md` from the latency JSON |
| `v2client/` | Earlier failed Node experiments (V1 + manual V2) |
| `/tmp/v2-new/` (NOT in repo) | Working V2 canary client + the script that actually placed trades |
