"""
Offscreen screenshot visual diff comparison and red highlight mask generation module
"""

import os
from typing import Dict, Any, Optional
from PIL import Image, ImageEnhance


def compare_screenshots(
    baseline_path: str,
    current_path: str,
    diff_output_path: Optional[str] = None,
    threshold: float = 0.05,
    tolerance: int = 10,
) -> Dict[str, Any]:
    """
    Compares two screenshot images, calculates pixel difference percentage with tolerance filtering,
    and optionally generates a visual diff highlight mask image.
    """
    abs_baseline = os.path.abspath(baseline_path)
    abs_current = os.path.abspath(current_path)

    if not os.path.exists(abs_baseline):
        return {
            "status": "error",
            "message": f"Baseline screenshot not found at {abs_baseline}",
        }
    if not os.path.exists(abs_current):
        return {
            "status": "error",
            "message": f"Current screenshot not found at {abs_current}",
        }

    try:
        base_img = Image.open(abs_baseline).convert("RGBA")
        curr_img = Image.open(abs_current).convert("RGBA")

        if base_img.size != curr_img.size:
            return {
                "status": "error",
                "message": f"Image dimension mismatch: baseline is {base_img.size}, current is {curr_img.size}",
                "baseline_size": base_img.size,
                "current_size": curr_img.size,
            }

        width, height = base_img.size
        total_pixels = width * height

        base_pixels = base_img.load()
        curr_pixels = curr_img.load()

        diff_pixel_count = 0
        diff_mask = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        mask_pixels = diff_mask.load()

        # Create dimmed grayscale base image for diff overlay background
        gray_curr = ImageEnhance.Brightness(
            curr_img.convert("L").convert("RGBA")
        ).enhance(0.4)
        gray_pixels = gray_curr.load()

        for y in range(height):
            for x in range(width):
                r1, g1, b1, a1 = base_pixels[x, y]
                r2, g2, b2, a2 = curr_pixels[x, y]

                color_diff = abs(r1 - r2) + abs(g1 - g2) + abs(b1 - b2)
                alpha_diff = abs(a1 - a2)

                if color_diff > tolerance or alpha_diff > tolerance:
                    diff_pixel_count += 1
                    mask_pixels[x, y] = (
                        255,
                        0,
                        60,
                        255,
                    )  # Vibrant red highlight for diff
                else:
                    mask_pixels[x, y] = gray_pixels[x, y]

        diff_percentage = round(diff_pixel_count / total_pixels, 4)
        within_threshold = diff_percentage <= threshold

        saved_diff_path = None
        if diff_output_path:
            abs_diff_out = os.path.abspath(diff_output_path)
            diff_dir = os.path.dirname(abs_diff_out)
            if diff_dir:
                os.makedirs(diff_dir, exist_ok=True)
            diff_mask.save(abs_diff_out)
            saved_diff_path = abs_diff_out

        status_result = "success" if within_threshold else "diff_detected"

        return {
            "status": status_result,
            "within_threshold": within_threshold,
            "diff_percentage": diff_percentage,
            "threshold": threshold,
            "tolerance": tolerance,
            "diff_pixel_count": diff_pixel_count,
            "total_pixels": total_pixels,
            "baseline_path": abs_baseline,
            "current_path": abs_current,
            "diff_output_path": saved_diff_path,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
