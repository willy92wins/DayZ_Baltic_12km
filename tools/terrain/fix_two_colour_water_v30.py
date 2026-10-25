"""Stage EV96: remove the two-colour water on EV95.

Cause (measured 2026-10-11 at (1912,6495) on reference B): where a pond plane covers a bed below the engine
sea (sea 0.75 +- 0.25 m), the sea renders under the pond and shows through as dark, wavy water; where the bed
is at or above 1.0 m the pond looks clear. Fix, per Guillermo 2026-10-11:
  A. pond cells with level >= 1.95 m and bed < 1.0 m: raise the bed to 1.0 m (draft stays >= 0.95 m);
  B. low watercourse reaches (cls 3/5/6/7, level < 1.95 m) that contain a sub-sea bed: become engine sea.
     Their pond pieces are removed and their bed is lowered to -0.5 m so the sea covers them uniformly.
Lakes (cls 2) are never converted. Road reserve and platform vertices are never edited.
Outputs go to a fresh build folder; EV95 inputs are hash-checked and read only.
"""
import hashlib, json, shutil, sys
from pathlib import Path

import numpy as np
from scipy import ndimage as nd

sys.path.insert(0, r"C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290/tools/terrain")
from wrp0wzd import read, write  # noqa: E402

EV95 = Path("E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/build-wide-slope")
OUT = Path("E:/DayZ-Baltic-Build/v30-water-two-colour-fix-20261011")
BBOX = OUT / "water-piece-bbox.npz"
SRC_TREE = EV95 / "package/world/root/dayz_baltic_12km_dev/tb/narva_trial"
PINS = {EV95 / "candidate/terrain.npz": "40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a",
        SRC_TREE / "baltic_trial.wrp": "66ed9a7fd9f1d1554df51983055226181194fede8a297dbb0a18a6abb7eab384"}
SEA_CLEAR = 1.0
HIGH_LEVEL = 1.95
SEA_BED = -0.5
WATERCOURSE = (3, 5, 6, 7)
REMOVE_FRACTION = 0.5


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    for p, h in PINS.items():
        assert sha(p) == h, p
    stage = OUT / "stage"
    if stage.exists():
        raise FileExistsError("stage output must be fresh")
    z = np.load(EV95 / "candidate/terrain.npz")
    arrays = {k: z[k].copy() for k in z.files}
    H, L, W, C = arrays["heights"], arrays["level"], arrays["water"], arrays["cls"]
    frozen = arrays["reserve"] | arrays["platform"]
    pond = W & np.isfinite(L) & (L > 0.9)
    bad = pond & (H < SEA_CLEAR)

    raise_a = pond & (L >= HIGH_LEVEL) & (H < SEA_CLEAR)
    low = pond & (L < HIGH_LEVEL) & np.isin(C, WATERCOURSE)
    lab, _ = nd.label(low, structure=np.ones((3, 3)))
    ids = np.unique(lab[bad & low])
    conv = np.isin(lab, ids[ids > 0])

    H2 = H.copy()
    a_edit = raise_a & ~frozen
    b_edit = conv & ~frozen & (H > SEA_BED)
    H2[a_edit] = np.float32(SEA_CLEAR)
    H2[b_edit] = np.float32(SEA_BED)

    wrp = read(SRC_TREE / "baltic_trial.wrp")
    assert np.array_equal(wrp["heights"], H[::-1])
    bb = np.load(BBOX)
    table = {n: (lo, hi) for n, lo, hi in zip(bb["names"], bb["bbox_min"], bb["bbox_max"])}
    removed, kept_records, ambiguous = [], [], []
    for o in wrp["objects"]:
        name = o["name"].lower()
        if not name.startswith("baltic_water_v30"):
            kept_records.append(o["bytes"])
            continue
        lo, hi = table[name]
        m = np.array(o["matrix"][:9]).reshape(3, 3)
        pos = np.array(o["matrix"][9:12])
        corners = np.array([[x, y, zz] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for zz in (lo[2], hi[2])])
        world = corners @ m + pos
        x0, x1 = world[:, 0].min(), world[:, 0].max()
        z0, z1 = world[:, 2].min(), world[:, 2].max()
        y_mid = float(world[:, 1].mean())
        c0, c1 = max(0, int(np.floor(x0 / 6))), min(2047, int(np.ceil(x1 / 6)))
        r0, r1 = max(0, int(np.floor(2047 - z1 / 6))), min(2047, int(np.ceil(2047 - z0 / 6)))
        win_pond = pond[r0:r1 + 1, c0:c1 + 1] & (np.abs(L[r0:r1 + 1, c0:c1 + 1] - y_mid) < 0.3)
        win_conv = conv[r0:r1 + 1, c0:c1 + 1] & win_pond
        n_pond, n_conv = int(win_pond.sum()), int(win_conv.sum())
        frac = n_conv / n_pond if n_pond else 0.0
        if n_conv and frac >= REMOVE_FRACTION:
            removed.append(dict(name=o["name"], pos=[float(v) for v in pos], frac=round(frac, 3), cells=n_conv))
        else:
            kept_records.append(o["bytes"])
            if n_conv:
                ambiguous.append(dict(name=o["name"], pos=[float(v) for v in pos], frac=round(frac, 3), cells=n_conv))

    shutil.copytree(SRC_TREE, stage / "root/dayz_baltic_12km_dev/tb/narva_trial")
    target = stage / "root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp"
    target.unlink()
    write(target, wrp["header"], H2[::-1], wrp["materials"], kept_records, wrp["terminator"])
    back = read(target)
    assert np.array_equal(back["heights"], H2[::-1]) and len(back["objects"]) == len(kept_records)
    arrays["heights"] = H2
    arrays["ev96_bed_raised"] = a_edit
    arrays["ev96_converted_to_sea"] = conv
    np.savez(OUT / "terrain-ev96.npz", **arrays)
    report = dict(
        schema="ev96-water-two-colour-stage.v1",
        inputs={str(p): h for p, h in PINS.items()},
        params=dict(SEA_CLEAR=SEA_CLEAR, HIGH_LEVEL=HIGH_LEVEL, SEA_BED=SEA_BED, WATERCOURSE=WATERCOURSE, REMOVE_FRACTION=REMOVE_FRACTION),
        raise_cells=int(raise_a.sum()), raise_edited=int(a_edit.sum()), raise_frozen_skipped=int((raise_a & frozen).sum()),
        raise_min_draft=float((L[a_edit] - SEA_CLEAR).min()) if a_edit.any() else None,
        convert_cells=int(conv.sum()), convert_lowered=int(b_edit.sum()), convert_frozen_skipped=int((conv & frozen).sum()),
        convert_frozen_dry=int((conv & frozen & (H > 0.25)).sum()),
        heights_changed=int((H2 != H).sum()), dry_cells_changed=int(((H2 != H) & ~W).sum()),
        objects_before=len(wrp["objects"]), objects_after=len(kept_records), pieces_removed=len(removed),
        pieces_ambiguous_kept=len(ambiguous), ambiguous=ambiguous[:200], removed=removed,
        wrp_sha256=sha(target), terrain_sha256=sha(OUT / "terrain-ev96.npz"))
    assert report["dry_cells_changed"] == 0
    (OUT / "stage-report.json").write_text(json.dumps(report, indent=1))
    print({k: v for k, v in report.items() if k not in ("removed", "ambiguous", "inputs")})


if __name__ == "__main__":
    main()
