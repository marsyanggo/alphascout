# alphascout 📊

A [Claude Code](https://claude.com/claude-code) **skill** that turns Claude into an
autonomous financial research analyst. Ask it to analyze, value, compare, or screen public
companies and it pulls **real market data** — fundamentals, prices, valuation ratios, news,
analyst forecasts, insider trades, and institutional holdings — then reasons over it.

It ships with **three interchangeable data backends** so you're never blocked:

| Backend | Script | Coverage | API key | Best for |
|---------|--------|----------|---------|----------|
| **yfinance** | `scripts/yf.py` | Whole market (incl. small/mid caps) | none | Default — works for any ticker, free |
| **Financial Datasets** | `scripts/fd.py` | US; free tier = a few large caps | yes | LLM-clean format |
| **Finnhub** | `scripts/finnhub.py` | Whole market | free key | Analyst estimates, recommendation trends |

The skill cross-validates figures across backends when it matters (price, multiples, margins).

## Install

This is a personal Claude Code skill. Clone it into your skills directory:

```bash
git clone https://github.com/<you>/alphascout.git \
  ~/.claude/skills/alphascout
cd ~/.claude/skills/alphascout
./install.sh          # creates .venv and installs yfinance
```

The `yfinance` backend works immediately with **no API key**. For the other two:

```bash
cp .env.example .env  # then add your keys (or export them as env vars)
```
- **Financial Datasets** key: https://financialdatasets.ai
- **Finnhub** free key: https://finnhub.io/register

## Use

Just talk to Claude Code naturally — the skill triggers automatically:

- "analyze NVDA's last 5 years of revenue and margins"
- "compare AAPL, MSFT and GOOGL on gross margin and FCF"
- "is NU overvalued? what's the upside to analyst targets?"
- "research the memory sector — MU, SK Hynix, Sandisk"

Or run a backend directly:

```bash
.venv/bin/python -W ignore scripts/yf.py income AAL --limit 5
.venv/bin/python -W ignore scripts/yf.py forecast NU
python3 scripts/finnhub.py recs MU
python3 scripts/fd.py income AAPL --limit 4
```

## ⚠️ Disclaimer

For **educational and informational purposes only**. Not financial advice. Data may be
incomplete, delayed, or wrong — always verify before making any decision. yfinance scrapes
Yahoo Finance and is not an official API.

## Acknowledgments

- **Methodology & design inspired by [Dexter](https://github.com/virattt/dexter)** by
  [@virattt](https://github.com/virattt) — an autonomous financial research agent (MIT
  License). This skill reimplements the data-tool + research-workflow idea natively for
  Claude Code; it does not include Dexter's source code.
- Data sources: [Financial Datasets](https://financialdatasets.ai),
  [yfinance](https://github.com/ranaroussi/yfinance) (Yahoo Finance),
  and [Finnhub](https://finnhub.io).

## License

[MIT](./LICENSE)
