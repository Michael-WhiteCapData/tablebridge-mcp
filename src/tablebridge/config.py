"""Environment-driven configuration for the tablebridge server."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_MAX_ROWS = 1000
# File extensions we expose as SQL views, mapped to the DuckDB reader function.
READERS = {
    ".csv": "read_csv_auto",
    ".tsv": "read_csv_auto",
    ".parquet": "read_parquet",
    ".json": "read_json_auto",
    ".ndjson": "read_json_auto",
}


@dataclass(frozen=True)
class Config:
    """Effective server configuration, sourced from the environment."""

    data_dir: Path = Path(".")
    max_rows: int = DEFAULT_MAX_ROWS
    recursive: bool = True

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> Config:
        src = os.environ if env is None else env
        return cls(
            data_dir=Path(src.get("TABLEBRIDGE_DATA_DIR", ".")).expanduser().resolve(),
            max_rows=int(src.get("TABLEBRIDGE_MAX_ROWS", str(DEFAULT_MAX_ROWS))),
            recursive=src.get("TABLEBRIDGE_RECURSIVE", "1").lower() not in ("0", "false", "no"),
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "data_dir": str(self.data_dir),
            "max_rows": self.max_rows,
            "recursive": self.recursive,
            "supported_extensions": sorted(READERS),
        }
