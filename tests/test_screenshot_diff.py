"""
Unit and integration tests for screenshot_diff module and screenshot-diff CLI command
"""

from PIL import Image
from typer.testing import CliRunner
from godot_cli_connect.operations.screenshot_diff import compare_screenshots
from godot_cli_connect.cli import app

runner = CliRunner()


def test_compare_identical_screenshots(tmp_path):
    b_path = tmp_path / "baseline.png"
    c_path = tmp_path / "current.png"

    img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
    img.save(b_path)
    img.save(c_path)

    res = compare_screenshots(str(b_path), str(c_path))
    assert res["status"] == "success"
    assert res["within_threshold"] is True
    assert res["diff_percentage"] == 0.0


def test_compare_different_screenshots(tmp_path):
    b_path = tmp_path / "baseline.png"
    c_path = tmp_path / "current.png"
    d_path = tmp_path / "diff.png"

    img1 = Image.new("RGBA", (100, 100), (255, 255, 255, 255))
    img2 = Image.new("RGBA", (100, 100), (0, 0, 0, 255))

    img1.save(b_path)
    img2.save(c_path)

    res = compare_screenshots(
        str(b_path), str(c_path), diff_output_path=str(d_path), threshold=0.01
    )
    assert res["status"] == "diff_detected"
    assert res["within_threshold"] is False
    assert res["diff_percentage"] == 1.0
    assert d_path.exists()


def test_cli_screenshot_diff(tmp_path):
    b_path = tmp_path / "base.png"
    c_path = tmp_path / "curr.png"

    img = Image.new("RGBA", (50, 50), (0, 255, 0, 255))
    img.save(b_path)
    img.save(c_path)

    res = runner.invoke(
        app, ["screenshot-diff", "-b", str(b_path), "-c", str(c_path), "--json"]
    )
    assert res.exit_code == 0
    assert '"status": "success"' in res.stdout
