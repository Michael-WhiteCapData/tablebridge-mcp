import json

from tablebridge import server
from tablebridge.config import Config


def test_config_from_env(tmp_path):
    cfg = Config.from_env(env={"TABLEBRIDGE_DATA_DIR": str(tmp_path), "TABLEBRIDGE_MAX_ROWS": "50"})
    assert cfg.data_dir == tmp_path.resolve()
    assert cfg.max_rows == 50
    assert cfg.recursive is True


def test_config_recursive_off():
    assert Config.from_env(env={"TABLEBRIDGE_RECURSIVE": "0"}).recursive is False


class StubBridge:
    def __init__(self):
        self.config = Config()
        self.calls = []

    def list_sources(self):
        return [{"table": "customers", "columns": 2}]

    def query(self, sql):
        self.calls.append(sql)
        return {"columns": ["x"], "rows": [{"x": 1}], "row_count": 1, "truncated": False}

    def scan(self):
        return 3


def test_list_sources_tool_returns_json():
    server.set_bridge(StubBridge())
    assert json.loads(server.list_sources())[0]["table"] == "customers"


def test_query_tool_delegates():
    stub = StubBridge()
    server.set_bridge(stub)
    out = json.loads(server.query("SELECT 1"))
    assert out["row_count"] == 1
    assert stub.calls == ["SELECT 1"]


def test_refresh_tool_reports_count():
    server.set_bridge(StubBridge())
    assert json.loads(server.refresh())["reloaded_tables"] == 3
