"""Shared pytest fixtures."""
import json
from pathlib import Path
import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _load(name: str):
    return json.loads((FIXTURE_DIR / name).read_text())


@pytest.fixture
def openbb_profile_aapl():
    return _load("openbb_profile_aapl.json")


@pytest.fixture
def openbb_quote_aapl():
    return _load("openbb_quote_aapl.json")


@pytest.fixture
def openbb_income_aapl():
    return _load("openbb_income_aapl.json")


@pytest.fixture
def openbb_balance_aapl():
    return _load("openbb_balance_aapl.json")


@pytest.fixture
def openbb_cash_aapl():
    return _load("openbb_cash_aapl.json")


@pytest.fixture
def us_10y_csv_path():
    return FIXTURE_DIR / "us_10y_sample.csv"
