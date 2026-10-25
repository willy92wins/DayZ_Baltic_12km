"""G2: on the lowered cells that carried road paint, the final layers must equal a render with no road paint at all.

Domain D (reimplemented in gate_lib): native cells with a corner > 0.5 m below EV95 (40c174e3) on the target terrain,
holding a pixel centre within 3.5 m of a road chain sample that was dry on the EV95 terrain and plane (paint, not bed).
Coverage: the tiles checked are every tile holding a D pixel, derived from D alone (gate_lib.tiles_touched), never from
the manifest; a required tile missing from the manifest is a FAIL by itself and its layers are taken as shipped.
Reference REF: build_surface_v30.tile() on the target terrain and water plane with the EV95 flags and the road tree
replaced by one point 10,000 km away, so no pixel is road; it never uses --road-off-lowered or lowered_cells().
Checks on each candidate, per tile:
  mask   PNG: RGBA equal to REF on every D pixel.
         PAA (decoded with ImageToPAA): slot equal to REF on every D pixel, except pixels of 4x4 DXT blocks whose
         encoded PNG holds 3 or 4 different slots (two DXT endpoints cannot hold three pure colours).
  sat    PNG: RGB equal to REF on D pixels with no road pixel outside the lowered cells within 3 px (the 0.8 px blur of
         build_surface_v30.py:218 reaches 3 px; nearer pixels carry the approach paint legitimately; reported apart).
         PAA: on those pixels where the unpatched source differs from REF by L1 >= 30, the decoded value is closer (L1)
         to REF than to the unpatched source.
Candidates: P1 patched PNG (the manifest PNG where the tool changed the layer, else the shipped source PNG) and P2 the
PAA entry READ FROM THE FINAL PACKED PBO must pass; N1 unpatched source PNG, N2 shipped EV109 PAA and N3 a composite
whose zone takes a regeneration WITHOUT the option (road paint reintroduced) must fail. PASS iff coverage holds and all
five candidates behave as stated.
"""
import hashlib
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from scipy.ndimage import maximum_filter
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gate_lib import (target_terrain, CACHE, EV109_PBO, EV95_PBO, FINAL_PBO, FLAGS, PATCH, PY, TOOLS, Pbo, World,  # noqa: E402
                      decode_bytes, domain_cells, layer_entry, load_png, manifest, sha, slot_of, source_png, stems,
                      tile_domain, tile_zone, tiles_touched, verdict)


from surface_scope_b import clearing_binding

def _init(terrain, out, plane, plane_sha):
    sys.path.insert(0, str(TOOLS))
    import build_surface_v30 as bsv
    bsv.init(terrain, out, "depth-all", "flowing", "gravel", "smooth", 1.0, plane, plane_sha,
             clearings_path=clearing_binding()["path"], clearings_sha256=clearing_binding()["sha256"])
    bsv.G["roads"] = cKDTree(np.array([[-1e7, -1e7]]))


def _tile(ab):
    import build_surface_v30 as bsv
    return bsv.tile(ab)[:2]


def missing(folder, tiles):
    return [t for t in tiles if not all((folder / "layers" / f"{s}.png").exists() for s in stems(*t).values())]


def render_reference(m, tiles, ref):
    todo = missing(ref, tiles)
    if todo:
        (ref / "layers").mkdir(parents=True, exist_ok=True)
        with Pool(2, initializer=_init, initargs=(target_terrain(), str(ref / "layers"), m["water_plane"],
                                                  m["water_plane_sha256"])) as pool:
            pool.map(_tile, todo)
    assert not missing(ref, tiles)


def render_roadon(m, tiles, roadon):
    todo = missing(roadon, tiles)
    if todo:
        cmd = [PY, "-I", "-B", str(TOOLS / "build_surface_v30.py"), target_terrain(), str(roadon), "--tiles",
               ";".join(f"{a},{b}" for a, b in todo), "--workers", "2", *FLAGS,
               "--water-plane", m["water_plane"], "--water-plane-sha256", m["water_plane_sha256"]]
        cb = clearing_binding()
        cmd += ["--forest-clearings", cb["path"], "--forest-clearings-sha256", cb["sha256"]]
        r = subprocess.run(cmd, capture_output=True, text=True)
        assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
    assert not missing(roadon, tiles)


