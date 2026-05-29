#!/usr/bin/env python3
"""
yfinance backend for the `alphascout` skill — free, no API key, full-market
coverage (works for tickers the Financial Datasets free tier blocks, e.g. AAL).

MUST run with the skill's venv python:
  ~/.claude/skills/alphascout/.venv/bin/python yf.py <command> TICKER ...

Commands:
  income/balance/cashflow/all TICKER [--period annual|quarterly] [--limit N]
  metrics  TICKER     # valuation + profitability ratios from Yahoo .info
  price    TICKER     # latest price snapshot
  prices   TICKER --start YYYY-MM-DD --end YYYY-MM-DD [--interval 1d|1wk|1mo]
  news     TICKER [--limit N]
  forecast TICKER     # analyst estimates (revenue/EPS), price targets, recommendations
"""
import sys
import json
import math
import argparse
import warnings

warnings.filterwarnings("ignore")
try:
    import yfinance as yf
except ImportError:
    sys.exit("ERROR: yfinance not installed in the skill venv. "
             "Run: ~/.claude/skills/alphascout/.venv/bin/python -m pip install yfinance")


def clean(v):
    if v is None:
        return None
    try:
        if isinstance(v, float) and math.isnan(v):
            return None
    except (TypeError, ValueError):
        pass
    return v


def first_row(df, names):
    """Return the DataFrame row matching the first label found in `names`."""
    for n in names:
        if n in df.index:
            return df.loc[n]
    return None


def statements(t, kind, period, limit):
    if period == "quarterly":
        df = {"income": t.quarterly_income_stmt, "balance": t.quarterly_balance_sheet,
              "cashflow": t.quarterly_cashflow}[kind]
    else:
        df = {"income": t.income_stmt, "balance": t.balance_sheet,
              "cashflow": t.cashflow}[kind]
    if df is None or df.empty:
        return []

    # Map our normalized keys -> possible yfinance row labels
    fields = {
        "income": {
            "revenue": ["Total Revenue", "Operating Revenue"],
            "gross_profit": ["Gross Profit"],
            "operating_income": ["Operating Income", "Total Operating Income As Reported"],
            "net_income": ["Net Income", "Net Income Common Stockholders"],
            "ebitda": ["EBITDA", "Normalized EBITDA"],
            "diluted_eps": ["Diluted EPS"],
        },
        "balance": {
            "total_assets": ["Total Assets"],
            "total_debt": ["Total Debt"],
            "total_equity": ["Total Equity Gross Minority Interest", "Stockholders Equity"],
            "cash": ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"],
        },
        "cashflow": {
            "operating_cash_flow": ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"],
            "capex": ["Capital Expenditure"],
            "free_cash_flow": ["Free Cash Flow"],
        },
    }[kind]

    rows = {k: first_row(df, labels) for k, labels in fields.items()}
    out = []
    for col in list(df.columns)[:limit]:
        entry = {"period": str(getattr(col, "date", lambda: col)())}
        for k, row in rows.items():
            entry[k] = clean(row[col]) if row is not None else None
        out.append(entry)
    return out


def emit(obj):
    json.dump(obj, sys.stdout, indent=2, ensure_ascii=False, default=str)
    sys.stdout.write("\n")


def main():
    p = argparse.ArgumentParser(prog="yf.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    for n in ("income", "balance", "cashflow", "all", "metrics", "price", "forecast"):
        sp = sub.add_parser(n)
        sp.add_argument("ticker")
        if n in ("income", "balance", "cashflow", "all"):
            sp.add_argument("--period", default="annual", choices=["annual", "quarterly"])
            sp.add_argument("--limit", type=int, default=5)
    sp = sub.add_parser("news"); sp.add_argument("ticker"); sp.add_argument("--limit", type=int, default=10)
    sp = sub.add_parser("prices")
    sp.add_argument("ticker"); sp.add_argument("--start", required=True)
    sp.add_argument("--end", required=True); sp.add_argument("--interval", default="1d")

    a = p.parse_args()
    t = yf.Ticker(a.ticker.upper())
    c = a.cmd

    if c in ("income", "balance", "cashflow"):
        emit({"source": "yfinance", "ticker": a.ticker.upper(), c: statements(t, c, a.period, a.limit)})
    elif c == "all":
        emit({"source": "yfinance", "ticker": a.ticker.upper(),
              "income": statements(t, "income", a.period, a.limit),
              "balance": statements(t, "balance", a.period, a.limit),
              "cashflow": statements(t, "cashflow", a.period, a.limit)})
    elif c == "metrics":
        i = t.info
        keys = ["trailingPE", "forwardPE", "priceToBook", "priceToSalesTrailing12Months",
                "enterpriseToEbitda", "returnOnEquity", "returnOnAssets", "grossMargins",
                "operatingMargins", "profitMargins", "revenueGrowth", "earningsGrowth",
                "debtToEquity", "currentRatio", "marketCap", "enterpriseValue",
                "dividendYield", "beta"]
        emit({"source": "yfinance", "ticker": a.ticker.upper(),
              "metrics": {k: clean(i.get(k)) for k in keys}})
    elif c == "price":
        fi = t.fast_info
        emit({"source": "yfinance", "ticker": a.ticker.upper(), "snapshot": {
            "price": clean(fi.get("lastPrice")), "open": clean(fi.get("open")),
            "dayHigh": clean(fi.get("dayHigh")), "dayLow": clean(fi.get("dayLow")),
            "prevClose": clean(fi.get("previousClose")), "volume": clean(fi.get("lastVolume")),
            "marketCap": clean(fi.get("marketCap"))}})
    elif c == "prices":
        h = t.history(start=a.start, end=a.end, interval=a.interval)
        out = [{"date": str(idx.date()), "open": clean(r.Open), "high": clean(r.High),
                "low": clean(r.Low), "close": clean(r.Close), "volume": clean(r.Volume)}
               for idx, r in h.iterrows()]
        emit({"source": "yfinance", "ticker": a.ticker.upper(), "prices": out})
    elif c == "news":
        items = (t.news or [])[:a.limit]
        out = []
        for n in items:
            c2 = n.get("content", n)
            out.append({"title": c2.get("title"),
                        "provider": (c2.get("provider") or {}).get("displayName"),
                        "date": c2.get("pubDate") or c2.get("displayTime"),
                        "url": (c2.get("canonicalUrl") or {}).get("url") or c2.get("link")})
        emit({"source": "yfinance", "ticker": a.ticker.upper(), "news": out})
    elif c == "forecast":
        result = {"source": "yfinance", "ticker": a.ticker.upper()}
        i = t.info
        result["forwardPE"] = clean(i.get("forwardPE"))
        result["targetMeanPrice"] = clean(i.get("targetMeanPrice"))
        result["targetLowPrice"] = clean(i.get("targetLowPrice"))
        result["targetHighPrice"] = clean(i.get("targetHighPrice"))
        result["recommendationKey"] = i.get("recommendationKey")
        result["numberOfAnalystOpinions"] = clean(i.get("numberOfAnalystOpinions"))
        for attr, label in [("earnings_estimate", "eps_estimate"),
                            ("revenue_estimate", "revenue_estimate")]:
            try:
                df = getattr(t, attr)
                if df is not None and not df.empty:
                    result[label] = {str(idx): {k: clean(v) for k, v in row.items()}
                                     for idx, row in df.iterrows()}
            except Exception:
                pass
        try:
            rec = t.recommendations
            if rec is not None and not rec.empty:
                result["recommendation_trend"] = rec.head(4).to_dict("records")
        except Exception:
            pass
        emit(result)


if __name__ == "__main__":
    main()
