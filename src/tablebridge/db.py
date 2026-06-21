"""DuckDB engine: load a directory of tabular files as in-memory tables and run
read-only SQL over them.

Security posture:
- Files are **materialized** into in-memory tables at scan time, so queries never
  touch the filesystem afterward.
- Query SQL is validated to be a single read-only statement, and raw file-reader
  functions (read_csv, read_parquet, glob, copy, attach, …) are rejected — an
  agent cannot read a path outside the configured data directory.
"""

from __future__ import annotations

import contextlib
import re
from pathlib import Path
from typing import Any

from .config import READERS, Config


class TableBridgeError(RuntimeError):
    """A user-facing error (bad SQL, unknown table, load failure)."""


_ALLOWED_START = {
    "SELECT", "WITH", "FROM", "DESCRIBE", "SUMMARIZE", "SHOW", "EXPLAIN", "VALUES", "TABLE",
}
_FORBIDDEN = re.compile(
    r"\b(read_csv|read_csv_auto|read_parquet|read_json|read_json_auto|read_ndjson|"
    r"read_text|read_blob|parquet_scan|glob|copy|attach|detach|install|load|export|import)\b",
    re.IGNORECASE,
)
_IDENT = re.compile(r"\W+")


def _table_name(path: Path, taken: set[str]) -> str:
    base = _IDENT.sub("_", path.stem).strip("_").lower() or "table"
    name, i = base, 2
    while name in taken:
        name, i = f"{base}_{i}", i + 1
    return name


def validate_sql(sql: str) -> str:
    """Return the SQL if it is a single safe read-only statement, else raise."""
    stmts = [s for s in (part.strip() for part in sql.split(";")) if s]
    if len(stmts) != 1:
        raise TableBridgeError("Provide exactly one SQL statement.")
    stmt = stmts[0]
    first = stmt.split(None, 1)[0].upper() if stmt.split() else ""
    if first not in _ALLOWED_START:
        raise TableBridgeError(
            f"Only read-only queries are allowed (got '{first or '?'}'). "
            "Use SELECT / WITH / DESCRIBE / SUMMARIZE / SHOW."
        )
    if _FORBIDDEN.search(stmt):
        raise TableBridgeError(
            "Raw file access functions are not allowed. Query the registered tables "
            "by name (see list_sources)."
        )
    return stmt


class TableBridge:
    """Loads a data directory into DuckDB and answers read-only queries."""

    def __init__(self, config: Config, con: Any = None) -> None:
        self._config = config
        self._registry: dict[str, dict[str, str]] = {}
        self._own_con = con is None
        self._con = con if con is not None else self._new_con()
        self.scan()

    def _new_con(self) -> Any:
        import duckdb  # noqa: PLC0415

        return duckdb.connect(":memory:")

    @property
    def config(self) -> Config:
        return self._config

    # -- loading -------------------------------------------------------------

    def scan(self) -> int:
        """(Re)load supported files under the data dir as in-memory tables.

        Reconnects first (when we own the connection) so a prior scan's
        ``enable_external_access=false`` lock is reset and files can be read again.
        """
        if self._own_con:
            self._con = self._new_con()
        self._registry.clear()
        pattern = "**/*" if self._config.recursive else "*"
        taken: set[str] = set()
        for path in sorted(self._config.data_dir.glob(pattern)):
            reader = READERS.get(path.suffix.lower())
            if not path.is_file() or reader is None:
                continue
            name = _table_name(path, taken)
            taken.add(name)
            try:
                self._con.execute(
                    f'CREATE OR REPLACE TABLE "{name}" AS SELECT * FROM {reader}(?)',
                    [str(path)],
                )
            except Exception as exc:  # noqa: BLE001 - surface load errors per file
                raise TableBridgeError(f"Failed to load {path.name}: {exc}") from exc
            rel = str(path.relative_to(self._config.data_dir))
            self._registry[name] = {"file": rel, "kind": path.suffix.lower().lstrip(".")}
        # Defense in depth: once data is materialized, forbid further file access.
        with contextlib.suppress(Exception):
            self._con.execute("SET enable_external_access=false")
        return len(self._registry)

    # -- introspection -------------------------------------------------------

    def list_sources(self) -> list[dict[str, Any]]:
        out = []
        for name, meta in self._registry.items():
            cols = self._con.execute(f'SELECT * FROM "{name}" LIMIT 0').description
            out.append({"table": name, "file": meta["file"], "kind": meta["kind"], "columns": len(cols)})
        return out

    def describe(self, table: str) -> list[dict[str, str]]:
        self._require(table)
        rows = self._con.execute(f'DESCRIBE "{table}"').fetchall()
        return [{"column": r[0], "type": r[1]} for r in rows]

    def preview(self, table: str, n: int = 20) -> dict[str, Any]:
        self._require(table)
        n = max(1, min(n, self._config.max_rows))
        return self._fetch(f'SELECT * FROM "{table}" LIMIT {n}')

    def query(self, sql: str) -> dict[str, Any]:
        return self._fetch(validate_sql(sql))

    # -- helpers -------------------------------------------------------------

    def _require(self, table: str) -> None:
        if table not in self._registry:
            known = ", ".join(self._registry) or "(none)"
            raise TableBridgeError(f"Unknown table '{table}'. Available: {known}")

    def _fetch(self, sql: str) -> dict[str, Any]:
        try:
            cur = self._con.execute(sql)
        except Exception as exc:  # noqa: BLE001 - return query errors to the agent
            raise TableBridgeError(f"Query failed: {exc}") from exc
        columns = [d[0] for d in cur.description] if cur.description else []
        cap = self._config.max_rows
        rows = cur.fetchmany(cap + 1)
        truncated = len(rows) > cap
        rows = rows[:cap]
        return {
            "columns": columns,
            "rows": [dict(zip(columns, r, strict=False)) for r in rows],
            "row_count": len(rows),
            "truncated": truncated,
        }
