<!-- mcp-name: io.github.Michael-WhiteCapData/tablebridge-mcp -->

# tablebridge

**Turn a folder of CSV / Parquet / JSON files into one SQL-queryable source for your AI agent.**

[![CI](https://github.com/Michael-WhiteCapData/tablebridge-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/Michael-WhiteCapData/tablebridge-mcp/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/tablebridge?color=3775A9&logo=pypi&logoColor=white)](https://pypi.org/project/tablebridge/)
[![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-server-D97757)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Small businesses don't have a data warehouse — they have a folder full of exports: `customers.csv`, last month's `orders.xlsx`, a `regions.json` someone emailed over. `tablebridge` is an [MCP](https://modelcontextprotocol.io/) server that points [DuckDB](https://duckdb.org/) at that folder, exposes **each file as a SQL table**, and lets your agent run **read-only SQL — including JOINs across files** — to answer questions over all of them at once. Scattered spreadsheets become one queryable source of truth.

It's **read-only and sandboxed**: files are loaded into an in-memory database, the data directory is the only thing it can see, and queries are validated so an agent can't write, escape to other paths, or call raw file functions.

---

## Why you'd want this

- 🔗 **One source over many files.** JOIN `orders.csv` to `customers.csv` to `regions.json` in a single query — no ETL, no database to stand up.
- 🦆 **DuckDB-powered.** Fast analytical SQL over CSV, TSV, Parquet, JSON/NDJSON.
- 🔒 **Safe by design.** Files are materialized into memory; queries are validated read-only; raw file-access functions and out-of-sandbox paths are rejected.
- 🤖 **Agent-friendly.** `list_sources` → `describe` → `query` is a natural flow the agent can follow on its own.
- 🪶 **Two dependencies** (`mcp`, `duckdb`), fully typed and tested.

## Install

```bash
uvx tablebridge          # run directly
# or
pip install tablebridge  # then run: tablebridge
```

### Claude Code

```bash
TABLEBRIDGE_DATA_DIR=/path/to/your/data claude mcp add tablebridge -- uvx tablebridge
```

### Claude Desktop / Cursor

```jsonc
{
  "mcpServers": {
    "tablebridge": {
      "command": "uvx",
      "args": ["tablebridge"],
      "env": { "TABLEBRIDGE_DATA_DIR": "/path/to/your/data" }
    }
  }
}
```

## Run with Docker

A [`Dockerfile`](Dockerfile) is included. The server speaks MCP over stdio. Mount the
folder you want to query at `/data` (read-only is fine) and run interactively (`-i`):

```bash
docker build -t tablebridge .
docker run --rm -i -v /path/to/your/data:/data:ro tablebridge
```

## Tools

| Tool | Description |
| --- | --- |
| `list_sources` | List the tables (one per data file) with column counts — start here |
| `describe` | A table's columns and types |
| `preview` | First N rows of a table |
| `query` | Run read-only SQL (DuckDB dialect) across the tables, JOINs included |
| `refresh` | Re-scan the data directory for added/changed files |
| `server_info` | Effective config (data dir, row cap, supported formats) |

## Example

With a folder containing `customers.csv`, `orders.csv`, and `regions.json`:

> **You:** Who are my top 3 customers by total spend, and what region are they in?
>
> **Agent:** *(calls `list_sources`, then `query`)*
> ```sql
> SELECT c.name, r.region, SUM(o.total) AS spend
> FROM customers c
> JOIN orders o   ON o.customer_id = c.id
> JOIN regions r  ON r.customer_id = c.id
> GROUP BY c.name, r.region
> ORDER BY spend DESC
> LIMIT 3;
> ```

## Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `TABLEBRIDGE_DATA_DIR` | `.` | Directory of files to expose (the sandbox boundary) |
| `TABLEBRIDGE_MAX_ROWS` | `1000` | Max rows returned per query/preview |
| `TABLEBRIDGE_RECURSIVE` | `1` | Scan subdirectories too |

Supported formats: `.csv`, `.tsv`, `.parquet`, `.json`, `.ndjson`.

## Security model

1. **Sandboxed** to `TABLEBRIDGE_DATA_DIR` — only files under it are loaded.
2. **Materialized** into an in-memory DuckDB, then external filesystem access is disabled — queries can't reach other paths.
3. **Validated SQL** — a single read-only statement only; writes and raw file-reader functions are rejected.

## Development

```bash
git clone https://github.com/Michael-WhiteCapData/tablebridge-mcp
cd tablebridge-mcp
uv pip install -e ".[dev]"
ruff check .
pytest          # uses real DuckDB over temp files
```

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE) © Michael Tierney
