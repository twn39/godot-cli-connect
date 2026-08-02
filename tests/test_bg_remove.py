"""Tests for BiRefNet background removal (mocked ORT session)."""

from pathlib import Path

import cv2
import numpy as np

from godot_cli_connect.operations import bg_remove
from godot_cli_connect.operations.bg_remove import (
    compose_rgba,
    postprocess_mask,
    preprocess_bgr,
    remove_background,
    resolve_model_path,
)


def test_preprocess_shape():
    img = np.zeros((200, 300, 3), dtype=np.uint8)
    img[:, :] = (40, 80, 120)
    t = preprocess_bgr(img, size=(1024, 1024))
    assert t.shape == (1, 3, 1024, 1024)
    assert t.dtype == np.float32


def test_postprocess_and_compose():
    logits = np.full((1, 1, 64, 64), 5.0, dtype=np.float32)  # high → white after sigmoid
    alpha = postprocess_mask(logits, (100, 120))
    assert alpha.shape == (100, 120)
    assert alpha.dtype == np.uint8
    assert alpha.mean() > 200

    bgr = np.zeros((100, 120, 3), dtype=np.uint8)
    bgr[:] = (10, 20, 30)
    bgra = compose_rgba(bgr, alpha)
    assert bgra.shape == (100, 120, 4)
    assert bgra[0, 0, 3] == alpha[0, 0]


def test_resolve_model_path(tmp_path, monkeypatch):
    model = tmp_path / "BiRefNet_lite_fp16.onnx"
    model.write_bytes(b"fake")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("BIREFNET_MODEL", raising=False)
    assert resolve_model_path(None) == str(model.resolve())
    assert resolve_model_path(str(model)) == str(model.resolve())


def test_remove_background_missing_input(tmp_path):
    res = remove_background(str(tmp_path / "nope.png"), model_path=str(tmp_path / "m.onnx"))
    assert res["status"] == "error"
    assert "not found" in res["message"].lower()


def test_remove_background_mocked(tmp_path, monkeypatch):
    # Create a simple BGR image
    img_path = tmp_path / "hero.png"
    bgr = np.zeros((64, 80, 3), dtype=np.uint8)
    bgr[10:50, 20:60] = (0, 0, 255)  # red blob
    cv2.imwrite(str(img_path), bgr)

    model = tmp_path / "BiRefNet_lite_fp16.onnx"
    model.write_bytes(b"x")

    class FakeInput:
        name = "input_image"
        shape = [1, 3, 1024, 1024]

    class FakeOutput:
        name = "output_image"
        shape = [1, 1, 1024, 1024]

    class FakeSession:
        def get_inputs(self):
            return [FakeInput()]

        def get_outputs(self):
            return [FakeOutput()]

        def get_providers(self):
            return ["CPUExecutionProvider"]

        def run(self, output_names, feed):
            # Soft center blob matte
            m = np.zeros((1, 1, 1024, 1024), dtype=np.float32)
            m[:, :, 200:800, 200:800] = 0.95
            return [m]

    monkeypatch.setattr(bg_remove, "_load_session", lambda _p: FakeSession())

    out = tmp_path / "hero_nobg.png"
    res = remove_background(str(img_path), str(out), model_path=str(model), save_mask=True)
    assert res["status"] == "success"
    assert Path(res["output_path"]).exists()
    assert Path(res["mask_path"]).exists()
    result = cv2.imread(str(out), cv2.IMREAD_UNCHANGED)
    assert result is not None
    assert result.shape[2] == 4
