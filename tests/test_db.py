import pytest

from tablebridge.db import TableBridgeError


def test_scan_registers_tables(bridge):
    tables = {s["table"] for s in bridge.list_sources()}
    assert {"customers", "orders", "regions"} <= tables


def test_describe_columns(bridge):
    cols = {c["column"] for c in bridge.describe("customers")}
    assert cols == {"id", "name"}


def test_preview_respects_max_rows(bridge):
    out = bridge.preview("orders", n=20)  # max_rows=2
    assert out["row_count"] == 2


def test_query_join_across_files(bridge):
    out = bridge.query(
        "SELECT c.name, SUM(o.total) AS spend FROM customers c "
        "JOIN orders o ON o.customer_id = c.id GROUP BY c.name ORDER BY c.name"
    )
    assert out["columns"] == ["name", "spend"]
    # max_rows=2 caps the two groups; both fit
    names = {r["name"] for r in out["rows"]}
    assert "Alice" in names


def test_query_truncation_flag(bridge):
    out = bridge.query("SELECT * FROM orders")  # 3 rows, cap 2
    assert out["row_count"] == 2
    assert out["truncated"] is True


def test_query_blocks_file_escape(bridge):
    with pytest.raises(TableBridgeError):
        bridge.query("SELECT * FROM read_csv_auto('/etc/passwd')")


def test_unknown_table_errors(bridge):
    with pytest.raises(TableBridgeError, match="Unknown table"):
        bridge.describe("nope")


def test_refresh_picks_up_new_file(bridge, data_dir):
    (data_dir / "extra.csv").write_text("a\n1\n")
    count = bridge.scan()
    assert "extra" in {s["table"] for s in bridge.list_sources()}
    assert count >= 4
