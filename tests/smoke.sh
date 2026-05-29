#!/usr/bin/env bash
# Smoke test for alphascout — runs in CI and locally.
# Checks: scripts compile, CLIs parse, backends fail gracefully without keys,
# and (best-effort) the yfinance backend can fetch live data.
set -uo pipefail
cd "$(dirname "$0")/.."

PY="${PYTHON:-python3}"
fail=0
pass() { echo "  ✅ $1"; }
die()  { echo "  ❌ $1"; fail=1; }

echo "1) Compile all scripts"
if "$PY" -m py_compile scripts/*.py; then pass "py_compile"; else die "syntax error"; fi

echo "2) CLI --help works (argparse integrity)"
for s in fd finnhub yf; do
  if "$PY" scripts/$s.py --help >/dev/null 2>&1; then pass "$s.py --help"; else die "$s.py --help"; fi
done

echo "3) Keyed backends fail gracefully without a key (no traceback)"
TMPHOME="$(mktemp -d)"
for s in fd finnhub; do
  out=$(HOME="$TMPHOME" FINANCIAL_DATASETS_API_KEY='' FINNHUB_API_KEY='' "$PY" scripts/$s.py income AAPL 2>&1); rc=$?
  if [ "$rc" -ne 0 ] && ! printf '%s' "$out" | grep -q "Traceback"; then
    pass "$s.py clean no-key error"
  else
    die "$s.py should exit non-zero with a clean message (got rc=$rc)"
  fi
done

echo "4) yfinance live fetch (best-effort — Yahoo can be flaky, non-fatal)"
if "$PY" -c "import yfinance" >/dev/null 2>&1; then
  if "$PY" -W ignore scripts/yf.py price AAPL 2>/dev/null | grep -q '"price"'; then
    pass "yf.py live fetch"
  else
    echo "  ⚠️  yfinance fetch failed (rate-limited / network) — not failing the build"
  fi
else
  echo "  ⚠️  yfinance not installed — skipping live fetch"
fi

echo
if [ "$fail" -eq 0 ]; then echo "SMOKE TEST PASSED ✅"; else echo "SMOKE TEST FAILED ❌"; fi
exit "$fail"
