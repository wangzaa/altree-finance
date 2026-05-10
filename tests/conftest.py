"""Shared pytest fixtures."""
import json
from pathlib import Path
import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def yfinance_info_aapl():
    return json.loads((FIXTURE_DIR / "yfinance_info_aapl.json").read_text())


@pytest.fixture
def yfinance_financials_aapl():
    return json.loads((FIXTURE_DIR / "yfinance_financials_aapl.json").read_text())


@pytest.fixture
def us_10y_csv_path():
    return FIXTURE_DIR / "us_10y_sample.csv"
