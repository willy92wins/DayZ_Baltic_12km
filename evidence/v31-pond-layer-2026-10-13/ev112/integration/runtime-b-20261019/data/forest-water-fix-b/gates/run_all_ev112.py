"""EV112 forest prototype on the EV110 terrain: placement, every gate, negative controls, hold-out seeds and renders.
Logs and values in <F>/gates-run/, outputs in <F>/map-<seed>/ (F = ev112-wip/forest).

Usage: python -I run_all_ev112.py <step> [args]
  rasters      gate rasters from the inputs (grasters.py) and the Livonia bands (livonia_bands.py)
  place SEED [TAG]   whole map -> map-<TAG or SEED>/
  gates SEED   G1, G4, G5, G2/G3 per window, G7 per bog, G8, G9 (statistics + spacing), counts, the EV111 pilot squares with
               the unchanged r2 scripts (G1, G2 --dense A-reserva, G3, G4, G5, G7)
  g6 SEED      second whole-map run (map-<SEED>-b) and byte comparison; negative: region run seeds SEED / SEED + 1
  partition SEED   region runs with the production calibration: tile 400 (other seams) and halo 0 (negative)
  negatives SEED   negatives_map.py on a region of the production records
  holdout S1 S2 ...  run_regions.py on fresh seeds
  render SEED  the two pilot squares and three random 1 km windows (numpy default_rng(20261017) among the windows
               with >= 50 ha of forest floor) at 1 m/px"""
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gcfg  # noqa: E402

PY = sys.executable
F = gcfg.E / "ev112-wip/forest"
GR = F / "gates-run"
RAS = GR / "rasters"
BANDS = GR / "livonia-ev112-bands.json"
TOOL = gcfg.TOOL_DIR / "forest_v31.py"
GR.mkdir(parents=True, exist_ok=True)
NEG_REGION = "7678,5074,9278,7784"


def run(name, args, cwd=None):
    t = time.time()
    with (GR / f"{name}.log").open("w", encoding="utf-8") as f:
        p = subprocess.run([PY, "-I", "-B", *map(str, args)], stdout=f, stderr=subprocess.STDOUT, cwd=str(cwd or HERE))
    last = [ln for ln in (GR / f"{name}.log").read_text(encoding="utf-8").splitlines() if ln.strip()]
    print(f"{name:34s} rc {p.returncode} {time.time() - t:7.1f} s | {last[-1] if last else ''}", flush=True)
    return p.returncode


def place_args(seed, out, *extra):
    a = [TOOL, "--terrain", gcfg.TERRAIN, "--footprint", gcfg.FOOTPRINT, "--stage-wrp", gcfg.STAGE_WRP, "--pbo", gcfg.PBO]
    for d in gcfg.LAYER_DIRS:
        a += ["--layer-dir", d]
    return a + ["--cover", gcfg.LAYERS, "--reference", gcfg.REFERENCE, "--seed", seed, "--out", out, "--workers", "4", *extra]


step = sys.argv[1]
if step == "rasters":
    run("rasters", [HERE / "grasters.py", RAS])
    run("livonia-bands", [HERE / "livonia_bands.py", BANDS])
elif step == "place":
    seed = sys.argv[2]
    tag = sys.argv[3] if len(sys.argv) > 3 else seed
    run(f"place-{tag}", place_args(seed, F / f"map-{tag}"))
elif step == "gates":
    seed = sys.argv[2]
    M = F / f"map-{seed}"
    rec = M / "records.json"
    out = GR / f"map-{seed}"
    out.mkdir(exist_ok=True)
    run("g1", [HERE / "g1_map.py", rec, out / "g1-violations.json"])
    run("g4", [HERE / "g4g5_map.py", rec, "G4"])
    run("g5", [HERE / "g4g5_map.py", rec, "G5"])
    run("g2g3", [HERE / "g2g3_map.py", rec, RAS, BANDS, out / "g2g3-windows.json"])
    run("g7", [HERE / "g7_map.py", rec, RAS, out / "g7-bogs.json", "--livonia-bands", BANDS])
    run("g8", [HERE / "g8_agreement.py", rec, RAS, BANDS, out / "g8-windows.json"])
    run("g9", [HERE / "g9_seams.py", rec, "500", out / "g9.json"])
    run("counts", [HERE / "counts_map.py", rec, RAS, out / "counts.json"])
    sub = out / "pilot-subset.json"
    run("pilot-subset", [HERE / "pilot_subset.py", rec, sub])
    for g, args in (("pilot-r2-g1", ["g1.py", sub, "--json", out / "pilot-r2-g1.json"]),
                    ("pilot-r2-g2", ["g2_g3.py", sub, "G2", "--dense", "A-reserva", "--json", out / "pilot-r2-g2.json"]),
                    ("pilot-r2-g3", ["g2_g3.py", sub, "G3", "--json", out / "pilot-r2-g3.json"]),
                    ("pilot-r2-g4", ["g4.py", sub]), ("pilot-r2-g5", ["g5.py", sub]),
                    ("pilot-r2-g7", ["g7_bog.py", sub, "--json", out / "pilot-r2-g7.json"])):
        run(g, args, cwd=gcfg.R2_GATES)
