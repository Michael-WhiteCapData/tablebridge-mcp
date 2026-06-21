"""tablebridge — query your scattered CSV / Parquet / JSON files with SQL, via MCP.

Points a DuckDB engine at a directory of tabular files, exposes each as a SQL
view, and lets an agent run read-only SQL (including JOINs across files) — so a
pile of exports becomes one queryable source of truth. Sandboxed to a single
data directory and read-only by default.
"""

from .config import Config
from .db import TableBridge, TableBridgeError

__all__ = ["Config", "TableBridge", "TableBridgeError", "__version__"]
__version__ = "0.1.0"
