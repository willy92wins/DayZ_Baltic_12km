from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
RUNTIME = HERE.parent
RECEIPT = RUNTIME / "runtime-receipt.json"
NAMES = {
    "A": "capture_20261010_214102_468.jpg",
    "A2": "capture_20261010_214130_034.jpg",
    "B": "capture_20261010_214159_815.jpg",
    "Aprime": "capture_20261010_214217_191.jpg",
}
# Rectangles in delivered 1920x1080 client coordinates [x0,y0,x1,y1),
# picked from the same static camera composition before computing deltas.
ROIS = {
    "full_client": (0, 0, 1920, 1080),
    "midwater_rect_patch": (900, 450, 1015, 515),
    "near_channel_water_control": (120, 790, 500, 1010),
    "bridge_and_piers": (500, 515, 1515, 645),
    "under_bridge_shadow_candidate": (500, 600, 1515, 735),
    "left_dry_land_control": (80, 610, 410, 780),
    "right_dry_land_control": (1430, 650, 1790, 850),
}
PAIRS = (("A", "A2", "temporal_control_A_to_A2"),
         ("A2", "B", "shadow_setting_contrast"),
         ("B", "Aprime", "restore_transition"),
         ("A2", "Aprime", "baseline_return_A2_to_Aprime"))


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_image(name, record):
    path = Path(record["fullres_path"]).resolve()
    if path.name != NAMES[name]:
        raise RuntimeError(f"receipt/image role mismatch {name}: {path}")
    got = file_sha(path)
    if got.lower() != record["fullres_file_sha256"].lower():
        raise RuntimeError(f"capture hash mismatch {name}: {got}")
    with Image.open(path) as im:
        arr = np.asarray(im.convert("RGB"), dtype=np.uint8)
    if arr.shape != (1080, 1920, 3):
        raise RuntimeError(f"unexpected image shape for {name}: {arr.shape}")
    return path, got, arr


def compare(a, b):
    d = np.abs(a.astype(np.int16) - b.astype(np.int16)).max(axis=2)
    # Pixel-level RGB absolute differences. No alignment, filtering, or edits.
    return {
        "mean_abs_max_channel": float(d.mean()),
        "median_abs_max_channel": float(np.median(d)),
        "p95_abs_max_channel": float(np.percentile(d, 95)),
        "p99_abs_max_channel": float(np.percentile(d, 99)),
        "max_abs_channel": int(d.max()),
        "fraction_pixels_gt_1": float(np.mean(d > 1)),
        "fraction_pixels_gt_2": float(np.mean(d > 2)),
        "fraction_pixels_gt_4": float(np.mean(d > 4)),
        "fraction_pixels_gt_8": float(np.mean(d > 8)),
        "mean_signed_luma_delta_b_minus_a": float(
            (0.2126 * (b[:, :, 0].astype(np.float32) - a[:, :, 0]) +
             0.7152 * (b[:, :, 1].astype(np.float32) - a[:, :, 1]) +
             0.0722 * (b[:, :, 2].astype(np.float32) - a[:, :, 2])).mean()),
    }


def signed_luma(a, b):
    aa = a.astype(np.float32); bb = b.astype(np.float32)
    return (0.2126 * (bb[:, :, 0] - aa[:, :, 0]) +
            0.7152 * (bb[:, :, 1] - aa[:, :, 1]) +
            0.0722 * (bb[:, :, 2] - aa[:, :, 2]))


def reversal_metrics(pre, enabled, restored):
    # If a static shadow change is reversible, enabled-pre and restored-enabled
    # should tend to be oppositely signed in the affected pixels.
    d_on = signed_luma(pre, enabled).ravel().astype(np.float64)
    d_off = signed_luma(enabled, restored).ravel().astype(np.float64)
    if np.std(d_on) == 0 or np.std(d_off) == 0:
        corr = None
    else:
        corr = float(np.corrcoef(d_on, d_off)[0, 1])
    denom = float(np.linalg.norm(d_on) * np.linalg.norm(d_off))
    cosine_opposite = None if denom == 0 else float(np.dot(d_on, -d_off) / denom)
    return {
        "on_mean_signed_luma": float(d_on.mean()),
        "off_mean_signed_luma": float(d_off.mean()),
        "on_off_signed_luma_correlation": corr,
        "on_vs_opposite_off_cosine": cosine_opposite,
        "state_return_residual_rms": float(np.sqrt(np.mean((d_on + d_off) ** 2))),
        "on_delta_rms": float(np.sqrt(np.mean(d_on ** 2))),
        "off_delta_rms": float(np.sqrt(np.mean(d_off ** 2))),
    }


