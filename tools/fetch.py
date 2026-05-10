"""CLI orchestrator: fetch one ticker's data into ./data/<DIR>/.

Usage:
  python tools/fetch.py <TICKER>                       # fetch one ticker
  python tools/fetch.py <TICKER> --peers MSFT,GOOG     # also peers
  python tools/fetch.py <TICKER> --erp 0.052           # override ERP
  python tools/fetch.py <TICKER> --tax-rate 0.23       # override marginal tax
  python tools/fetch.py <TICKER> --force               # ignore freshness
  python tools/fetch.py --suggest-peers <TICKER>       # print candidate peers
  python tools/fetch.py --refresh-shared               # update _shared/
  python tools/fetch.py --status                       # cached tickers + ages
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow running as `python tools/fetch.py <TICKER>` by adding the repo root
# (parent of this file's directory) to sys.path before importing `tools.*`.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import requests  # noqa: E402

from tools.tickers import parse_ticker  # noqa: E402
from tools.normalize import build_summary  # noqa: E402
from tools.shared import refresh_all, is_fresh, stamp  # noqa: E402


TICKER_STALENESS_HOURS = 24


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ticker_dir(data_root: Path, ticker: str) -> Path:
    parsed = parse_ticker(ticker)
    return data_root / parsed["dir_name"]


def _is_ticker_fresh(ticker_dir: Path) -> bool:
    stamp_file = ticker_dir / "fetched_at.txt"
    return is_fresh(stamp_file, max_age_days=TICKER_STALENESS_HOURS / 24)


def _to_jsonable(obj):
    """Make OpenBB pydantic outputs JSON-serializable (handles dates)."""
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_jsonable(v) for v in obj]
    return obj


def _fetch_openbb(ticker: str) -> tuple[dict, dict, list[dict], list[dict], list[dict], list[str]]:
    """Return (profile, quote, income[], balance[], cash[], suggested_peers)."""
    from openbb import obb

    # Profile (company info, sector/industry, market cap, shares)
    p = obb.equity.profile(symbol=ticker, provider="yfinance")
    profile = p.results[0].model_dump() if p.results else {}

    # Quote (current price, optional PE)
    quote: dict = {}
    try:
        q = obb.equity.price.quote(symbol=ticker, provider="yfinance")
        quote = q.results[0].model_dump() if q.results else {}
    except Exception as e:
        print(f"warn: quote fetch failed for {ticker}: {e}")

    # Fundamentals — annual, last 5 years
    def _rows(call):
        try:
            r = call(symbol=ticker, provider="yfinance", period="annual", limit=5)
            return [row.model_dump() for row in r.results]
        except Exception as e:
            print(f"warn: {call.__name__} failed for {ticker}: {e}")
            return []

    income = _rows(obb.equity.fundamental.income)
    balance = _rows(obb.equity.fundamental.balance)
    cash = _rows(obb.equity.fundamental.cash)

    # Peers — only `fmp` provider supports this in OpenBB 4.7.1, and that
    # requires an API key. Without a key, return empty and rely on user
    # passing peers via the --peers flag.
    peers: list[str] = []
    return profile, quote, income, balance, cash, peers


def _save_raw(ticker_dir: Path, profile: dict, quote: dict,
              income: list[dict], balance: list[dict], cash: list[dict],
              peers: list[str]) -> None:
    raw = ticker_dir / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "openbb_profile.json").write_text(json.dumps(_to_jsonable(profile), indent=2))
    (raw / "openbb_quote.json").write_text(json.dumps(_to_jsonable(quote), indent=2))
    (raw / "openbb_income.json").write_text(json.dumps(_to_jsonable(income), indent=2))
    (raw / "openbb_balance.json").write_text(json.dumps(_to_jsonable(balance), indent=2))
    (raw / "openbb_cash.json").write_text(json.dumps(_to_jsonable(cash), indent=2))
    if peers:
        (raw / "peers.json").write_text(json.dumps(peers, indent=2))


def _fetch_wikipedia(name: str) -> dict | None:
    """Best-effort Wikipedia summary. Failure is non-fatal (returns None)."""
    if not name:
        return None
    title = name.replace(" ", "_")
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
    try:
        r = requests.get(url, timeout=8, headers={"User-Agent": "altree-finance/0.1"})
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def _rate_csv_for(region: str, shared_root: Path) -> Path:
    rate_file_map = {
        "US": "us_10y.csv", "UK": "uk_10y.csv",
        "EUROZONE": "eu_10y.csv", "JAPAN": "jp_10y.csv",
        "ASIA_DM": "us_10y.csv", "ASIA_EM": "us_10y.csv", "OTHER": "us_10y.csv",
    }
    return shared_root / "rates" / rate_file_map[region]


def cmd_fetch(args: argparse.Namespace, data_root: Path) -> int:
    """Fetch one ticker (and optional peers)."""
    tickers = [args.ticker] + (args.peers.split(",") if args.peers else [])

    # Ensure shared cache is fresh first
    shared_root = data_root / "_shared"
    refresh_all(shared_root, force=False)

    for tkr in tickers:
        tkr = tkr.strip()
        if not tkr:
            continue
        tdir = _ticker_dir(data_root, tkr)
        if not args.force and _is_ticker_fresh(tdir):
            print(f"cached: {tkr} (fresh)")
            continue

        print(f"fetching: {tkr}")
        profile, quote, income, balance, cash, peers = _fetch_openbb(tkr)
        tdir.mkdir(parents=True, exist_ok=True)
        _save_raw(tdir, profile, quote, income, balance, cash, peers)

        # Wikipedia (best-effort, non-fatal)
        wiki = _fetch_wikipedia(profile.get("name") or "")
        if wiki:
            (tdir / "raw" / "wikipedia_summary.json").write_text(json.dumps(wiki, indent=2))

        parsed = parse_ticker(tkr)
        rate_csv = _rate_csv_for(parsed["region"], shared_root)

        # All peers passed on the same fetch are first-class fetches; the
        # --peers flag also gets persisted as suggested_yfinance for the
        # primary ticker so /comps can find them.
        manual_peers = args.peers.split(",") if args.peers and tkr == args.ticker else []
        manual_peers = [p.strip() for p in manual_peers if p.strip() and p.strip() != tkr]

        summary = build_summary(
            ticker=tkr,
            profile=profile,
            quote=quote,
            income=income,
            balance=balance,
            cash=cash,
            rate_csv_path=rate_csv,
            fetched_at=_now_iso(),
            peers=manual_peers,
        )

        # CLI overrides
        if args.erp is not None:
            summary["wacc_inputs"]["equityRiskPremium"] = {
                "value":  args.erp,
                "source": f"CLI override (--erp {args.erp})",
            }
        if args.tax_rate is not None:
            summary["wacc_inputs"]["marginalTaxRate"] = args.tax_rate

        (tdir / "summary.json").write_text(json.dumps(_to_jsonable(summary), indent=2))
        stamp(tdir)
        print(f"  → wrote {tdir}/summary.json")

    return 0


def cmd_suggest_peers(args: argparse.Namespace, data_root: Path) -> int:
    """Print candidate peers without writing any data."""
    profile, _q, _i, _b, _c, _peers = _fetch_openbb(args.ticker)
    industry = (
        profile.get("industry")
        or profile.get("industry_group")
        or profile.get("industry_category")
        or "?"
    )
    print(f"{args.ticker} — {profile.get('name', '?')}")
    print(f"  Sector:   {profile.get('sector', '?')}")
    print(f"  Industry: {industry}")
    print(f"  Yahoo-suggested peers: (not available without FMP API key)")
    print(f"  → Specify peers manually with --peers TICKER1,TICKER2,...")
    return 0


def cmd_refresh_shared(args: argparse.Namespace, data_root: Path) -> int:
    refresh_all(data_root / "_shared", force=True)
    print("shared/ refreshed.")
    return 0


def cmd_status(args: argparse.Namespace, data_root: Path) -> int:
    print(f"data root: {data_root}")
    if not data_root.exists():
        print("(no data)")
        return 0
    for child in sorted(data_root.iterdir()):
        if child.is_dir() and child.name != "_shared":
            stamp_file = child / "fetched_at.txt"
            age = "?"
            if stamp_file.exists():
                age = stamp_file.read_text().strip()
            print(f"  {child.name:<20} fetched_at={age}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch financial data into ./data/")
    parser.add_argument("ticker", nargs="?", help="Ticker symbol (e.g. AAPL, 7203.T, BARC.L)")
    parser.add_argument("--peers", help="Comma-separated peer tickers to also fetch")
    parser.add_argument("--erp", type=float, help="Override equity risk premium for this run")
    parser.add_argument("--tax-rate", type=float, help="Override marginal tax rate for this run")
    parser.add_argument("--force", action="store_true", help="Ignore staleness, refetch")
    parser.add_argument("--suggest-peers", action="store_true", help="Print candidate peers, no fetch")
    parser.add_argument("--refresh-shared", action="store_true", help="Update _shared/ rates, FX, macro")
    parser.add_argument("--status", action="store_true", help="List cached tickers and ages")
    parser.add_argument("--data-root", default="./data", help="Cache root (default: ./data)")
    args = parser.parse_args()

    data_root = Path(args.data_root).resolve()

    if args.status:
        return cmd_status(args, data_root)
    if args.refresh_shared:
        return cmd_refresh_shared(args, data_root)
    if not args.ticker:
        parser.print_help()
        return 1
    if args.suggest_peers:
        return cmd_suggest_peers(args, data_root)
    return cmd_fetch(args, data_root)


if __name__ == "__main__":
    sys.exit(main())
