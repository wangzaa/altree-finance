"""Refresh `data/_shared/` caches: rates, FX, macro.

These are not ticker-scoped — they're project-wide reference data.

Staleness windows:
  - rates/  : 7 days
  - fx/     : 1 day
  - macro/  : 30 days

OpenBB API surface notes (verified against OpenBB 4.7.1):
  - Rates use ``fixedincome.government.yield_curve``. Providers actually
    available: ``federal_reserve`` (US only), ``econdb`` (global by
    country), ``fmp``, ``fred``. There is NO direct ECB / BoE / BoJ
    provider — global non-US rates come from ``econdb``.
  - FX uses ``currency.price.historical`` with providers ``fmp``,
    ``tiingo``, ``yfinance``. There is no direct ECB reference-rate
    integration; we use ``yfinance`` (consistent with the rest of the
    project's equity-data source). Documented in
    ``docs/providers/openbb.md``.
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

# OpenBB import is deferred to avoid heavy import at module load when only
# the staleness helpers are needed (e.g., from fetch.py's --status flag).


STALENESS_DAYS = {
    "rates": 7,
    "fx":    1,
    "macro": 30,
}

# Maps our internal region label → econdb's country string for yield_curve.
# econdb's accepted countries (OpenBB 4.7.1): australia, canada, china,
# ecb_instantaneous_forward, ecb_par_yield, ecb_spot_rate, hong_kong, india,
# japan, mexico, new_zealand, russia, saudi_arabia, singapore, south_africa,
# south_korea, taiwan, thailand, united_kingdom, united_states.
ECONDB_COUNTRY = {
    "UK":       "united_kingdom",
    "EUROZONE": "ecb_spot_rate",   # ECB spot rate — closest available proxy for Eurozone
    "JAPAN":    "japan",
}

# FX pairs we care about (vs USD) — yfinance Yahoo symbol form.
# Yahoo's CCYUSD=X syntax returns USD-per-unit of the base currency
# (e.g. EURUSD=X close=1.18 means 1 EUR = 1.18 USD).
FX_PAIRS = [
    "EURUSD=X",  # Eurozone
    "GBPUSD=X",  # UK
    "JPYUSD=X",  # Japan
    "AUDUSD=X",  # Australia
    "CADUSD=X",  # Canada
    "CHFUSD=X",  # Switzerland
    "KRWUSD=X",  # Korea — KOSPI / KOSDAQ tickers
    "TWDUSD=X",  # Taiwan — TWSE / Taipei OTC tickers
]


def is_fresh(stamp_path: Path, max_age_days: int) -> bool:
    """Return True if a file's modification time is within ``max_age_days``."""
    if not stamp_path.exists():
        return False
    age = (datetime.now(timezone.utc).timestamp() - stamp_path.stat().st_mtime) / 86400
    return age <= max_age_days


def stamp(path: Path) -> None:
    """Write ISO-8601 UTC timestamp to ``fetched_at.txt`` next to ``path``."""
    iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    path.mkdir(parents=True, exist_ok=True)
    (path / "fetched_at.txt").write_text(iso)


def _write_rate_csv(rows: Iterable[tuple[str, float]], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "rate"])
        for date, rate in rows:
            w.writerow([date, rate])


def _extract_10y_rate(results) -> tuple[str, float] | None:
    """Find the 10-year point in a yield_curve result set.

    Returns (date, rate) for the maturity_years closest to 10, or None.
    """
    best = None
    best_diff = float("inf")
    for r in results:
        years = getattr(r, "maturity_years", None)
        if years is None:
            continue
        diff = abs(float(years) - 10.0)
        if diff < best_diff:
            best_diff = diff
            best = (str(r.date), float(r.rate))
    return best


def refresh_rates(shared_root: Path, force: bool = False) -> None:
    """Populate `_shared/rates/{us,eu,uk,jp}_10y.csv` via OpenBB."""
    from openbb import obb

    rates_dir = shared_root / "rates"
    stamp_file = rates_dir / "fetched_at.txt"
    if not force and is_fresh(stamp_file, STALENESS_DAYS["rates"]):
        return

    rates_dir.mkdir(parents=True, exist_ok=True)

    # US 10Y — Federal Reserve (H.15)
    us = obb.fixedincome.government.yield_curve(provider="federal_reserve")
    point = _extract_10y_rate(us.results)
    if point:
        _write_rate_csv([point], rates_dir / "us_10y.csv")

    # Non-US — econdb global yield curves
    for region, country in ECONDB_COUNTRY.items():
        try:
            data = obb.fixedincome.government.yield_curve(
                provider="econdb", country=country
            )
            point = _extract_10y_rate(data.results)
            if point:
                fname = {"UK": "uk_10y.csv", "EUROZONE": "eu_10y.csv", "JAPAN": "jp_10y.csv"}[region]
                _write_rate_csv([point], rates_dir / fname)
        except Exception as e:
            # Non-fatal — log and continue. Other regions may still succeed.
            print(f"warn: rates refresh failed for {region} ({country}): {e}")

    stamp(rates_dir)


