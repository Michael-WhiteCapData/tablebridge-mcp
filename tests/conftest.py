"""Fixtures: a temp data directory with real CSV/JSON files + a live bridge."""

from __future__ import annotations

import pytest

from tablebridge.config import Config
from tablebridge.db import TableBridge


@pytest.fixture
def data_dir(tmp_path):
    (tmp_path / "customers.csv").write_text("id,name\n1,Alice\n2,Bob\n")
    (tmp_path / "orders.csv").write_text(
        "id,customer_id,total\n10,1,99.5\n11,1,5.0\n12,2,20.0\n"
    )
    (tmp_path / "regions.json").write_text(
        '[{"customer_id":1,"region":"NY"},{"customer_id":2,"region":"CA"}]'
    )
    return tmp_path


@pytest.fixture
def bridge(data_dir):
    # max_rows=2 so truncation behavior is exercised.
    return TableBridge(Config(data_dir=data_dir, max_rows=2))