def block_mixed(slot):
    """True on pixels of 4x4 blocks holding three or more different slots."""
    h, w = slot.shape
    blocks = slot.reshape(h // 4, 4, w // 4, 4).transpose(0, 2, 1, 3).reshape(h // 4, w // 4, 16)
    n = np.zeros((h // 4, w // 4), int)
    for k in range(4):
        n += (blocks == k).any(-1)
    return np.repeat(np.repeat(n >= 3, 4, 0), 4, 1)


def l1(u, v):
    return np.abs(u[..., :3].astype(int) - v[..., :3].astype(int)).sum(-1)


def main():
    m = manifest()
    world = World(target_terrain())
    dom, near_wet_only = domain_cells(world)
    required = tiles_touched(dom, zone=False)
    listed = {tuple(t) for t in m["tiles"]}
    not_listed = [list(t) for t in required if t not in listed]
    key = f"{sha(target_terrain())[:12]}-{m['water_plane_sha256'][:12]}-{clearing_binding()['sha256'][:12]}"
    ref_dir, roadon_dir = CACHE / f"ref-noroad-{key}", CACHE / f"regen-roadon-{key}"
    render_reference(m, required, ref_dir)
    render_roadon(m, required, roadon_dir)
    ev95, ev109, final = Pbo(EV95_PBO), Pbo(EV109_PBO), Pbo(str(FINAL_PBO))
    recs = {tuple(r["tile"]): r for r in m["records"]}
    cand = {k: dict(mask_bad=0, sat_bad=0, sat_checked=0) for k in ("P1_patched_png", "P2_final_pbo_paa", "N1_source_png",
                                                                       "N2_shipped_ev109_paa", "N3_road_reintroduced_png")}
    per_tile, totals = [], dict(domain_px=0, sat_comparable_px=0, blur_band_px=0, paa_mask_excused_px=0,
                                discriminating_px=0, source_road_px_in_domain=0, painted_not_slot0_in_source=0)
    for a, b in required:
        f = world.fields(a, b, pad=3)
        D = tile_domain(dom, a, b)
        roadon_px = f["road"] & ~f["low"]
        near_roadon = maximum_filter(roadon_px, size=7)[3:-3, 3:-3]
        C = D & ~near_roadon
        zone = tile_zone(dom, a, b)
        painted = f["painted"][3:-3, 3:-3]
        row = dict(tile=[a, b], in_manifest=(a, b) in listed, domain_px=int(D.sum()), sat_comparable_px=int(C.sum()),
                   blur_band_px=int((D & near_roadon).sum()))
        for p, stem in stems(a, b).items():
            entry = layer_entry(stem)
            src_path = source_png(stem, ev95.read(entry))
            assert src_path is not None, stem
            src = load_png(src_path)
            ref = load_png(ref_dir / "layers" / f"{stem}.png")
            rec = recs.get((a, b))
            changed = bool(rec and rec["layers"][p]["changed_px"])
            pat = load_png(PATCH / "layers" / f"{stem}.png") if changed else src
            fin_bytes = final.read(entry)
            row[f"{p}_final_entry_sha256"] = hashlib.sha256(fin_bytes).hexdigest()
            pat_dec = decode_bytes(fin_bytes)
            ship_dec = decode_bytes(ev109.read(entry))
            n3 = src.copy()
            n3[zone] = load_png(roadon_dir / "layers" / f"{stem}.png")[zone]
            if p == "m":
                rs = slot_of(ref)
                for k, img in (("P1_patched_png", pat), ("N1_source_png", src), ("N3_road_reintroduced_png", n3)):
                    bad = int(((img != ref).any(-1) & D).sum())
                    cand[k]["mask_bad"] += bad
                    row[f"{k}_mask_bad"] = bad
                for k, img, enc in (("P2_final_pbo_paa", pat_dec, pat), ("N2_shipped_ev109_paa", ship_dec, src)):
                    excused = block_mixed(slot_of(enc))
                    bad = int(((slot_of(img) != rs) & D & ~excused).sum())
                    cand[k]["mask_bad"] += bad
                    row[f"{k}_mask_bad"] = bad
                    if k == "P2_final_pbo_paa":
                        totals["paa_mask_excused_px"] += int((D & excused & (slot_of(img) != rs)).sum())
                ss = slot_of(src)
                totals["source_road_px_in_domain"] += int((D & painted & (ss == 0)).sum())
                totals["painted_not_slot0_in_source"] += int((D & painted & (ss != 0)).sum())
            else:
                for k, img in (("P1_patched_png", pat), ("N1_source_png", src), ("N3_road_reintroduced_png", n3)):
                    bad = int(((img != ref).any(-1) & C).sum())
                    cand[k]["sat_bad"] += bad
                    cand[k]["sat_checked"] += int(C.sum())
                    row[f"{k}_sat_bad"] = bad
                Q = C & (l1(src, ref) >= 30)
                totals["discriminating_px"] += int(Q.sum())
                row["discriminating_px"] = int(Q.sum())
                for k, img in (("P2_final_pbo_paa", pat_dec), ("N2_shipped_ev109_paa", ship_dec)):
                    bad = int((Q & ~(l1(img, ref) < l1(img, src))).sum())
                    cand[k]["sat_bad"] += bad
                    cand[k]["sat_checked"] += int(Q.sum())
                    row[f"{k}_sat_bad"] = bad
        for k in ("domain_px", "sat_comparable_px", "blur_band_px"):
            totals[k] += row[k]
        per_tile.append(row)
    for k, v in cand.items():
        v["passes"] = v["mask_bad"] == 0 and v["sat_bad"] == 0
    coverage_ok = not not_listed and len(required) > 0 and all(r["domain_px"] > 0 for r in per_tile)
    ok = (coverage_ok and cand["P1_patched_png"]["passes"] and cand["P2_final_pbo_paa"]["passes"]
          and not cand["N1_source_png"]["passes"] and not cand["N2_shipped_ev109_paa"]["passes"]
          and not cand["N3_road_reintroduced_png"]["passes"]
          and totals["domain_px"] > 0 and totals["discriminating_px"] > 0)
    verdict("G2_road_paint", ok, dict(
        domain_cells=int(dom.sum()), lowered_cells=int(world.lowered.sum()),
        lowered_near_road_but_wet_in_ev95_cells=near_wet_only, required_tiles=[list(t) for t in required],
        manifest_tiles=len(listed), required_tiles_not_in_manifest=not_listed, coverage_ok=coverage_ok,
        final_pbo=str(FINAL_PBO), final_pbo_sha256=sha(FINAL_PBO), candidates=cand, totals=totals,
        note="pixel totals sum over tiles; overlapping tiles count shared pixels twice",
        reference_dir=str(ref_dir), roadon_dir=str(roadon_dir), target_terrain_sha256=sha(target_terrain()),
        per_tile=per_tile))


if __name__ == "__main__":
    main()
