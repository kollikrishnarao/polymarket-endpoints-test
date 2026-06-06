import json
import time
import websocket
import threading

URL = "wss://ws-live-data.polymarket.com"
SYMBOLS = ["btcusdt"]
# Server actually expects JSON for crypto_prices filters, not CSV (despite docs example).
# Validation regex: ^[{[]{1}([,:{}\[\]0-9.\-+Eaeflnr-u \n\r\t]|".*?")+[}\]]{1}$
SYMBOL_FILTER = json.dumps({"symbol": ",".join(SYMBOLS)})  # e.g. {"symbol":"btcusdt"}
# Also try a list-of-symbols form
SYMBOL_FILTER_LIST = json.dumps(SYMBOLS)  # e.g. ["btcusdt"]
TIMEOUT = 12
results = {"subs": [], "msgs": [], "errors": [], "state": "init"}


def on_open(ws):
    results["state"] = "open"
    sub = {
        "action": "subscribe",
        "subscriptions": [
            {
                "topic": "crypto_prices",
                "type": "update",
                "filters": SYMBOL_FILTER,
            },
            {
                "topic": "crypto_prices_chainlink",
                "type": "*",
                "filters": json.dumps({"symbol": "btc/usd"}),
            },
            {
                "topic": "activity",
                "type": "trades",
                "filters": json.dumps({"market_slug": "btc-updown-15m-1780746300"}),
            },
        ],
    }
    ws.send(json.dumps(sub))
    results["subs"].append(sub)
    # send pings every 5s
    def keepalive():
        if ws.keep_running:
            try:
                ws.send("ping")
            except Exception:
                pass
            threading.Timer(5, keepalive).start()
    threading.Timer(5, keepalive).start()
    threading.Timer(TIMEOUT, lambda: ws.close()).start()


def on_message(ws, msg):
    try:
        parsed = json.loads(msg)
        results["msgs"].append(parsed)
    except Exception as e:
        results["msgs"].append({"raw": msg[:200], "err": str(e)})


def on_error(ws, err):
    results["errors"].append(str(err))


def on_close(ws, code, reason):
    results["state"] = f"closed code={code} reason={reason}"


ws = websocket.WebSocketApp(
    URL,
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close,
)
ws.run_forever()

print(f"STATE: {results['state']}")
print(f"SUBS_SENT: {json.dumps(results['subs'], indent=2)}")
print(f"ERRORS: {results['errors']}")
print(f"MSG_COUNT: {len(results['msgs'])}")
print()
for i, m in enumerate(results["msgs"][:4]):
    print(f"========= msg {i} =========")
    if "raw" in m:
        print(f"raw frame: {m['raw']!r}")
    else:
        # show envelope keys, but truncate the payload data array
        out = {
            "topic": m.get("topic"),
            "type": m.get("type"),
            "timestamp": m.get("timestamp"),
            "connection_id": m.get("connection_id"),
        }
        if "payload" in m and isinstance(m["payload"], dict):
            payload_summary = {k: (f"<{len(v)} items>" if isinstance(v, list) else v) for k, v in m["payload"].items()}
            out["payload"] = payload_summary
        print(json.dumps(out, indent=2))
        if "payload" in m and isinstance(m["payload"], dict) and "data" in m["payload"]:
            data = m["payload"]["data"]
            print(f"  data first 3: {data[:3]}")
            print(f"  data last 3:  {data[-3:]}")
            print(f"  data total:   {len(data)}")
        if "payload" in m and isinstance(m["payload"], dict) and "value" in m["payload"]:
            print(f"  full payload: {m['payload']}")
