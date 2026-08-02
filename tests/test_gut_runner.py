"""
Unit and integration tests for gut_runner module
"""

from typer.testing import CliRunner

from godot_cli_connect.cli import app
from godot_cli_connect.operations.gut_runner import (
    parse_gut_stdout,
    parse_junit_xml,
    run_gut_tests,
)

runner = CliRunner()

SAMPLE_JUNIT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
  <testsuite name="GUT Tests" tests="2" failures="1" errors="0">
    <testcase name="test_pass" classname="res.test.unit.test_player"/>
    <testcase name="test_fail" classname="res.test.unit.test_player">
      <failure message="Expected 80 but got 100"/>
    </testcase>
  </testsuite>
</testsuites>
"""


def test_parse_junit_xml(tmp_path):
    xml_file = tmp_path / "results.xml"
    xml_file.write_text(SAMPLE_JUNIT_XML)

    metrics = parse_junit_xml(str(xml_file))
    assert metrics["passed"] == 1
    assert metrics["failed"] == 1
    assert metrics["total"] == 2
    assert len(metrics["failures"]) == 1
    assert "Expected 80 but got 100" in metrics["failures"][0]["message"]


def test_parse_gut_stdout():
    stdout = """*** GUT SUMMARY ***
Passed: 10
Failed: 2
Pending: 1
"""
    metrics = parse_gut_stdout(stdout)
    assert metrics["passed"] == 10
    assert metrics["failed"] == 2
    assert metrics["pending"] == 1
    assert metrics["total"] == 13


def test_run_gut_tests_no_plugin(tmp_path):
    res = run_gut_tests(str(tmp_path))
    assert res["status"] == "error"
    assert "GUT runner script not found" in res["message"]


def test_cli_test_gut_no_plugin(tmp_path):
    res = runner.invoke(app, ["test-gut", "-p", str(tmp_path), "--json"])
    assert res.exit_code == 1
    assert '"status": "error"' in res.stdout
