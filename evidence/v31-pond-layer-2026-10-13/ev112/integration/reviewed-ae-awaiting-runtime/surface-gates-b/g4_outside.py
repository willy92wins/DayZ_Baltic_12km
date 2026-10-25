"""G4: nothing changes outside the affected cells dilated by 2 px, judged on the final packed PBO.

Zone (gate_lib, reimplemented): the domain cells of G2 dilated by 2 px (Chebyshev), in world pixels.
Tiles examined: every tile the zone touches (derived from the domain alone) plus every tile in the manifest.
  PNG: patched layer (manifest PNG where the tool changed it, else the source) vs shipped source PNG; changed pixels
       outside the zone must be 0.
  PAA: the entry of the FINAL PACKED PBO vs the EV95 entry, both decoded with ImageToPAA (top mip); a changed pixel
       outside the zone is explained when its 4x4 DXT block also holds zone pixels (DXT encodes per block);
       unexplained must be 0.
  Entries: every other entry of the final PBO (all tiles the zone does not touch, config, rvmats, texHeaders...) must be
       byte-identical to EV95, except baltic_trial.wrp (the compiled terrain, bound by G5).
Informational: ImageToPAA on the shipped source PNG reproduces the shipped PAA bytes (encoder determinism/provenance).
PASS iff PNG outside = 0, PAA unexplained = 0 and no entry outside the examined tiles differs from EV95.
"""
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gate_lib import (target_terrain, EV95_PBO, FINAL_PBO, GATES, I2P, PATCH, Pbo, World, decode_bytes, domain_cells,  # noqa: E402
                      layer_entry, load_png, manifest, sha, source_png, stems, tile_zone, tiles_touched, verdict)


from surface_scope_b import allowed_zone, expected_tiles

def main():
    m = manifest()
    world = World(target_terrain())
    dom, _ = domain_cells(world)
    zone_tiles = expected_tiles(dom)
    recs = {tuple(r["tile"]): r for r in m["records"]}
    tiles = sorted(set(zone_tiles) | set(recs))
    ev95, final = Pbo(EV95_PBO), Pbo(str(FINAL_PBO))
    assert set(final.index) == set(ev95.index), "entry names differ from EV95"
    rows, png_out, paa_expl, paa_unexpl, reenc_same, reenc_n = [], 0, 0, 0, 0, 0
    (GATES / "g4" / "reencode").mkdir(parents=True, exist_ok=True)
    examined = set()
    for a, b in tiles:
        for p, stem in stems(a, b).items():
            zone = allowed_zone(dom, a, b, p)
            zblock = np.repeat(np.repeat(zone.reshape(128, 4, 128, 4).any(axis=(1, 3)), 4, 0), 4, 1)
            entry = layer_entry(stem)
            examined.add(entry)
            shipped = ev95.read(entry)
            src = source_png(stem, shipped)
            assert src is not None, stem
            base = load_png(src)
            rec = recs.get((a, b))
            new = load_png(PATCH / "layers" / f"{stem}.png") if rec and rec["layers"][p]["changed_px"] else base
            changed = (new != base).any(-1)
            out_png = int((changed & ~zone).sum())
            row = dict(tile=[a, b], layer=p, in_manifest=rec is not None, zone_px=int(zone.sum()),
                       changed_in_zone=int((changed & zone).sum()), changed_outside_zone_png=out_png)
            fin = final.read(entry)
            row["final_entry_differs_from_ev95"] = fin != shipped
            if fin != shipped:
                dch = (decode_bytes(fin) != decode_bytes(shipped)).any(-1)
                expl = int((dch & ~zone & zblock).sum())
                unexpl = int((dch & ~zone & ~zblock).sum())
                row.update(paa_changed_in_zone=int((dch & zone).sum()), paa_changed_outside_explained=expl,
                           paa_changed_outside_unexplained=unexpl)
                paa_expl += expl
                paa_unexpl += unexpl
            out = GATES / "g4" / "reencode" / f"{stem}.paa"
            if not out.exists():
                subprocess.run([I2P, str(src), str(out)], capture_output=True, check=True)
            same = out.read_bytes() == shipped
            row["reencoded_source_equals_shipped"] = same
            reenc_same += same
            reenc_n += 1
            png_out += out_png
            rows.append(row)
    others = sorted(k for k in ev95.index if k not in examined and k != "baltic_trial.wrp"
                    and final.read(k) != ev95.read(k))
    ok = png_out == 0 and paa_unexpl == 0 and not others and len(zone_tiles) > 0
    verdict("G4_outside_zone", ok, dict(
        zone_tiles=[list(t) for t in zone_tiles], manifest_tiles_not_in_zone=[list(t) for t in recs if t not in zone_tiles],
        examined_entries=len(examined), final_pbo=str(FINAL_PBO), final_pbo_sha256=sha(FINAL_PBO),
        entries_outside_examined_tiles_checked=len(ev95.index) - len(examined) - 1,
        entries_outside_examined_tiles_differing_from_ev95=others,
        png_changed_outside_zone=png_out, paa_changed_outside_zone_explained_by_dxt_block=paa_expl,
        paa_changed_outside_zone_unexplained=paa_unexpl, png_changed_in_zone=sum(x["changed_in_zone"] for x in rows),
        reencoded_source_equals_shipped=f"{reenc_same}/{reenc_n}", rows=rows))


if __name__ == "__main__":
    main()
