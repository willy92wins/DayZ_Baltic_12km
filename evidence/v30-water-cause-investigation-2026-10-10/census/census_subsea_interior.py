from __future__ import annotations

import csv
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

sys.path.insert(0, "E:/DayZ-Baltic-Build/v30-global-water-risk-20261009")
from audit_visible_field_domain import UNIT, area, clip

OUT = Path("E:/DayZ-Baltic-Build/v30-subsea-interior-census-20261009")
BASE = Path("E:/DayZ-Baltic-Build/v30-remaining-exact-dry-support-20261009/candidate")
TERRAIN = BASE / "terrain.npz"
PFILE = BASE / "plane.npy"
FFILE = BASE / "visible-field.npy"
CONSTRAINTS = BASE.parent / "constraints.npz"
VERIFY = Path(r"C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290\evidence\v30-remaining-exact-dry-support-2026-10-09\verify.py")

# Local inherited sea levels under audit, not engine-verified levels.
SEA_NOMINAL = 0.65
SEA_MAX = 0.85
DRAFT = 0.95
RAISED_BED = 1.0
POND_CLASSES = (2, 3, 5, 6, 7)
OFFSETS = ((0, 0), (0, 1), (1, 0), (1, 1))
FACES = ((0, 1, 3), (0, 2, 3))  # NW-NE-SE and NW-SW-SE, native NW-SE diagonal


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def clip_constraints(values: np.ndarray) -> np.ndarray:
    poly = UNIT.copy()
    for value in values:
        poly = clip(poly, value)
        if len(poly) == 0:
            break
    return poly


