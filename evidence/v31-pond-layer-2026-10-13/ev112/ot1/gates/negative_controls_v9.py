"""Negative controls of the gates new in EV112 (G9 mounds, G10 stones, G11 roads/bridges/kept water) and of G0. Each mode seeds a
NEW folder <base>/neg-<mode> from a validated run (or from the EV110 kit outputs), applies one mutation and runs one gate; the
expected verdict is printed next to the gate's own last line. The EV110 controls (negative_controls.py, 24 modes) still apply
to G1-G8. Usage: negative_controls_v9.py <validated_run> <base_dir> [mode ...]"""
import json, os, pathlib, shutil, subprocess, sys
import numpy as np
I = pathlib.Path(__file__).parent; sys.path.insert(0, str(I)); import gatelib as G
N = pathlib.Path(sys.argv[1]); BASE = pathlib.Path(sys.argv[2])
EV110 = pathlib.Path(G.B) / "ev110" / "kit"
EXPECT = {"mound-spike": ("gate_g9_mounds.py", "FAIL"), "mound-new-ring-pyramid": ("gate_g9_mounds.py", "FAIL"),
          "stones-ev110": ("gate_g10_stones.py", "FAIL"), "stones-lift": ("gate_g10_stones.py", "FAIL"),
          "stones-out": ("gate_g10_stones.py", "FAIL"), "stones-density": ("gate_g10_stones.py", "FAIL"),
          "stones-on-road": ("gate_g10_stones.py", "FAIL"), "stones-as-is": ("gate_g10_stones.py", "PASS"),
          "piece-on-road": ("gate_g11_junctions.py", "FAIL"), "piece-at-bridge": ("gate_g11_junctions.py", "FAIL"),
          "kept-envelope-cut": ("gate_g11_junctions.py", "FAIL"), "kept-water-lost": ("gate_g11_junctions.py", "FAIL"),
          "junctions-as-is": ("gate_g11_junctions.py", "PASS")}
modes = sys.argv[3:] or list(EXPECT)
RUNF = ["terrain-kit.npz", "kit-records.json", "kit-report.json", "envelope-ev108.npy", "cover-ev108.npy"]


def seed(D, src=N, names=RUNF):
    for f in names:
        (D / f).parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(src / f, D / f)


def seed_fp(D):
    fps = sorted((N / "bury-work").glob("fp*"), key=lambda p: int(p.name[2:]))
    (D / "bury-work" / fps[-1].name).mkdir(parents=True)
    shutil.copyfile(fps[-1] / "footprint.npz", D / "bury-work" / fps[-1].name / "footprint.npz")
    return D / "bury-work" / fps[-1].name / "footprint.npz"


def save_npz(path, arr):
    np.savez(path, **arr)


