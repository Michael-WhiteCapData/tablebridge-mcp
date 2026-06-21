import pytest

from tablebridge.db import TableBridgeError, validate_sql


def test_allows_select_and_with():
    assert validate_sql("SELECT 1") == "SELECT 1"
    assert validate_sql("WITH t AS (SELECT 1) SELECT * FROM t").startswith("WITH")


def test_strips_trailing_semicolon():
    assert validate_sql("SELECT 1;") == "SELECT 1"


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO t VALUES (1)",
        "UPDATE t SET x=1",
        "DELETE FROM t",
        "DROP TABLE t",
        "CREATE TABLE t (x int)",
        "COPY t TO 'out.csv'",
        "ATTACH 'x.db'",
        "SET enable_external_access=true",
    ],
)
def test_rejects_writes_and_dangerous(sql):
    with pytest.raises(TableBridgeError):
        validate_sql(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM read_csv_auto('/etc/passwd')",
        "SELECT * FROM read_parquet('x')",
        "SELECT * FROM glob('/**')",
    ],
)
def test_rejects_raw_file_readers(sql):
    with pytest.raises(TableBridgeError, match="Raw file access"):
        validate_sql(sql)


def test_rejects_multiple_statements():
    with pytest.raises(TableBridgeError, match="exactly one"):
        validate_sql("SELECT 1; SELECT 2")