def delta_corr(a0, a1, b0, b1):
    da = signed_luma(a0, a1).ravel().astype(np.float64)
    db = signed_luma(b0, b1).ravel().astype(np.float64)
    if np.std(da) == 0 or np.std(db) == 0:
        return None
    return float(np.corrcoef(da, db)[0, 1])


def main():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    records = {name: receipt[name][0] for name in NAMES}
    imgs = {}
    image_meta = {}
    for name, record in records.items():
        path, digest, arr = load_image(name, record)
        imgs[name] = arr
        image_meta[name] = {"path": str(path), "sha256": digest, "shape": list(arr.shape),
                            "receipt_frame_stale": record["frame_stale"],
                            "receipt_warning": record.get("warnings", []),
                            "capture_frame_sha256": record["frame_sha256"],
                            "client_pixel_sha256": record["effective_surface"]["native_pixel_sha256"],
                            "native_temporal_probe": {
                                k: record["frame_stale_detail"].get(k)
                                for k in ("frames", "distinct_frames", "max_adjacent_delta", "repeat_count")}}
    pairs = {}
    for left, right, pair_name in PAIRS:
        pairs[pair_name] = {"roles": [left, right], "rois": {}}
        for roi_name, (x0, y0, x1, y1) in ROIS.items():
            pairs[pair_name]["rois"][roi_name] = compare(
                imgs[left][y0:y1, x0:x1], imgs[right][y0:y1, x0:x1])
    reversibility = {}
    temporal_vs_setting = {}
    for roi_name, (x0, y0, x1, y1) in ROIS.items():
        crop = {k: v[y0:y1, x0:x1] for k, v in imgs.items()}
        pre = imgs["A2"][y0:y1, x0:x1]
        enabled = imgs["B"][y0:y1, x0:x1]
        restored = imgs["Aprime"][y0:y1, x0:x1]
        reversibility[roi_name] = reversal_metrics(pre, enabled, restored)
        temporal_vs_setting[roi_name] = {
            "A_to_A2_vs_A2_to_B_signed_luma_corr": delta_corr(crop["A"], crop["A2"], crop["A2"], crop["B"]),
            "A_to_A2_vs_B_to_Aprime_signed_luma_corr": delta_corr(crop["A"], crop["A2"], crop["B"], crop["Aprime"]),
        }
    result = {
        "schema": "v4-shadow-probe-pixel-difference.v1",
        "receipt_path": str(RECEIPT),
        "receipt_sha256": file_sha(RECEIPT),
        "setting_protocol": {
            "target": "engine setting id 160 Shadows, 0→1→0",
            "control": "id 163 Terrain shadows remained 0",
            "capture_order": ["A", "A2", "B", "Aprime"],
            "coordinate_system": "1920x1080 delivered client pixels; ROIs fixed before comparisons",
        },
        "images": image_meta,
        "rois_xyxy": {k: list(v) for k, v in ROIS.items()},
        "pair_differences": pairs,
        "A2_B_Aprime_reversibility": reversibility,
        "temporal_control_vs_toggle_delta_correlation": temporal_vs_setting,
        "interpretation_limits": [
            "JPEG decoded pixel deltas include compression/temporal noise; identical scene pixels are not expected to be bit-identical.",
            "frame_stale=false means the capture path saw distinct frames, not that the camera/scene animation was moving or the water shader advanced.",
            "Pixel differences alone cannot attribute change to shadows, water animation, camera jitter, exposure, fog, or another render stage.",
            "No pixel masks identify semantic water/bridge/land automatically; ROIs are manually fixed scene rectangles and may include mixed materials at edges.",
        ],
    }
    out = HERE / "pixel-difference-analysis.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "OK", "out": str(out), "receipt_sha256": result["receipt_sha256"],
                      "pairs": list(pairs)}, separators=(",", ":")))


if __name__ == "__main__":
    main()
