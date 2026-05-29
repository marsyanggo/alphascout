#!/usr/bin/env python3
"""
Finnhub backend for the `alphascout` skill — free tier with an API key.
Strong for analyst estimates, recommendation trends, and a wide ratio set.

Key resolution order:
  1. $FINNHUB_API_KEY
  2. <skill dir>/.env           (line: FINNHUB_API_KEY=...)
  3. ~/workspace/dexter/.env
Get a free key at https://finnhub.io/register

Zero external deps (urllib). Usage:
  finnhub.py quote      AAL              # real-time-ish quote
  finnhub.py metrics    AAL              # basic financials: margins, ratios, 52w range
  finnhub.py financials AAL [--freq annual|quarterly]   # as-reported statements
  finnhub.py earnings   AAL              # EPS estimate vs actual (surprises)
  finnhub.py recs       AAL              # analyst recommendation trends
  finnhub.py target     AAL              # price target (may require paid plan)
  finnhub.py news       AAL [--days N]
  finnhub.py raw /endpoint k=v ...       # escape hatch
"""
import sys
import os
import json
import argparse
import datetime
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

BASE = "https://finnhub.io/api/v1"


def load_key() -> str:
    k = os.environ.get("FINNHUB_API_KEY")
    if k:
        return k.strip()
    for p in [Path(__file__).resolve().parent.parent / ".env",
              Path.home() / "workspace" / "dexter" / ".env"]:
        try:
            for line in p.read_text().splitlines():
                line = line.strip()
                if line.startswith("FINNHUB_API_KEY="):
                    v = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if v and not v.startswith("your-"):
                        return v
        except OSError:
            continue
    return ""


def get(endpoint, params):
    key = load_key()
    if not key:
        sys.exit("ERROR: no FINNHUB_API_KEY found. Get a free key at https://finnhub.io/register "
                 "and add FINNHUB_API_KEY=... to the skill's .env")
    params = {**params, "token": key}
    url = f"{BASE}{endpoint}?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "curl/8.0"})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} {e.reason} on {endpoint}: {e.read().decode('utf-8','replace')[:300]}")
    except urllib.error.URLError as e:
        sys.exit(f"Network error on {endpoint}: {e.reason}")


def emit(o):
    json.dump(o, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


def main():
    p = argparse.ArgumentParser(prog="finnhub.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    for n in ("quote", "metrics", "earnings", "recs", "target"):
        sp = sub.add_parser(n); sp.add_argument("ticker")
    sp = sub.add_parser("financials"); sp.add_argument("ticker")
    sp.add_argument("--freq", default="annual", choices=["annual", "quarterly"])
    sp = sub.add_parser("news"); sp.add_argument("ticker"); sp.add_argument("--days", type=int, default=14)
    sp = sub.add_parser("raw"); sp.add_argument("endpoint"); sp.add_argument("rest", nargs=argparse.REMAINDER)

    a = p.parse_args()
    sym = a.ticker.upper() if hasattr(a, "ticker") else None
    c = a.cmd

    if c == "quote":
        emit(get("/quote", {"symbol": sym}))
    elif c == "metrics":
        emit(get("/stock/metric", {"symbol": sym, "metric": "all"}))
    elif c == "financials":
        emit(get("/stock/financials-reported", {"symbol": sym, "freq": a.freq}))
    elif c == "earnings":
        emit(get("/stock/earnings", {"symbol": sym}))
    elif c == "recs":
        emit(get("/stock/recommendation", {"symbol": sym}))
    elif c == "target":
        emit(get("/stock/price-target", {"symbol": sym}))
    elif c == "news":
        today = datetime.date.today()
        frm = today - datetime.timedelta(days=a.days)
        emit(get("/company-news", {"symbol": sym, "from": frm.isoformat(), "to": today.isoformat()}))
    elif c == "raw":
        params = dict(kv.split("=", 1) for kv in a.rest if "=" in kv)
        emit(get(a.endpoint, params))


if __name__ == "__main__":
    main()
