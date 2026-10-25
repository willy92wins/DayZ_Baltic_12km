"""Seed sweep on fixed regions (development seeds or held-out seeds): place each region with its own calibration pass,
then judge it. Regions (fixed before the sweep): the pilot squares A and B with their surroundings and the open bogs
of the map (see REGIONS). Per seed and region: G1, G4, G5 (every instance), the EV111 pilot squares with the unchanged
r2 scripts (G2 --dense A-reserva, G3, G7 r2 scope) when the region holds them, G7 v4 (bogs in the region), G8 and
G2/G3 per 1 km window inside the region.
Usage: python -I run_regions.py <tool.py> <out dir> <gate-rasters dir> <livonia-ev112-bands.json> <seed> [<seed> ...]
Writes <out>/seed<k>-<region>/ (placer output) and <out>/sweep.json; prints one line per seed and region."""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gcfg  # noqa: E402

PY = sys.executable
REGIONS = {"A": "7600,4300,10800,6900", "B": "8100,6600,9500,7950", "SW": "300,0,2400,1400"}
tool, out, rast, bands = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4]
seeds = [int(s) for s in sys.argv[5:]]
out.mkdir(parents=True, exist_ok=True)
E = gcfg.E


def place(seed, region, d):
    a = [PY, "-I", "-B", str(tool), "--terrain", str(gcfg.TERRAIN), "--footprint", str(gcfg.FOOTPRINT), "--stage-wrp", str(gcfg.STAGE_WRP),
         "--pbo", gcfg.PBO]
    for ld in gcfg.LAYER_DIRS:
        a += ["--layer-dir", ld]
    a += ["--cover", str(gcfg.LAYERS), "--reference", str(gcfg.REFERENCE), "--seed", str(seed), "--out", str(d),
          "--region", region, "--workers", "4"]
    p = subprocess.run(a, capture_output=True, text=True)
    (d.parent / f"{d.name}.place.log").write_text(p.stdout + p.stderr, encoding="utf-8")
    return p.returncode


def gate(cmd, log):
    p = subprocess.run([PY, "-I", "-B", *map(str, cmd)], capture_output=True, text=True, cwd=str(HERE))
    log.write_text(p.stdout + p.stderr, encoding="utf-8")
    last = [ln for ln in p.stdout.splitlines() if ln.strip()]
    return "PASS" if p.returncode == 0 else ("FAIL" if p.returncode == 1 else f"ERROR rc {p.returncode}"), (last[-1] if last else "")


summary = json.loads((out / "sweep.json").read_text(encoding="utf-8")) if (out / "sweep.json").exists() else {}
for seed in seeds:
    for rn, reg in REGIONS.items():
        d = out / f"seed{seed}-{rn}"
        key = f"{seed}-{rn}"
        if not (d / "records.json").exists():
            if place(seed, reg, d):
                summary[key] = {"place": "ERROR"}
                continue
        rec = d / "records.json"
        x0, z0, x1, z1 = [float(v) for v in reg.split(",")]
        wins = ";".join(f"{wx},{wz}" for wz in range(0, 11289, 500) for wx in range(0, 11289, 500)
                        if wx >= x0 + 100 and wx + 1000 <= x1 - 100 and wz >= z0 + 100 and wz + 1000 <= z1 - 100)
        r = {}
        r["G1"] = gate([HERE / "g1_map.py", rec, d / "g1.json"], d / "g1.log")
        r["G4"] = gate([HERE / "g4g5_map.py", rec, "G4"], d / "g4.log")
        r["G5"] = gate([HERE / "g4g5_map.py", rec, "G5"], d / "g5.log")
        r["G7v4"] = gate([HERE / "g7_map.py", rec, rast, d / "g7.json", "--livonia-bands", bands, "--bbox", reg], d / "g7.log")
        if wins:
            r["G8"] = gate([HERE / "g8_agreement.py", rec, rast, bands, d / "g8.json", "--windows", wins], d / "g8.log")
            r["G2G3win"] = gate([HERE / "g2g3_map.py", rec, rast, bands, d / "g23.json", "--windows", wins], d / "g23.log")
        if rn in ("A", "B"):
            sub = d / "pilot-subset.json"
            gate([HERE / "pilot_subset.py", rec, sub], d / "subset.log")
            sec = "A-reserva" if rn == "A" else "B-bosque-carretera-agua"
            for g, args in (("G2r2", ["g2_g3.py", sub, "G2", "--dense", "A-reserva", "--json", d / "g2r2.json"]),
                            ("G3r2", ["g2_g3.py", sub, "G3", "--json", d / "g3r2.json"]),
                            ("G7r2", ["g7_bog.py", sub, "--json", d / "g7r2.json"])):
                p = subprocess.run([PY, "-I", "-B", *map(str, args)], capture_output=True, text=True, cwd=str(gcfg.R2_GATES))
                (d / f"{g}.log").write_text(p.stdout + p.stderr, encoding="utf-8")
                line = [ln for ln in p.stdout.splitlines() if ln.strip().startswith(sec) and (" G2:" in ln or " G3:" in ln or " G7:" in ln)]
                r[g] = (line[-1].split(":")[1].split()[0] if line else "NOT_JUDGED", line[-1].strip() if line else "")
        summary[key] = {k: v[0] for k, v in r.items()}
        print(f"seed {seed} {rn}: " + " ".join(f"{k} {v[0]}" for k, v in r.items()), flush=True)
        (out / "sweep.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
