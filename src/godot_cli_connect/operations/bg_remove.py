"""
Game asset background removal via BiRefNet_lite ONNX + OpenCV.

Default model path (project root): ``BiRefNet_lite_fp16.onnx``
  HuggingFace: baby2008/BiRefNet_lite-ONNX (model_fp16.onnx)

Pipeline:
  1. Load BGR image with OpenCV
  2. Resize to model size (1024x1024), ImageNet normalize, NCHW
  3. ONNX Runtime inference → alpha matte
  4. Resize matte to original size, compose RGBA PNG
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from ..models import err, ok

# Default relative to CWD / package project root candidates
DEFAULT_MODEL_NAME = "BiRefNet_lite_fp16.onnx"
DEFAULT_INPUT_SIZE = 1024

# ImageNet normalization (BiRefNet / torchvision convention)
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

# Official download URL (optional helper)
MODEL_DOWNLOAD_URL = (
    "https://huggingface.co/baby2008/BiRefNet_lite-ONNX/resolve/main/"
    "onnx/model_fp16.onnx?download=true"
)


def resolve_model_path(model_path: str | None = None) -> str:
    """
    Resolve ONNX model file path.

    Search order when ``model_path`` is omitted:
      1. env ``BIREFNET_MODEL``
      2. ``./BiRefNet_lite_fp16.onnx`` (cwd)
      3. ``./models/BiRefNet_lite_fp16.onnx``
      4. next to package install (rare)
    """
    if model_path:
        p = os.path.abspath(model_path)
        if not os.path.isfile(p):
            raise FileNotFoundError(f"ONNX model not found: {p}")
        return p

    env = os.environ.get("BIREFNET_MODEL")
    if env and os.path.isfile(env):
        return os.path.abspath(env)

    pkg_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    candidates = [
        os.path.abspath(DEFAULT_MODEL_NAME),
        os.path.abspath(os.path.join("models", DEFAULT_MODEL_NAME)),
        os.path.abspath(os.path.join(pkg_dir, "models", DEFAULT_MODEL_NAME)),
        os.path.abspath(os.path.join(pkg_dir, DEFAULT_MODEL_NAME)),
        os.path.abspath(os.path.join(pkg_dir, "..", "..", DEFAULT_MODEL_NAME)),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c

    raise FileNotFoundError(
        f"BiRefNet ONNX model not found. Place `{DEFAULT_MODEL_NAME}` in the project root "
        f"(or models/), set BIREFNET_MODEL, or pass --model. "
        f"Download: {MODEL_DOWNLOAD_URL}"
    )


@lru_cache(maxsize=2)
def _load_session(model_path: str):
    """Load and cache an ONNX InferenceSession for the given model path."""
    import onnxruntime as ort

    try:
        ort.set_default_logger_severity(3)  # 3 = ERROR level (suppress WARNINGs and INFO)
    except Exception:
        pass

    opts = ort.SessionOptions()
    opts.log_severity_level = 3  # 3 = ERROR level (suppress WARNINGs)
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    # Prefer CoreML/CUDA when available, fall back to CPU
    available = ort.get_available_providers()
    preferred = [
        p
        for p in ("CoreMLExecutionProvider", "CUDAExecutionProvider", "CPUExecutionProvider")
        if p in available
    ]
    if not preferred:
        preferred = ["CPUExecutionProvider"]
    return ort.InferenceSession(model_path, sess_options=opts, providers=preferred)


def _model_hw(session) -> tuple[int, int]:
    shape = session.get_inputs()[0].shape
    # [N, C, H, W] — H/W may be int or dynamic str
    h = shape[2] if isinstance(shape[2], int) else DEFAULT_INPUT_SIZE
    w = shape[3] if isinstance(shape[3], int) else DEFAULT_INPUT_SIZE
    return h, w


def preprocess_bgr(image_bgr: np.ndarray, size: tuple[int, int] = (1024, 1024)) -> np.ndarray:
    """
    BGR uint8 HWC → float32 NCHW ImageNet-normalized tensor.
    """
    h, w = size
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(rgb, (w, h), interpolation=cv2.INTER_LINEAR)
    x = resized.astype(np.float32) / 255.0
    x = (x - IMAGENET_MEAN) / IMAGENET_STD
    x = np.transpose(x, (2, 0, 1))[None, ...]  # 1,3,H,W
    return np.ascontiguousarray(x, dtype=np.float32)


def postprocess_mask(
    mask_nchw: np.ndarray,
    orig_hw: tuple[int, int],
) -> np.ndarray:
    """
    Model output [1,1,H,W] → uint8 alpha matte (H_orig, W_orig) in 0..255.
    Applies sigmoid if values look like logits.
    """
    m = np.asarray(mask_nchw).squeeze()
    if m.ndim != 2:
        m = m.reshape(m.shape[-2], m.shape[-1])

    # logits if outside [0,1] range substantially
    if m.min() < -0.01 or m.max() > 1.01:
        m = 1.0 / (1.0 + np.exp(-m.astype(np.float64)))
    else:
        m = m.astype(np.float64)
        m = np.clip(m, 0.0, 1.0)

    oh, ow = orig_hw
    m_u8 = (m * 255.0).astype(np.float32)
    m_resized = cv2.resize(m_u8, (ow, oh), interpolation=cv2.INTER_LINEAR)
    return np.clip(m_resized, 0, 255).astype(np.uint8)


def erode_alpha(alpha: np.ndarray, radius: int = 1) -> np.ndarray:
    """Erode alpha mask by `radius` pixels to eliminate outer edge white fringe."""
    if radius <= 0:
        return alpha
    kernel_size = radius * 2 + 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    return cv2.erode(alpha, kernel)


def decontaminate_colors(image_bgr: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    """
    Decontaminate background color bleed on semi-transparent edge pixels.
    Replaces RGB values of border pixels with pure foreground RGB via inpainting.
    """
    semi = (alpha > 0) & (alpha < 250)
    has_opaque = np.any(alpha >= 250)
    if not np.any(semi) or not has_opaque:
        return image_bgr

    inpaint_mask = (alpha < 250).astype(np.uint8)
    inpainted = cv2.inpaint(image_bgr, inpaint_mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA)

    clean_bgr = image_bgr.copy()
    clean_bgr[semi] = inpainted[semi]
    return clean_bgr


def compose_rgba(image_bgr: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    """BGR + alpha → BGRA uint8."""
    if alpha.shape[:2] != image_bgr.shape[:2]:
        alpha = cv2.resize(
            alpha, (image_bgr.shape[1], image_bgr.shape[0]), interpolation=cv2.INTER_LINEAR
        )
    bgra = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2BGRA)
    bgra[:, :, 3] = alpha
    return bgra


def remove_background(
    input_path: str,
    output_path: str | None = None,
    *,
    model_path: str | None = None,
    threshold: float | None = None,
    erode: int = 0,
    decontaminate: bool = False,
    save_mask: bool = False,
    mask_path: str | None = None,
) -> dict[str, Any]:
    """
    Remove background from a game asset image and write a transparent PNG.

    Args:
        input_path: Source image (png/jpg/webp/...).
        output_path: Destination RGBA PNG. Default: ``<stem>_nobg.png`` next to input.
        model_path: Optional path to BiRefNet ONNX.
        threshold: If set (0..1), hard-binarize alpha at this level after matte.
        erode: Pixels to erode/shrink alpha mask edges (1-3px fixes white fringe).
        decontaminate: Clean background color bleed from semi-transparent edge RGB pixels.
        save_mask: Also write grayscale mask PNG.
        mask_path: Optional mask output path.
    """
    abs_in = os.path.abspath(input_path)
    if not os.path.isfile(abs_in):
        return err(f"Input image not found: {abs_in}")

    try:
        model = resolve_model_path(model_path)
    except FileNotFoundError as e:
        return err(str(e))

    image = cv2.imread(abs_in, cv2.IMREAD_COLOR)
    if image is None:
        return err(f"Failed to read image (unsupported or corrupt): {abs_in}")

    orig_h, orig_w = image.shape[:2]

    if output_path is None:
        stem = Path(abs_in).stem
        parent = Path(abs_in).parent
        output_path = str(parent / f"{stem}_nobg.png")
    abs_out = os.path.abspath(output_path)
    out_dir = os.path.dirname(abs_out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    try:
        session = _load_session(model)
        in_meta = session.get_inputs()[0]
        out_meta = session.get_outputs()[0]
        mh, mw = _model_hw(session)

        tensor = preprocess_bgr(image, size=(mh, mw))
        outputs = session.run([out_meta.name], {in_meta.name: tensor})
        alpha = postprocess_mask(outputs[0], (orig_h, orig_w))

        if threshold is not None:
            t = int(np.clip(float(threshold), 0.0, 1.0) * 255)
            alpha = np.where(alpha >= t, 255, 0).astype(np.uint8)

        if erode > 0:
            alpha = erode_alpha(alpha, radius=erode)

        proc_image = image
        if decontaminate:
            proc_image = decontaminate_colors(image, alpha)

        rgba = compose_rgba(proc_image, alpha)
        ok_write = cv2.imwrite(abs_out, rgba)
        if not ok_write:
            return err(f"Failed to write output: {abs_out}")

        mask_out = None
        if save_mask:
            mask_out = (
                os.path.abspath(mask_path)
                if mask_path
                else str(Path(abs_out).with_name(Path(abs_out).stem + "_mask.png"))
            )
            cv2.imwrite(mask_out, alpha)

        return ok(
            mode="onnx",
            model="BiRefNet_lite",
            model_path=model,
            input_path=abs_in,
            output_path=abs_out,
            mask_path=mask_out,
            width=orig_w,
            height=orig_h,
            input_size=[mw, mh],
            threshold=threshold,
            providers=list(session.get_providers()),
            message=f"Background removed → {abs_out}",
        )
    except Exception as e:
        return err(f"Background removal failed: {e}")


def remove_background_batch(
    input_paths: list[str],
    output_dir: str | None = None,
    *,
    model_path: str | None = None,
    threshold: float | None = None,
    erode: int = 0,
    decontaminate: bool = False,
) -> dict[str, Any]:
    """Remove background for multiple images; shares one loaded model session."""
    results = []
    errors = []
    for p in input_paths:
        out = None
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            out = os.path.join(output_dir, f"{Path(p).stem}_nobg.png")
        res = remove_background(
            p,
            out,
            model_path=model_path,
            threshold=threshold,
            erode=erode,
            decontaminate=decontaminate,
        )
        results.append(res)
        if res.get("status") != "success":
            errors.append({"input": p, "message": res.get("message")})

    ok_count = sum(1 for r in results if r.get("status") == "success")
    return (
        ok(
            mode="onnx",
            model="BiRefNet_lite",
            total=len(input_paths),
            succeeded=ok_count,
            failed=len(input_paths) - ok_count,
            results=results,
            errors=errors or None,
            message=f"Processed {ok_count}/{len(input_paths)} images",
        )
        if ok_count
        else err(
            f"All {len(input_paths)} images failed",
            results=results,
            errors=errors,
        )
    )
