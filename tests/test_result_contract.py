"""Result contract and catalog alignment tests."""

from __future__ import annotations

import inspect

from godot_cli_connect.models import err, is_success, ok
from godot_cli_connect.operations import api, checker, inspector, project_init
from godot_cli_connect.operations.tools_catalog import (
    RESULT_SCHEMA,
    catalog_alignment,
    list_tools,
)


def test_ok_err_flat_envelope():
    success = ok(message="done", mode="offline", value=1)
    assert success["status"] == "success"
    assert success["message"] == "done"
    assert success["mode"] == "offline"
    assert success["value"] == 1
    assert is_success(success)

    failure = err("boom", mode="engine", code=2)
    assert failure["status"] == "error"
    assert failure["message"] == "boom"
    assert failure["mode"] == "engine"
    assert failure["code"] == 2
    assert not is_success(failure)

    custom = err("nope", status="not_found", query="x")
    assert custom["status"] == "not_found"
    assert not is_success(custom)


def test_catalog_aligns_with_cli():
    report = catalog_alignment()
    assert report["aligned"] is True, report
    assert report["catalog_count"] > 0
    assert report["cli_count"] >= report["catalog_count"]


def test_list_tools_includes_schema_and_alignment():
    res = list_tools()
    assert res["status"] == "success"
    assert "tools" in res
    assert res["result_contract"]["schema"] == RESULT_SCHEMA
    assert res["catalog_alignment"]["aligned"] is True


def test_public_ops_modules_import_ok_or_err():
    """Modules that return agent results should construct them via models helpers."""
    modules = [api, checker, inspector, project_init]
    for mod in modules:
        source = inspect.getsource(mod)
        assert "from ..models import" in source or "ok(" in source
        assert "ok(" in source or "err(" in source


def test_result_schema_documents_status():
    assert RESULT_SCHEMA["required"] == ["status"]
    assert "status" in RESULT_SCHEMA["properties"]
