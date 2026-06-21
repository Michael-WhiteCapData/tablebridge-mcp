# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and this project adheres to
[Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-06-21

### Added
- Initial release.
- Exposes a directory of CSV/TSV/Parquet/JSON/NDJSON files as DuckDB tables.
- Tools: `list_sources`, `describe`, `preview`, `query`, `refresh`, `server_info`.
- Read-only, sandboxed security model: materialized in-memory tables, external
  filesystem access disabled post-load, single read-only statement validation
  rejecting writes and raw file-access functions.
- Configurable via `TABLEBRIDGE_DATA_DIR`, `TABLEBRIDGE_MAX_ROWS`,
  `TABLEBRIDGE_RECURSIVE`.
- Test suite using real DuckDB over temp files; CI on Python 3.11 and 3.12.
- MCP registry manifest, PyPI publish + registry-publish workflows.

[0.1.0]: https://github.com/Michael-WhiteCapData/tablebridge-mcp/releases/tag/v0.1.0
