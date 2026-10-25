"""G3: after the patch, the overlap strips of neighbouring tiles hold the same pixels.

Tiles overlap by 128 px (step 384 of 512). For every pair of horizontal, vertical and diagonal neighbours with at least
one tile of the manifest or of the independent zone (gate_lib.tiles_touched), compare the shared region of the final layers: patched PNG where the tool changed the layer, else the
shipped source PNG (the one whose PAA is the shipped EV95 entry). PASS iff every shared region is identical (s and m).
Non-vacuity: number of compared regions that hold patched pixels. Informational: the same comparison on the entries of the FINAL PACKED PBO decoded with ImageToPAA.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gate_lib import (target_terrain, EV95_PBO, FINAL_PBO, PATCH, Pbo, World, decode_bytes, domain_cells, layer_entry,  # noqa: E402
                      load_png, manifest, source_png, stems, tiles_touched, verdict)


def main():
    m = manifest()
    patched = {tuple(r["tile"]): r for r in m["records"]}
    pbo, final = Pbo(EV95_PBO), Pbo(str(FINAL_PBO))
    dom, _ = domain_cells(World(target_terrain()))
    centre = sorted(set(patched) | set(tiles_touched(dom, zone=True)))
    cache = {}

    def layer(ab, p):
        if (ab, p) not in cache:
            stem = stems(*ab)[p]
            rec = patched.get(ab)
            if rec and rec["layers"][p]["changed_px"]:
                cache[(ab, p)] = load_png(PATCH / "layers" / f"{stem}.png")
            else:
                src = source_png(stem, pbo.read(f"data/layers/{stem}.paa"), wide=True)
                assert src is not None, stem
                cache[(ab, p)] = load_png(src)
        return cache[(ab, p)]

    def shipped(ab, p):
        stem = stems(*ab)[p]
        return load_png(source_png(stem, pbo.read(f"data/layers/{stem}.paa"), wide=True))

    def decoded(ab, p):
        return decode_bytes(final.read(layer_entry(stems(*ab)[p])))

    pairs = set()
    for a, b in centre:
        for da in (-1, 0, 1):
            for db in (-1, 0, 1):
                n = (a + da, b + db)
                if (da or db) and 0 <= n[0] < 32 and 0 <= n[1] < 32:
                    pairs.add(tuple(sorted([(a, b), n])))
    rows, ok, dec_bad = [], True, 0
    for t1, t2 in sorted(pairs):
        da, db = t2[0] - t1[0], t2[1] - t1[1]
        # region of t1 shared with t2, and the same region in t2's pixels
        s1 = (slice(384, 512) if db == 1 else slice(0, 128) if db == -1 else slice(0, 512),
              slice(384, 512) if da == 1 else slice(0, 128) if da == -1 else slice(0, 512))
        s2 = (slice(0, 128) if db == 1 else slice(384, 512) if db == -1 else slice(0, 512),
              slice(0, 128) if da == 1 else slice(384, 512) if da == -1 else slice(0, 512))
        for p in ("s", "m"):
            diff = int((layer(t1, p)[s1] != layer(t2, p)[s2]).any(-1).sum())
            ddiff = int((decoded(t1, p)[s1] != decoded(t2, p)[s2]).any(-1).sum())
            touched = int((layer(t1, p)[s1] != shipped(t1, p)[s1]).any(-1).sum())
            rows.append(dict(pair=[list(t1), list(t2)], layer=p, png_diff_px=diff, paa_decoded_diff_px=ddiff,
                             patched_px_in_shared_region=touched))
            ok &= diff == 0
            dec_bad += ddiff
    ok &= len(pairs) > 0
    verdict("G3_overlaps", ok, dict(centre_tiles=[list(t) for t in centre], pairs=len(pairs), comparisons=len(rows),
                                     png_bad=sum(r["png_diff_px"] > 0 for r in rows),
                                     comparisons_with_patched_px_in_shared_region=sum(r["patched_px_in_shared_region"] > 0 for r in rows),
                                     patched_px_in_shared_regions=sum(r["patched_px_in_shared_region"] for r in rows),
                                     paa_decoded_diff_px_informational=dec_bad, rows=rows))


if __name__ == "__main__":
    main()