def interval(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    lo = np.zeros(values.shape[0])
    hi = np.ones(values.shape[0])
    for d in np.moveaxis(values, 1, 0):
        a, b = d[:, 0], d[:, 1]
        delta = b - a
        cross = np.zeros(len(a))
        np.divide(-a, delta, out=cross, where=np.abs(delta) > 1e-14)
        crossing = np.clip(cross, 0, 1)
        lower = np.where((a <= 0) & (b > 0), crossing, 0)
        upper = np.where((a > 0) & (b <= 0), crossing, 1)
        upper[(a <= 0) & (b <= 0)] = 0
        lo = np.maximum(lo, lower)
        hi = np.minimum(hi, upper)
    return lo, hi


def shared(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    al, ah = interval(a)
    bl, bh = interval(b)
    return np.minimum(ah, bh) - np.maximum(al, bl) > 1e-8


def control_checks() -> list[str]:
    # Two independent checks that clipping preserves known area and rejects a zero-width join.
    assert abs(area(clip_constraints(np.ones((3, 3)))) - 18.0) < 1e-10
    a = np.array([[[1.0, -1.0]], [[1.0, 0.0]], [[1.0, 1.0]]])
    b = np.array([[[-1.0, 1.0]], [[0.0, 1.0]], [[-1.0, 1.0]]])
    assert shared(a, b).tolist() == [False, True, True]
    c = np.array([[[1.0, -1.0], [-1.0, 1.0]]])
    lo, hi = interval(c)
    assert hi[0] - lo[0] == 0
    h = np.full(3, -2.65)
    p = 2.1
    underwater = clip_constraints(np.vstack((0.85 - h, p - h)))
    raised_good = clip_constraints(np.vstack((0.85 - h, p - h, p - 0.95 - np.maximum(h, 1.0))))
    assert abs(area(underwater) - 18.0) < 1e-10
    assert abs(area(raised_good) - 18.0) < 1e-10
    dry = np.full(3, 1.1)
    assert area(clip_constraints(np.vstack((0.85 - dry, p - dry)))) == 0
    return ["18m2_full_native_face", "shared_positive_width_edge", "zero_width_contact_rejected",
            "synthetic_h_minus2_65_p2_1_face18m2_and_1m_raise_keeps_1_1m_draft",
            "synthetic_h1_1_p2_1_face_has_zero_subsea_overlap"]


def exact_wet_support(h: np.ndarray, p: np.ndarray, f: np.ndarray) -> np.ndarray:
    # Verbatim semantics of EV72 verify.py::exact_wet_support, evaluated on supplied arrays.
    corners = OFFSETS
    hv = [h[dr:dr + 2047, dc:dc + 2047] for dr, dc in corners]
    nominal = np.fmax(p, SEA_MAX)
    visible = np.where(np.isfinite(p)[:, :, None], f, SEA_MAX)
    support = np.zeros(h.shape, dtype=bool)
    for ids in FACES:
        wet = np.logical_or.reduce([(nominal > hv[i]) | (visible[:, :, i] > hv[i]) for i in ids])
        for i in ids:
            dr, dc = corners[i]
            support[dr:dr + 2047, dc:dc + 2047] |= wet
    return support


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    checks = control_checks()
    with np.load(TERRAIN) as z:
        t = {k: z[k] for k in z.files}
    with np.load(CONSTRAINTS) as z:
        q = {k: z[k] for k in z.files}
    h = t["heights"].astype(np.float64)
    cls = t["cls"]
    p = np.load(PFILE)
    f = np.load(FFILE)
    assert h.shape == (2048, 2048) and p.shape == (2047, 2047) and f.shape == (2047, 2047, 4)

    # A water piece is cell-wide: qualify a cell if any corner has an inland pond class.
    inland = np.zeros_like(p, dtype=bool)
    for dr, dc in OFFSETS:
        inland |= np.isin(cls[dr:dr + 2047, dc:dc + 2047], POND_CLASSES)
    finite_p = np.isfinite(p)
    low = np.minimum.reduce((h[:-1, :-1], h[:-1, 1:], h[1:, :-1], h[1:, 1:]))
    high = np.maximum.reduce((h[:-1, :-1], h[:-1, 1:], h[1:, :-1], h[1:, 1:]))
    # Include fully submerged faces too; no high-corner/orilla-crossing predicate.
    cell = finite_p & inland & (p > SEA_NOMINAL) & (low < SEA_MAX)
    rr, cc = np.nonzero(cell)
    n = len(rr)
    ground = np.stack((h[rr, cc], h[rr, cc + 1], h[rr + 1, cc], h[rr + 1, cc + 1]), axis=1)
    class_values = np.stack([cls[rr + dr, cc + dc] for dr, dc in OFFSETS], axis=1)
    masks = {name: np.stack([t[name][rr + dr, cc + dc] for dr, dc in OFFSETS], axis=1).astype(bool)
             for name in ("reserve", "platform", "narva", "water", "beach")}
    protection_names = ("fixed", "allowed", "target", "water_support", "released_dry", "other_fixed", "large_lake_banks")
    mask_arrays = {**{name: t[name] for name in masks}, **{name: q[name] for name in protection_names}}

    # constraints are positive in the relevant interior. The first candidate domain
    # catches any locally inherited sea/pond overlap; separate areas report nominal and max sea.
    constraints = np.stack((SEA_MAX - ground, p[rr, cc, None] - ground), axis=1)
    area_groups = ("nominal_0_65", "max_0_85", "tide_only_plane_band")
    areas = np.zeros((n, 2, len(area_groups)), dtype=np.float64)
    raised_good = np.zeros((n, 2), dtype=np.float64)
    raised_good_nominal = np.zeros((n, 2), dtype=np.float64)
    active_poly = np.empty((n, 2), dtype=object)
    active_constraints = np.zeros((n, 2, 2, 3), dtype=np.float64)
    active = np.zeros((n, 2), dtype=bool)
    centers = np.zeros((n, 2, 2), dtype=np.float64)
    xz_corners = np.stack((np.c_[cc * 6, 12282 - rr * 6],
                           np.c_[cc * 6 + 6, 12282 - rr * 6],
                           np.c_[cc * 6, 12282 - rr * 6 - 6],
                           np.c_[cc * 6 + 6, 12282 - rr * 6 - 6]), axis=1)
    for i in range(n):
        plane = p[rr[i], cc[i]]
        raised = np.maximum(ground[i], RAISED_BED)
        for fi, slots in enumerate(FACES):
            vals = constraints[i][:, slots]
            poly = clip_constraints(vals)
            if plane > SEA_NOMINAL:
                nominal_poly = clip_constraints(np.vstack((SEA_NOMINAL - ground[i, slots], plane - ground[i, slots])))
                areas[i, fi, 0] = area(nominal_poly)
                nominal_good = clip_constraints(np.vstack((SEA_NOMINAL - ground[i, slots],
                                                           plane - ground[i, slots],
                                                           plane - DRAFT - raised[list(slots)])))
                raised_good_nominal[i, fi] = area(nominal_good)
                if plane > SEA_MAX:
                    max_poly = clip_constraints(np.vstack((SEA_MAX - ground[i, slots], plane - ground[i, slots])))
                    areas[i, fi, 1] = area(max_poly)
                else:
                    # Pond plane lies inside the inherited sea band; count as tide-band only.
                    areas[i, fi, 2] = area(poly)
            active_poly[i, fi] = poly
            if len(poly) and area(poly) > 1e-9:
                active[i, fi] = True
                # Water after raising the bottom is >=0.95m exactly where this half-plane is positive.
                good = clip_constraints(np.vstack((vals, plane - DRAFT - raised[list(slots)])))
                raised_good[i, fi] = area(good)
                xyz = np.c_[xz_corners[i, slots, 0], ground[i, slots], xz_corners[i, slots, 1]]
                centers[i, fi] = np.mean(poly @ xyz[:, (0, 2)], axis=0)
                active_constraints[i, fi] = vals

    # Build components from positive-area native face fragments, joining only where
    # their strict overlap intervals share positive width.
    local = np.full((n, 2), -1, dtype=np.int32)
    local[active] = np.arange(active.sum())
    lookup = np.full(p.shape, -1, dtype=np.int32)
    lookup[rr, cc] = np.arange(n)
    pair_list = []

    def add(a, b, yes):
        ok = (a >= 0) & (b >= 0) & yes
        if ok.any():
            pair_list.append(np.c_[a[ok], b[ok]])

    add(local[:, 0], local[:, 1], shared(active_constraints[:, 0][:, :, [0, 2]], active_constraints[:, 1][:, :, [0, 2]]))
    for axis in ("east", "south"):
        possible = cc < p.shape[1] - 1 if axis == "east" else rr < p.shape[0] - 1
        src = np.flatnonzero(possible)
        dst = lookup[rr[src] + (axis == "south"), cc[src] + (axis == "east")]
        keep = dst >= 0
        src, dst = src[keep], dst[keep]
        sa, sb, fa, fb = ([1, 2], [0, 1], 0, 1) if axis == "east" else ([1, 2], [0, 1], 1, 0)
        a = active_constraints[src, fa][:, :, sa]
        b = active_constraints[dst, fb][:, :, sb]
        add(local[src, fa], local[dst, fb], shared(a, b))
    pairs = np.concatenate(pair_list) if pair_list else np.empty((0, 2), dtype=np.int32)
    nodes = int(active.sum())
    graph = coo_matrix((np.ones(len(pairs), np.uint8), (pairs[:, 0], pairs[:, 1])), shape=(nodes, nodes)).tocsr()
    count, labels = connected_components(graph, directed=False) if nodes else (0, np.empty(0, dtype=np.int32))
    area_per_node = (active_poly[active]).astype(object)
    node_areas = np.array([area(poly) for poly in area_per_node], dtype=float)
    totals = np.bincount(labels, weights=node_areas, minlength=count) if count else np.zeros(0)
    comp_area_groups = np.zeros((count, len(area_groups)), dtype=float)
    comp_good = np.zeros(count, dtype=float)
    comp_bad = np.zeros(count, dtype=float)
    comp_masks = {name: np.zeros(count, dtype=bool) for name in mask_arrays}
    comp_classbits = np.zeros(count, dtype=np.uint16)
    active_ids = np.flatnonzero(active)
    for node, flat in enumerate(active_ids):
        i, fi = np.unravel_index(flat, active.shape)
        lab = labels[node]
        comp_area_groups[lab] += areas[i, fi]
        comp_good[lab] += raised_good[i, fi]
        comp_bad[lab] += max(0.0, node_areas[node] - raised_good[i, fi])
        slots = FACES[fi]
        for slot in slots:
            dr, dc = OFFSETS[slot]
            for name, mask in mask_arrays.items():
                comp_masks[name][lab] |= bool(mask[rr[i] + dr, cc[i] + dc])
            comp_classbits[lab] |= np.uint16(1 << int(cls[rr[i] + dr, cc[i] + dc]))

    support = exact_wet_support(h, p, f)
    face_support = np.zeros((n, 2), dtype=bool)
    for fi, slots in enumerate(FACES):
        face_support[:, fi] = np.logical_or.reduce([
            support[rr + OFFSETS[k][0], cc + OFFSETS[k][1]] for k in slots
        ])
    eligible_nodes = active
    eligible_faces = int(active.sum())
    protected_faces = int((active & face_support).sum())
    mutable_candidate_vertices = 0
    candidate_vertex_set = set()
    for i, fi in zip(*np.nonzero(active)):
        for slot in FACES[fi]:
            dr, dc = OFFSETS[slot]
            candidate_vertex_set.add((int(rr[i] + dr), int(cc[i] + dc)))
    for r, c in candidate_vertex_set:
        if not support[r, c]:
            mutable_candidate_vertices += 1

    face_mask_coverage = {}
    active_r, active_f = np.nonzero(active)
    active_areas = np.array([area(active_poly[i, fi]) for i, fi in zip(active_r, active_f)])
    for name, mask in mask_arrays.items():
        any_vertex = np.zeros(len(active_r), dtype=bool)
        all_vertices = np.ones(len(active_r), dtype=bool)
        for slot in FACES[0]:
            dr, dc = OFFSETS[slot]
            values = mask[rr[active_r] + dr, cc[active_r] + dc]
            any_vertex |= values
            all_vertices &= values
        # Face 1 has a different corner set; replace using its own incidence for each row.
        face_any = np.zeros(len(active_r), dtype=bool)
        face_all = np.zeros(len(active_r), dtype=bool)
        for j, (i, fi) in enumerate(zip(active_r, active_f)):
            vals = [bool(mask[rr[i] + OFFSETS[slot][0], cc[i] + OFFSETS[slot][1]]) for slot in FACES[fi]]
            face_any[j] = any(vals)
            face_all[j] = all(vals)
        face_mask_coverage[name] = dict(
            candidate_faces_any_vertex=int(face_any.sum()), candidate_faces_all_vertices=int(face_all.sum()),
            overlap_area_any_vertex_m2=float(active_areas[face_any].sum()),
            overlap_area_all_vertices_m2=float(active_areas[face_all].sum()))

    narva_r, narva_c = 898, 402  # cell containing the reviewed bridge point x=2417,z=6890
    narva_i = int(lookup[narva_r, narva_c])
    narva_faces = []
    if narva_i >= 0:
        for fi, slots in enumerate(FACES):
            comp = int(labels[local[narva_i, fi]]) if active[narva_i, fi] else None
            narva_faces.append(dict(face=fi, active=bool(active[narva_i, fi]), component=comp,
                                    area_m2=float(area(active_poly[narva_i, fi])),
                                    raised_ge_0_95_draft_m2=float(raised_good[narva_i, fi])))
    narva_bridge = dict(x=2417, z=6890, cell_row=narva_r, cell_col=narva_c,
                        cell_height_corners_m=h[narva_r:narva_r + 2, narva_c:narva_c + 2].tolist(),
                        cell_class_corners=cls[narva_r:narva_r + 2, narva_c:narva_c + 2].tolist(),
                        P_m=float(p[narva_r, narva_c]), F_corners_m=f[narva_r, narva_c].tolist(),
                        masks={name: bool(mask[narva_r, narva_c]) for name, mask in mask_arrays.items()}, faces=narva_faces)

    rows = []
    for k in range(count):
        incident = np.flatnonzero(labels == k)
        points = np.array([centers[np.unravel_index(active_ids[x], active.shape)] for x in incident])
        center = np.average(points, axis=0, weights=node_areas[incident])
        item = dict(component=int(k), area_m2=float(totals[k]), x=float(center[0]), z=float(center[1]),
                    nominal_0_65_m2=float(comp_area_groups[k, 0]), max_0_85_m2=float(comp_area_groups[k, 1]),
                    tide_only_plane_band_m2=float(comp_area_groups[k, 2]),
                    raised_to_1m_ge_0_95_draft_m2=float(comp_good[k]),
                    raised_to_1m_below_0_95_draft_m2=float(comp_bad[k]),
                    touches_reserve_vertex=bool(comp_masks["reserve"][k]),
                    touches_platform_vertex=bool(comp_masks["platform"][k]),
                    touches_narva_vertex=bool(comp_masks["narva"][k]),
                    touches_water_mask_vertex=bool(comp_masks["water"][k]),
                    touches_beach_vertex=bool(comp_masks["beach"][k]),
                    touches_fixed_vertex=bool(comp_masks["fixed"][k]),
                    touches_allowed_vertex=bool(comp_masks["allowed"][k]),
                    touches_target_vertex=bool(comp_masks["target"][k]),
                    touches_water_support_vertex=bool(comp_masks["water_support"][k]),
                    touches_released_dry_vertex=bool(comp_masks["released_dry"][k]),
                    touches_other_fixed_vertex=bool(comp_masks["other_fixed"][k]),
                    touches_large_lake_bank_vertex=bool(comp_masks["large_lake_banks"][k]),
                    incident_classes=','.join(str(j) for j in range(8) if comp_classbits[k] & (1 << j)),
                    exact_wet_faces=int(np.count_nonzero(face_support[active] [labels == k])))
        rows.append(item)
    rows.sort(key=lambda r: -r["area_m2"])
    with (OUT / "components.csv").open("w", newline="", encoding="utf-8") as fcsv:
        writer = csv.DictWriter(fcsv, fieldnames=list(rows[0]) if rows else ["component"])
        writer.writeheader()
        writer.writerows(rows)

    summary = dict(
        status="GEOMETRIC_CENSUS_NOT_RENDER_VERDICT",
        assumptions={"sea_nominal_m": SEA_NOMINAL, "sea_max_m": SEA_MAX,
                     "source": "inherited prompt values; not verified current engine tide/sea contract",
                     "raised_bed_m": RAISED_BED, "required_draft_m": DRAFT},
        inputs={str(path): sha(path) for path in (TERRAIN, PFILE, FFILE, CONSTRAINTS)},
        shapes={"terrain": list(h.shape), "plane": list(p.shape), "visible_field": list(f.shape)},
        terrain_class_counts={str(int(k)): int(v) for k, v in zip(*np.unique(cls, return_counts=True))},
        mask_vertex_counts={name: int(mask.sum()) for name, mask in mask_arrays.items()},
        protection_mask_face_coverage=face_mask_coverage,
        domain=dict(candidate_cells=int(n), active_native_faces=int(active.sum()), components=int(count),
                    components_with_nominal_overlap=int(np.count_nonzero(comp_area_groups[:, 0] > 1e-6)),
                    components_with_max_sea_overlap=int(np.count_nonzero(comp_area_groups[:, 1] > 1e-6)),
                    max_sea_components_touching_narva=int(np.count_nonzero((comp_area_groups[:, 1] > 1e-6) & comp_masks["narva"])),
                    max_sea_components_not_touching_narva=int(np.count_nonzero((comp_area_groups[:, 1] > 1e-6) & ~comp_masks["narva"])),
                    positive_width_connections=int(len(pairs)), area_m2=float(totals.sum()),
                    nominal_sea_overlap_m2=float(areas[:, :, 0].sum()),
                    max_sea_overlap_m2=float(areas[:, :, 1].sum()),
                    tide_only_plane_band_m2=float(areas[:, :, 2].sum())),
        raise_to_1m=dict(undersea_overlap_m2=float(totals.sum()),
                         preserves_at_least_0_95_draft_m2=float(comp_good.sum()),
                         below_0_95_draft_m2=float(comp_bad.sum()),
                         max_sea_overlap_preserves_at_least_0_95_draft_m2=float(comp_good.sum()),
                         max_sea_overlap_below_0_95_draft_m2=float(areas[:, :, 1].sum() - comp_good.sum()),
                         nominal_overlap_preserves_at_least_0_95_draft_m2=float(raised_good_nominal.sum()),
                         nominal_overlap_below_0_95_draft_m2=float(areas[:, :, 0].sum() - raised_good_nominal.sum()),
                         face_count_ge_0_95=int(np.count_nonzero((raised_good >= 18.0 - 1e-9) & active)),
                         face_count_partial_ge_0_95=int(np.count_nonzero((raised_good > 1e-9) & (raised_good < 18.0 - 1e-9) & active)),
                         face_count_no_ge_0_95=int(np.count_nonzero((raised_good <= 1e-9) & active))),
        ev72_gate=dict(source=str(VERIFY), active_candidate_faces=eligible_faces,
                       protected_candidate_faces=protected_faces,
                       unprotected_candidate_faces=eligible_faces - protected_faces,
                       candidate_incident_vertices=len(candidate_vertex_set),
                       mutable_candidate_vertices=mutable_candidate_vertices,
                       expected_mutable_face_area_m2=0.0 if protected_faces == eligible_faces else None),
        narva_bridge_cell=narva_bridge,
        largest_components=rows[:25], checks=checks, seconds=time.monotonic() - started,
        limits=["P is treated as the physical pond plane and F as visible field, following the EV72 verifier; F is not substituted for geometric draft.",
                "Mask tags mean at least one incident vertex, not that the full polygon lies inside a protected region.",
                "Interior-water classification is cell-wide if any corner class is in 2,3,5,6,7; pure class 1 / delta 4 cells are excluded. Faces fully below the sea cut are included; no shoreline-crossing predicate is used.",
                "Strict positive half-plane clipping assumes linear height over native NW-SE faces.",
                "EV72 exact_wet_support is reported only as the current candidate's mutation gate; it is not used to define or diagnose the submerged-water domain.",
                "Sea 0.65/0.85 are inherited values, not current engine measurements; visual manifestation is unproven.",
                "No source, terrain, plane, F, objects, package or game process was modified."])
    (OUT / "census.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "largest_components"}, indent=2))


if __name__ == "__main__":
    main()