results = {}
for mode in modes:
    D = BASE / f"neg-{mode}"; D.mkdir(parents=True, exist_ok=False)
    gname, want = EXPECT[mode]
    if mode.startswith("mound"):
        seed(D)
        z = np.load(D / "terrain-kit.npz"); arr = {k: z[k].copy() for k in z.files}
        g9 = json.load(open(N / "gate-g9.json"))
        H = arr["heights"]; rep = json.load(open(D / "kit-report.json"))
        s = next(x for x in rep["sites"] if "skipped" not in x and x.get("mode") == "reach")
        V = np.array(s["lattice"]); mid = V[len(V) // 2]; d = V[len(V) // 2 + 1] - V[len(V) // 2]; n = np.array([-d[1], d[0]]) / np.linalg.norm(d)
        off = 15.0 if mode == "mound-spike" else 3.0                 # 15 m: judged band; 3 m: a seat-ring vertex (new pyramid)
        p = mid + off * n; r, c = int(round((G.ZTOP - p[1]) / 6)), int(round(p[0] / 6))
        H[r, c] = H[r - 1:r + 2, c - 1:c + 2].max() + 1.0
        arr["heights"] = H; save_npz(D / "terrain-kit.npz", arr)
    elif mode.startswith("stones"):
        if mode == "stones-ev110":
            seed(D, EV110, ["terrain-kit.npz", "kit-records.json", "kit-report.json", "envelope-ev108.npy"])
        else:
            seed(D)
            recs = json.load(open(D / "kit-records.json"))
            st = [r for r in recs if r["piece"] == "stones"]
            if mode == "stones-lift":
                for r in st:
                    r["matrix"][10] += 0.5
            elif mode == "stones-out":
                for r in st:
                    r["matrix"][9] += 7.0
            elif mode == "stones-density":
                sid = max({r["site"] for r in st}, key=lambda k: sum(1 for r in st if r["site"] == k))
                drop = [r for r in st if r["site"] == sid][::2]
                recs = [r for r in recs if not any(r is d for d in drop)]
            elif mode == "stones-on-road":
                z = np.load(D / "terrain-kit.npz"); fr = np.argwhere(z["platform"])[5000]
                st[0]["matrix"][9] = 6.0 * fr[1] + 3; st[0]["matrix"][11] = G.ZTOP - 6.0 * fr[0] - 3
            json.dump(recs, open(D / "kit-records.json", "w"))
    elif mode in ("piece-on-road", "piece-at-bridge", "kept-envelope-cut", "kept-water-lost", "junctions-as-is"):
        seed(D); fp = seed_fp(D)
        recs = json.load(open(D / "kit-records.json"))
        if mode in ("piece-on-road", "piece-at-bridge"):
            rep = json.load(open(D / "kit-report.json"))
            sid = next(x["site"] for x in rep["sites"] if "skipped" not in x and x.get("mode") == "reach")
            p = next(r for r in recs if r["site"] == sid and r["piece"] != "stones")
            if mode == "piece-on-road":
                z = np.load(D / "terrain-kit.npz"); fr = np.argwhere(z["platform"])[5000]
                tx, tz = 6.0 * fr[1], G.ZTOP - 6.0 * fr[0]; p["matrix"][10] = float(z["heights"][fr[0], fr[1]]) + 1.0
            else:
                tx, tz = 10338.9 + 20.0, 7423.1
            p["matrix"][9] = tx; p["matrix"][11] = tz
            json.dump(recs, open(D / "kit-records.json", "w"))
        elif mode == "kept-envelope-cut":
            g11 = json.load(open(N / "gate-g11.json"))
            e = np.load(D / "envelope-ev108.npy"); e0 = np.load(G.B + "/bridges/envelope-ev107.npy")
            z0 = np.load(G.B + "/bridges/terrain-ev107.npz")
            # an envelope cell of the input that is still there and holds a kept wet vertex (x, z from G11's kept list or any)
            fin = np.argwhere(np.isfinite(e) & np.isfinite(e0) & (e == e0))
            r, c = fin[len(fin) // 2]
            e[r, c] = np.nan; np.save(D / "envelope-ev108.npy", e)
        elif mode == "kept-water-lost":
            f = np.load(fp); arr = {k: f[k].copy() for k in f.files}
            pl = arr["plane"]; fin = np.argwhere(np.isfinite(pl))
            r, c = fin[len(fin) // 3]; arr["plane"][max(r - 3, 0):r + 4, max(c - 3, 0):c + 4] = np.nan
            np.savez(fp, **arr)
    pr = subprocess.run([sys.executable, "-I", str(I / gname), str(D)], capture_output=True, text=True)
    last = (pr.stdout.strip().splitlines() or ["(none)"])[-1]
    got = last.split()[1] if len(last.split()) > 1 else "ERROR"
    results[mode] = dict(gate=gname, expected=want, got=got, ok=got == want, line=last, stderr=pr.stderr[-400:])
    print(mode, gname, "expected", want, "got", got, "OK" if got == want else "MISMATCH", flush=True)
json.dump(results, open(BASE / "negative-controls-v9.json", "w"), indent=1)
print("ALL AS EXPECTED" if all(v["ok"] for v in results.values()) else "SOME MISMATCH")
sys.exit(0 if all(v["ok"] for v in results.values()) else 1)
