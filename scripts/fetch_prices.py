#!/usr/bin/env python3
"""Fetch daily closing prices for the workbench's real-data universe.

Writes one JSON file per symbol to data/prices/ and a manifest to data/index.json.
Each series keeps the most recent WINDOW trading days, using dividend- and split-
adjusted closes. Run once a day by .github/workflows/fetch-prices.yml.
"""
import json
import pathlib
import sys
from datetime import datetime, timezone

import yfinance as yf

WINDOW = 750  # matches the workbench's N (trading days per series)

UNIVERSE = [
    # Taiwan
    ("2330.TW", "台積電 TSMC", "TW", "TWD"),
    ("0050.TW", "元大台灣50 Yuanta Taiwan 50 ETF", "TW", "TWD"),
    ("2317.TW", "鴻海 Hon Hai", "TW", "TWD"),
    ("2454.TW", "聯發科 MediaTek", "TW", "TWD"),
    # Hong Kong
    ("0700.HK", "騰訊控股 Tencent", "HK", "HKD"),
    ("0005.HK", "匯豐控股 HSBC Holdings", "HK", "HKD"),
    ("9988.HK", "阿里巴巴-SW Alibaba", "HK", "HKD"),
    # United States
    ("AAPL", "Apple", "US", "USD"),
    ("MSFT", "Microsoft", "US", "USD"),
    ("NVDA", "NVIDIA", "US", "USD"),
    ("SPY", "SPDR S&P 500 ETF", "US", "USD"),
    # Mainland China (A-shares)
    ("600519.SS", "貴州茅台 Kweichow Moutai", "CN", "CNY"),
    ("000858.SZ", "五糧液 Wuliangye", "CN", "CNY"),
    ("601318.SS", "中國平安 Ping An", "CN", "CNY"),
]

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "prices"
SOURCE = "Yahoo Finance via yfinance (daily close, dividend- and split-adjusted)"


def fetch(symbol):
    df = yf.download(symbol, period="5y", interval="1d", auto_adjust=True,
                     progress=False, threads=False)
    if df is None or df.empty:
        raise RuntimeError("no data returned")
    close = df["Close"]
    if hasattr(close, "columns"):  # yfinance may return a one-column frame
        close = close.iloc[:, 0]
    close = close.dropna()
    close = close.tail(WINDOW)
    if len(close) < WINDOW:
        raise RuntimeError(f"only {len(close)} trading days, need {WINDOW}")
    dates = [d.strftime("%Y-%m-%d") for d in close.index]
    values = [round(float(v), 4) for v in close.values]
    return dates, values


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []
    failures = []
    for symbol, name, market, currency in UNIVERSE:
        try:
            dates, values = fetch(symbol)
        except Exception as exc:  # keep going; report at the end
            failures.append({"symbol": symbol, "error": str(exc)})
            print(f"FAILED {symbol}: {exc}", file=sys.stderr)
            continue
        file_name = symbol.replace(".", "_") + ".json"
        payload = {
            "symbol": symbol, "name": name, "market": market, "currency": currency,
            "source": SOURCE, "dates": dates, "close": values,
        }
        (OUT / file_name).write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        manifest.append({"symbol": symbol, "name": name, "market": market, "currency": currency,
                         "n": len(values), "start": dates[0], "end": dates[-1],
                         "file": f"data/prices/{file_name}"})
        print(f"ok {symbol}: {len(values)} days, {dates[0]} to {dates[-1]}")

    if not manifest:
        print("no symbols fetched; keeping previous data", file=sys.stderr)
        return 1
    index = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "source": SOURCE,
        "window_days": WINDOW,
        "symbols": manifest,
        "failures": failures,
    }
    (ROOT / "data" / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
