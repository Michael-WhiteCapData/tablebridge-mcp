# Contributing to tablebridge

Thanks for your interest! This server stays small, focused, and read-only-safe — contributions that keep it that way merge easiest.

## Getting set up

```bash
git clone https://github.com/Michael-WhiteCapData/tablebridge-mcp
cd tablebridge-mcp
uv pip install -e ".[dev]"
```

## Before opening a PR

- `ruff check .` passes (`ruff check --fix .` to autofix).
- `pytest` passes. Tests use real DuckDB over temp files — no external services.
- New behavior comes with a test.
- **Security:** any change to `query`/SQL handling must keep the read-only guarantees — single statement, no writes, no raw file-access functions, no escaping the data directory. Add a test proving the new path stays sandboxed.

## Architecture

- `config.py` — env-driven config (data dir, row cap) + supported formats.
- `db.py` — DuckDB engine: materializes files as tables, validates SQL, runs queries.
- `server.py` — the MCP tool layer (thin; delegates to `TableBridge`).

## Ideas welcome

- More input formats (e.g. Excel via the DuckDB `excel` extension).
- A `schema_summary` tool that profiles columns.

## Code of conduct

Be decent, assume good faith, keep it constructive.