def refresh_fx(shared_root: Path, force: bool = False) -> None:
    """Populate `_shared/fx/yfinance_fx.csv` via OpenBB→yfinance.

    Note: OpenBB 4.7.1 does not expose ECB reference rates through
    `currency.price.historical` (providers are fmp/tiingo/yfinance). We use
    yfinance for consistency with the rest of the equity data layer. The
    rates are mid-market prices from Yahoo Finance, EOD.
    """
    from openbb import obb

    fx_dir = shared_root / "fx"
    stamp_file = fx_dir / "fetched_at.txt"
    if not force and is_fresh(stamp_file, STALENESS_DAYS["fx"]):
        return

    fx_dir.mkdir(parents=True, exist_ok=True)
    out_rows = []
    for pair in FX_PAIRS:
        try:
            data = obb.currency.price.historical(symbol=pair, provider="yfinance")
            if not data.results:
                continue
            # pair like 'EURUSD=X' returns USD per 1 unit of the base currency.
            # e.g. EURUSD=X close=1.18 means 1 EUR = 1.18 USD.
            # Walk from the newest bar backwards to skip NaN closes
            # (some pairs have data gaps on weekends/holidays).
            ccy = pair[:3]
            chosen = None
            for r in reversed(data.results):
                c = r.close
                if c is None:
                    continue
                try:
                    cf = float(c)
                except (TypeError, ValueError):
                    continue
                # numpy NaN slips past float() — explicit isnan check
                if cf != cf:  # NaN != NaN
                    continue
                if cf > 0:
                    chosen = (str(r.date), ccy, cf)
                    break
            if chosen:
                out_rows.append(chosen)
            else:
                print(f"warn: FX pair {pair} had no valid bar")
        except Exception as e:
            print(f"warn: FX refresh failed for {pair}: {e}")

    out = fx_dir / "yfinance_fx.csv"
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "currency", "usd_per_unit"])
        for row in out_rows:
            w.writerow(row)
    stamp(fx_dir)


def refresh_macro(shared_root: Path, force: bool = False) -> None:
    """Populate `_shared/macro/` minimal indicators via OpenBB."""
    from openbb import obb

    macro_dir = shared_root / "macro"
    stamp_file = macro_dir / "fetched_at.txt"
    if not force and is_fresh(stamp_file, STALENESS_DAYS["macro"]):
        return

    macro_dir.mkdir(parents=True, exist_ok=True)

    # GDP via OECD
    try:
        gdp = obb.economy.gdp.real(provider="oecd")
        with open(macro_dir / "oecd_gdp.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["country", "date", "value"])
            for r in gdp.results:
                country = getattr(r, "country", None) or ""
                date = str(getattr(r, "date", ""))
                value = getattr(r, "value", None)
                if value is not None:
                    w.writerow([country, date, value])
    except Exception as e:
        print(f"warn: GDP refresh failed: {e}")

    # CPI via OECD for major countries
    try:
        cpi = obb.economy.cpi(
            country=["united_states", "united_kingdom", "japan", "germany"],
            provider="oecd",
            transform="yoy",
            frequency="monthly",
        )
        with open(macro_dir / "oecd_cpi.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["country", "date", "value"])
            for r in cpi.results:
                country = getattr(r, "country", None) or ""
                date = str(getattr(r, "date", ""))
                value = getattr(r, "value", None)
                if value is not None:
                    w.writerow([country, date, value])
    except Exception as e:
        print(f"warn: CPI refresh failed: {e}")

    stamp(macro_dir)


def refresh_all(shared_root: Path, force: bool = False) -> None:
    """Refresh rates, FX, macro (each respects its own staleness window unless forced)."""
    refresh_rates(shared_root, force=force)
    refresh_fx(shared_root, force=force)
    refresh_macro(shared_root, force=force)
