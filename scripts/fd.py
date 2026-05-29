#!/usr/bin/env python3
"""
financialdatasets.ai API client — backing tool for the `alphascout` skill.

Zero external dependencies (urllib only). Resolves the API key from, in order:
  1. $FINANCIAL_DATASETS_API_KEY
  2. <skill dir>/.env
  3. ~/workspace/dexter/.env   (the cloned Dexter project)

Usage:
  fd.py income   AAPL [--period annual|quarterly|ttm] [--limit N]
  fd.py balance  AAPL [--period ...] [--limit N]
  fd.py cashflow AAPL [--period ...] [--limit N]
  fd.py all      AAPL [--period ...] [--limit N]      # income+balance+cashflow combined
  fd.py metrics  AAPL [--period ...] [--limit N]      # historical key ratios / financial metrics
  fd.py snapshot AAPL                                 # latest key-ratio snapshot
  fd.py price    AAPL                                 # current price snapshot
  fd.py prices   AAPL --start 2025-01-01 --end 2025-06-01 [--interval day|week|month|year]
  fd.py news     [AAPL] [--limit N]                   # omit ticker for market-wide news
  fd.py earnings AAPL [--limit N]
  fd.py insider  AAPL [--limit N]
  fd.py holdings AAPL [--limit N]                     # institutional holdings
  fd.py filings  AAPL [--limit N]
  fd.py raw GET /financials/income-statements/ ticker=AAPL period=annual limit=4
  fd.py raw POST /financials/search/screener/ '{"period":"ttm","limit":10,"filters":[...]}'

Output is pretty-printed JSON on stdout. Errors go to stderr with a non-zero exit.
"""
import sys
import os
import json
import argparse
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

BASE = "https://api.financialdatasets.ai"


def load_key() -> str:
    key = os.environ.get("FINANCIAL_DATASETS_API_KEY")
    if key:
        return key.strip()
    candidates = [
        Path(__file__).resolve().parent.parent / ".env",
        Path.home() / "workspace" / "dexter" / ".env",
        Path.home() / ".claude" / "skills" / "alphascout" / ".env",
    ]
    for p in candidates:
        try:
            for line in p.read_text().splitlines():
                line = line.strip()
                if line.startswith("FINANCIAL_DATASETS_API_KEY="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val and not val.startswith("your-"):
                        return val
        except OSError:
            continue
    return ""


def request(method: str, endpoint: str, params=None, body=None):
    key = load_key()
    if not key:
        sys.exit(
            "ERROR: no Financial Datasets API key found.\n"
            "Set $FINANCIAL_DATASETS_API_KEY or add it to the skill's .env."
        )
    url = BASE + endpoint
    if params:
        flat = [(k, v) for k, v in params.items() if v is not None]
        if flat:
            url += "?" + urllib.parse.urlencode(flat)
    data = json.dumps(body).encode() if body is not None else None
    headers = {
        "x-api-key": key,
        "Accept": "application/json",
        # Cloudflare (error 1010) bans the default urllib UA; present a normal one.
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:500]
        sys.exit(f"HTTP {e.code} {e.reason} on {method} {endpoint}\n{detail}")
    except urllib.error.URLError as e:
        sys.exit(f"Network error on {method} {endpoint}: {e.reason}")


def emit(obj):
    json.dump(obj, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


# ---- subcommand handlers ---------------------------------------------------

def fin(endpoint, args):
    return request("GET", endpoint, {
        "ticker": args.ticker.upper(),
        "period": args.period,
        "limit": args.limit,
    })


def main():
    p = argparse.ArgumentParser(prog="fd.py", add_help=True)
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_fin(name):
        sp = sub.add_parser(name)
        sp.add_argument("ticker")
        sp.add_argument("--period", default="annual",
                        choices=["annual", "quarterly", "ttm"])
        sp.add_argument("--limit", type=int, default=4)
        return sp

    for n in ("income", "balance", "cashflow", "all", "metrics"):
        add_fin(n)

    sp = sub.add_parser("snapshot"); sp.add_argument("ticker")
    sp = sub.add_parser("price"); sp.add_argument("ticker")

    sp = sub.add_parser("prices")
    sp.add_argument("ticker")
    sp.add_argument("--start", required=True)
    sp.add_argument("--end", required=True)
    sp.add_argument("--interval", default="day",
                    choices=["day", "week", "month", "year"])

    sp = sub.add_parser("news")
    sp.add_argument("ticker", nargs="?", default=None)
    sp.add_argument("--limit", type=int, default=10)

    for n in ("earnings", "insider", "holdings", "filings"):
        sp = sub.add_parser(n)
        sp.add_argument("ticker")
        sp.add_argument("--limit", type=int, default=10)

    sp = sub.add_parser("raw")
    sp.add_argument("method", choices=["GET", "POST"])
    sp.add_argument("endpoint")
    sp.add_argument("rest", nargs=argparse.REMAINDER)

    args = p.parse_args()
    c = args.cmd

    endpoints = {
        "income": "/financials/income-statements/",
        "balance": "/financials/balance-sheets/",
        "cashflow": "/financials/cash-flow-statements/",
        "all": "/financials/",
        "metrics": "/financial-metrics/",
    }

    if c in endpoints:
        emit(fin(endpoints[c], args))
    elif c == "snapshot":
        emit(request("GET", "/financial-metrics/snapshot/", {"ticker": args.ticker.upper()}))
    elif c == "price":
        emit(request("GET", "/prices/snapshot/", {"ticker": args.ticker.upper()}))
    elif c == "prices":
        emit(request("GET", "/prices/", {
            "ticker": args.ticker.upper(), "interval": args.interval,
            "interval_multiplier": 1, "start_date": args.start, "end_date": args.end,
        }))
    elif c == "news":
        emit(request("GET", "/news", {
            "ticker": args.ticker.upper() if args.ticker else None,
            "limit": min(args.limit, 100),
        }))
    elif c == "earnings":
        emit(request("GET", "/earnings", {"ticker": args.ticker.upper(), "limit": args.limit}))
    elif c == "insider":
        emit(request("GET", "/insider-trades/", {"ticker": args.ticker.upper(), "limit": args.limit}))
    elif c == "holdings":
        emit(request("GET", "/institutional-holdings/", {"ticker": args.ticker.upper(), "limit": args.limit}))
    elif c == "filings":
        emit(request("GET", "/filings/", {"ticker": args.ticker.upper(), "limit": args.limit}))
    elif c == "raw":
        if args.method == "GET":
            params = {}
            for kv in args.rest:
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    params[k] = v
            emit(request("GET", args.endpoint, params))
        else:
            body = json.loads(args.rest[0]) if args.rest else {}
            emit(request("POST", args.endpoint, body=body))


if __name__ == "__main__":
    main()