elif step == "g6":
    seed = int(sys.argv[2])
    run("place-b", place_args(seed, F / f"map-{seed}-b"))
    run("g6", [HERE / "g6_compare.py", F / f"map-{seed}", F / f"map-{seed}-b"])
    reg = NEG_REGION
    run("g6neg-place-a", place_args(seed, F / f"g6neg/seed{seed}", "--region", reg))
    run("g6neg-place-b", place_args(seed + 1, F / f"g6neg/seed{seed + 1}", "--region", reg))
    run("g6-neg", [HERE / "g6_compare.py", F / f"g6neg/seed{seed}", F / f"g6neg/seed{seed + 1}"])
elif step == "partition":
    seed = sys.argv[2]
    cal = F / f"map-{seed}" / "report.json"
    reg = "6000,4000,9000,7000"
    run("partition-place-t400", place_args(seed, F / "partition/tile400", "--region", reg, "--tile", "400", "--calibration", cal))
    run("partition-place-halo0", place_args(seed, F / "partition/halo0", "--region", reg, "--halo", "0", "--calibration", cal))
    out = GR / f"map-{seed}"
    run("g9-partition", [HERE / "g9_seams.py", F / f"map-{seed}" / "records.json", "500", out / "g9-partition.json", "--region", reg,
                         "--compare", F / "partition/tile400/records.json", "--compare-tile", "400"])
    run("g9-neg-halo0", [HERE / "g9_seams.py", F / "partition/halo0/records.json", "500", out / "g9-neg-halo0.json", "--region", reg,
                         "--compare", F / f"map-{seed}" / "records.json", "--compare-tile", "500"])
elif step == "negatives":
    seed = sys.argv[2]
    run("negatives", [HERE / "negatives_map.py", F / f"map-{seed}" / "records.json", RAS, BANDS, GR / "neg", NEG_REGION])
    run("g8-neg-ev111-v2", [HERE / "g8_agreement.py", gcfg.F111 / "pilot-v3r2/records.json", RAS, BANDS, GR / "g8-neg-ev111-v2.json",
                            "--windows", "7678,5074;8278,6784;8178,5074;8778,6784"])
elif step == "holdout":
    seeds = sys.argv[2:]
    run("holdout-" + "-".join(seeds), [HERE / "run_regions.py", TOOL, F / ("holdout-" + "-".join(seeds)), RAS, BANDS, *seeds])
elif step == "render":
    seed = sys.argv[2]
    rec = F / f"map-{seed}" / "records.json"
    out = F / f"renders-{seed}"
    for sec in json.loads(gcfg.SECTORS.read_text(encoding="utf-8"))["sectors"]:
        p = np.asarray(sec["polygon_xz"], float)
        run(f"render-{sec['name']}", [HERE.parent / "render_v4.py", rec, out, sec["name"], int(p[:, 0].min()), int(p[:, 1].min()), 1000])
    g8 = json.loads((GR / f"map-{seed}" / "g8-windows.json").read_text(encoding="utf-8"))["windows"]
    cand = sorted((w["x0"], w["z0"]) for w in g8 if w["forest_ha"] >= 50)
    pick = np.random.default_rng(20261017).choice(len(cand), 3, replace=False)
    sel = [cand[i] for i in sorted(pick)]
    (out / "random-windows.json").write_text(json.dumps({"rng": "numpy default_rng(20261017).choice(n, 3, replace=False)", "candidates": len(cand),
                                                         "windows": sel}, indent=1) + "\n", encoding="utf-8")
    for x0, z0 in sel:
        run(f"render-random-{int(x0)}-{int(z0)}", [HERE.parent / "render_v4.py", rec, out, f"random-{int(x0)}-{int(z0)}", int(x0), int(z0), 1000])
