"""The tablebridge MCP server.

Tools return JSON so the agent gets structured results. Everything is read-only
and sandboxed to the configured data directory.
"""

from __future__ import annotations

import json
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from .config import Config
from .db import TableBridge

mcp = FastMCP("tablebridge")

_bridge: TableBridge | None = None


def get_bridge() -> TableBridge:
    global _bridge
    if _bridge is None:
        _bridge = TableBridge(Config.from_env())
    return _bridge


def set_bridge(bridge: TableBridge) -> None:
    """Replace the module-level bridge (used by tests)."""
    global _bridge
    _bridge = bridge


def _json(data: Any) -> str:
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
def list_sources() -> str:
    """List the tables available to query (one per data file) with column counts.

    Start here: each CSV/Parquet/JSON file under the data directory is exposed as
    a table you can SELECT from and JOIN across.
    """
    return _json(get_bridge().list_sources())


@mcp.tool()
def describe(
    table: Annotated[str, Field(description="Table name to inspect, as listed by `list_sources`.")],
) -> str:
    """Show a table's column names and DuckDB types.

    Use this before writing a `query` to learn a table's schema — its columns,
    their types, and order. The table name is the data file's stem as reported by
    `list_sources`. Read-only. Returns a JSON array of {name, type} objects.
    """
    return _json(get_bridge().describe(table))


@mcp.tool()
def preview(
    table: Annotated[str, Field(description="Table name to preview, as listed by `list_sources`.")],
    n: Annotated[int, Field(description="Number of rows to return from the top of the table.")] = 20,
) -> str:
    """Return the first ``n`` rows of a table as JSON.

    Use to eyeball a table's contents and value shapes before querying. The row
    count is capped by TABLEBRIDGE_MAX_ROWS regardless of ``n``. Read-only.
    Returns a JSON array of row objects.
    """
    return _json(get_bridge().preview(table, n))


@mcp.tool()
def query(
    sql: Annotated[
        str,
        Field(description="A read-only DuckDB SQL statement (SELECT / WITH / DESCRIBE / SUMMARIZE)."),
    ],
) -> str:
    """Run a read-only SQL query (DuckDB dialect) across the loaded tables.

    Use this for any real data question — filtering, aggregation, or JOINs across
    files. Each data file is exposed as a table (see `list_sources`); call
    `describe` first if you need a table's schema. Supports SELECT / WITH /
    DESCRIBE / SUMMARIZE; writes and raw file-access functions are rejected.
    Results are capped at TABLEBRIDGE_MAX_ROWS, with a ``truncated`` flag when
    more rows exist.
    """
    return _json(get_bridge().query(sql))


@mcp.tool()
def refresh() -> str:
    """Re-scan the data directory (pick up added/changed files) and report the count."""
    count = get_bridge().scan()
    return _json({"reloaded_tables": count})


@mcp.tool()
def server_info() -> str:
    """Report the effective configuration (data dir, row cap, supported formats)."""
    return _json(get_bridge().config.as_dict())


def main() -> None:
    """Console-script entry point: run the server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
