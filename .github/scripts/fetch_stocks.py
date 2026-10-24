"""Fetch watchlist quotes and price history from Yahoo Finance and write stocks.json.

Usage: python fetch_stocks.py <out.json> [<previous.json>]

If a symbol fails to download, its entry from the previous file is kept and marked stale,
so one bad request doesn't blank the page.
"""
import json
import sys
import time
from datetime import datetime, timezone

import yfinance as yf

GROUPS = [
    ("AI & platforms", ["AVGO", "META"]),
    ("Memory", ["MU", "SNDK", "WDC", "005930.KS", "000660.KS"]),
]

# Chart series kept per symbol; 1M, 6M and YTD are cut from the 1Y daily series in the page
SERIES = {
    "1D": dict(period="1d", interval="5m"),
    "5D": dict(period="5d", interval="30m"),
    "1Y": dict(period="1y", interval="1d"),
    "5Y": dict(period="5y", interval="1wk"),
}


def num(v, digits=None):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    if v != v:  # NaN
        return None
    return round(v, digits) if digits is not None else v


def history(ticker, period, interval, digits):
    df = ticker.history(period=period, interval=interval, auto_adjust=False)
    return [[int(ts.timestamp()), num(close, digits)]
            for ts, close in zip(df.index, df["Close"]) if num(close) is not None]


def fetch(symbol):
    t = yf.Ticker(symbol)
    info = t.info
    price = num(info.get("currentPrice") or info.get("regularMarketPrice"))
    prev = num(info.get("regularMarketPreviousClose") or info.get("previousClose"))
    if price is None or prev is None:
        raise ValueError("no price")
    digits = 2 if price >= 10 else 4
    rate = num(info.get("dividendRate"))
    entry = {
        "symbol": symbol,
        "name": info.get("shortName") or info.get("longName") or symbol,
        "exchange": info.get("fullExchangeName") or info.get("exchange"),
        "currency": info.get("currency") or "USD",
        "marketState": info.get("marketState"),
        "price": round(price, digits),
        "prevClose": round(prev, digits),
        "change": round(price - prev, digits),
        "changePct": round((price / prev - 1) * 100, 2),
        "open": num(info.get("regularMarketOpen") or info.get("open"), digits),
        "dayLow": num(info.get("regularMarketDayLow") or info.get("dayLow"), digits),
        "dayHigh": num(info.get("regularMarketDayHigh") or info.get("dayHigh"), digits),
        "yearLow": num(info.get("fiftyTwoWeekLow"), digits),
        "yearHigh": num(info.get("fiftyTwoWeekHigh"), digits),
        "marketCap": num(info.get("marketCap")),
        "pe": num(info.get("trailingPE"), 2),
        "divYield": round(rate / price * 100, 2) if rate else None,
        "volume": num(info.get("regularMarketVolume") or info.get("volume")),
        "avgVolume": num(info.get("averageVolume")),
        "series": {},
    }
    for key, args in SERIES.items():
        entry["series"][key] = history(t, args["period"], args["interval"], digits)
        time.sleep(0.5)
    if not entry["series"]["1Y"]:
        raise ValueError("no history")
    return entry


def main():
    out = sys.argv[1]
    previous = {}
    if len(sys.argv) > 2:
        try:
            old = json.load(open(sys.argv[2]))
            previous = {s["symbol"]: s for g in old["groups"] for s in g["stocks"]}
        except Exception:
            pass

    fresh = 0
    groups = []
    for name, symbols in GROUPS:
        stocks = []
        for symbol in symbols:
            try:
                entry = fetch(symbol)
                entry["updated"] = int(time.time())
                fresh += 1
            except Exception as e:
                print(f"{symbol}: {type(e).__name__}: {e}", file=sys.stderr)
                if symbol not in previous:
                    continue
                entry = dict(previous[symbol], stale=True)
            stocks.append(entry)
            time.sleep(1)
        groups.append({"name": name, "stocks": stocks})

    if fresh == 0:
        sys.exit("No symbols could be fetched; leaving the published data as it is.")

    json.dump({"generated": datetime.now(timezone.utc).isoformat(timespec="seconds"), "groups": groups},
              open(out, "w"), separators=(",", ":"))
    print(f"Wrote {out}: {fresh} fresh symbols")


if __name__ == "__main__":
    main()
