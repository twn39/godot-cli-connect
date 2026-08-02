"""Tests for result contract helpers."""

from godot_cli_connect.models import (
    OperationResult,
    as_result_dict,
    err,
    is_success,
    ok,
)


def test_ok_flat_dict():
    res = ok(message="done", mode="offline", save_path="res://a.tscn")
    assert res["status"] == "success"
    assert res["message"] == "done"
    assert res["mode"] == "offline"
    assert res["save_path"] == "res://a.tscn"
    assert "data" not in res
    assert is_success(res)


def test_err_flat_dict():
    res = err("failed", errors=["e1"], code=2)
    assert res["status"] == "error"
    assert res["message"] == "failed"
    assert res["errors"] == ["e1"]
    assert res["code"] == 2
    assert not is_success(res)


def test_operation_result_to_flat_dict():
    r = OperationResult(status="success", message="m", data={"x": 1}, errors=[])
    flat = r.to_flat_dict()
    assert flat == {"status": "success", "message": "m", "x": 1}
    assert as_result_dict(r) == flat
    assert as_result_dict({"status": "success"})["status"] == "success"
