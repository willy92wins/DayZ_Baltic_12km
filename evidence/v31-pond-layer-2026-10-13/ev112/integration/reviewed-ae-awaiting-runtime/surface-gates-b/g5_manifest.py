"""G5: the manifest lists exactly the changed layer entries, and the packed PBO carries exactly those bytes.

  a) manifest vs patch folder: every PAA in <patch>/layers whose bytes differ from the EV95 PBO entry is in the
     manifest, and nothing else; each manifest file exists with its recorded SHA256; each listed layer has a patched
     PNG that differs from its source, and no layer with an unchanged PNG is listed; the manifest tiles are exactly the
     tiles the zone touches, derived from the domain alone (gate_lib.tiles_touched), as the tool header promises;
     the EV95 PBO the gates read is the manifest base PBO (SHA256).
  b) payload binding, entry by entry, on the final packed PBO: for each manifest entry SHA256(PBO entry) ==
     manifest sha256 == SHA256(file) == SHA256(ImageToPAA(patched PNG)), so the bytes G2/G4 judged on the PNG side are
     the bytes shipped; package.json names this PBO and this manifest by hash.
  c) the packed PBO read back: same entry names and header properties as EV95 and as the shipped EV109; entries
     changed against EV95 == manifest entries + baltic_trial.wrp; against EV109 (EV95 + EV109 WRP, package_ev109.py)
     == manifest entries exactly.
  d) binding to the trusted target (review 2 of 15-10): the manifest terrain SHA256 (recorded and recomputed) equals the
     trusted terrain SHA256 given by the build chain, and the packed baltic_trial.wrp entry equals the trusted compiled WRP
     SHA256; the domain of a) is computed on the trusted terrain. c) against the previous shipped PBO (EV109) allows its
     WRP to differ when the trusted WRP is a new one.
PASS iff a), b), c) and d).
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gate_lib import (TARGET_TERRAIN_SHA, TARGET_WRP_SHA, target_terrain, EV109_PBO, EV95_PBO, FINAL_PBO, GATES, I2P, PACKAGE, PATCH, Pbo, World,  # noqa: E402
                      domain_cells, layer_entry, load_png, manifest, sha, source_png, stems, tiles_touched, verdict)


def h(data):
    return hashlib.sha256(data).hexdigest()


from surface_scope_b import expected_tiles

def main():
    m = manifest()
    ev95, ev109, new = Pbo(EV95_PBO), Pbo(EV109_PBO), Pbo(str(FINAL_PBO))
    listed = sorted(e["entry"] for e in m["entries"])
    assert listed == sorted(m["changed_entries"])
    files_ok = all(Path(e["file"]).exists() and sha(e["file"]) == e["sha256"] for e in m["entries"])
    differing, png_changed = [], []
    for f in sorted((PATCH / "layers").glob("*.paa")):
        entry = f"data/layers/{f.name.lower()}"
        if f.read_bytes() != ev95.read(entry):
            differing.append(entry)
    for r in m["records"]:
        for p, stem in stems(*r["tile"]).items():
            png = PATCH / "layers" / f"{stem}.png"
            if png.exists():
                src = source_png(stem, ev95.read(layer_entry(stem)))
                if not np.array_equal(load_png(png), load_png(src)):
                    png_changed.append(layer_entry(stem))
    dom, _ = domain_cells(World(target_terrain()))
    zone_tiles = expected_tiles(dom)
    manifest_tiles = sorted(tuple(t) for t in m["tiles"])
    tiles_ok = manifest_tiles == zone_tiles and sorted(tuple(r["tile"]) for r in m["records"]) == zone_tiles
    base_ok = sha(EV95_PBO) == m["base_pbo_sha256"]
    a_ok = files_ok and listed == sorted(differing) and listed == sorted(png_changed) and tiles_ok and base_ok

    same_names = set(new.index) == set(ev95.index) == set(ev109.index)
    binding, reenc_dir = [], GATES / "g5" / "reencode-patched"
    reenc_dir.mkdir(parents=True, exist_ok=True)
    for e in sorted(m["entries"], key=lambda e: e["entry"]):
        stem = Path(e["entry"]).stem
        out = reenc_dir / f"{stem}.paa"
        if out.exists():
            out.unlink()
        r = subprocess.run([I2P, str(PATCH / "layers" / f"{stem}.png"), str(out)], capture_output=True, text=True)
        reenc = h(out.read_bytes()) if r.returncode == 0 and out.exists() else None
        pbo_sha = h(new.read(e["entry"])) if e["entry"] in new.index else None
        file_sha = sha(e["file"]) if Path(e["file"]).exists() else None
        binding.append(dict(entry=e["entry"], manifest_sha256=e["sha256"], file_sha256=file_sha, pbo_entry_sha256=pbo_sha,
                            reencoded_patched_png_sha256=reenc,
                            ok=pbo_sha == e["sha256"] == file_sha == reenc))
    receipt_path = PACKAGE / "package.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8")) if receipt_path.exists() else {}
    receipt_ok = (receipt.get("pbo_sha256") == sha(FINAL_PBO) and receipt.get("manifest_sha256") == sha(PATCH / "manifest.json"))
    b_ok = same_names and all(x["ok"] for x in binding) and len(binding) == len(listed) and receipt_ok

    props_ok = new.props == ev95.props == ev109.props and bool(new.props)
    vs95 = sorted(k for k in ev95.index if new.read(k) != ev95.read(k)) if same_names else None
    vs109 = sorted(k for k in ev109.index if new.read(k) != ev109.read(k)) if same_names else None
    wrp_new = new.read("baltic_trial.wrp") if "baltic_trial.wrp" in new.index else b""
    prev_wrp_differs = same_names and wrp_new != ev109.read("baltic_trial.wrp")
    c_ok = (same_names and props_ok and vs95 == sorted(listed + ["baltic_trial.wrp"])
            and vs109 == sorted(listed + (["baltic_trial.wrp"] if prev_wrp_differs else [])))
    man_terrain_sha = m.get("terrain_sha256")
    man_terrain_now = sha(m["terrain"]) if Path(m["terrain"]).exists() else None
    wrp_sha = h(wrp_new)
    d_ok = (man_terrain_sha == TARGET_TERRAIN_SHA and man_terrain_now == TARGET_TERRAIN_SHA and wrp_sha == TARGET_WRP_SHA
            and receipt.get("wrp_from_sha256") is not None)

    verdict("G5_manifest", a_ok and b_ok and c_ok and d_ok, dict(
        trusted_terrain_sha256=TARGET_TERRAIN_SHA, manifest_terrain_sha256=man_terrain_sha, manifest_terrain_now_sha256=man_terrain_now,
        trusted_wrp_sha256=TARGET_WRP_SHA, packed_wrp_sha256=wrp_sha, prev_wrp_differs=prev_wrp_differs, d_ok=d_ok,
        manifest_entries=len(listed), paa_files_differing_from_ev95=len(differing), layers_with_changed_png=len(png_changed),
        files_ok=files_ok, ev95_pbo_is_manifest_base=base_ok, manifest_tiles=len(manifest_tiles), zone_tiles=len(zone_tiles), tiles_ok=tiles_ok, a_ok=a_ok,
        binding_ok=sum(x["ok"] for x in binding), binding_n=len(binding), receipt_ok=receipt_ok, b_ok=b_ok,
        package=str(FINAL_PBO), package_sha256=sha(FINAL_PBO), properties=new.props, properties_ok=props_ok,
        same_entry_names=same_names, changed_vs_ev95=vs95, changed_vs_ev109=vs109, c_ok=c_ok,
        unchanged_layers_not_listed=[f"{stems(*r['tile'])[p]}" for r in m["records"] for p in ("s", "m")
                                     if not r["layers"][p]["changed_px"]],
        binding=binding))


if __name__ == "__main__":
    main()
