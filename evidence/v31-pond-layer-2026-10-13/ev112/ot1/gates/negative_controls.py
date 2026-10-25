"""Negative controls for the kit gates (round 1 after the review of 15-10; the first eight modes are the reviewer's
impl-kit-review1/negative_control.py, the rest are new). Each mode seeds a NEW folder <base>/neg-<mode> from a validated run,
applies one mutation and runs one gate in-process; the expected verdict is printed next to the gate's own line.
Usage: negative_controls.py <validated_run> <base_dir> [mode ...]"""
import copy, json, os, pathlib, runpy, shutil, subprocess, sys
import numpy as np
sys.dont_write_bytecode = True
I = pathlib.Path(__file__).parent; sys.path.insert(0, str(I)); import gatelib as G
N = pathlib.Path(sys.argv[1]); BASE = pathlib.Path(sys.argv[2])
EXPECT = {"g1-no-output": ("gate_g1_cli.py", "FAIL"), "wide": ("gate_g2_width.py", "FAIL"), "stray": ("gate_g3_continuity.py", "FAIL"),
          "no-water-textures-g4": ("gate_g4_engine_margin.py", "PASS"), "no-water-textures-g7": ("gate_g7_probe.py", "FAIL"),
          "frozen": ("gate_g5_slopes.py", "FAIL"), "steep": ("gate_g5_slopes.py", "FAIL"), "envelope": ("gate_g6_pond_layer.py", "FAIL"),
          "probe-coordinates": ("gate_g7_probe.py", "FAIL"), "probe-coordinates-all": ("gate_g7_probe.py", "FAIL"),
          "probe-csv": ("gate_g7_probe.py", "FAIL"), "probe-side": ("gate_g7_probe.py", "FAIL"), "probe-scale": ("gate_g7_probe.py", "FAIL"),
          "probe-lip-end": ("gate_g7_probe.py", "FAIL"), "old-bed-in-sheet": ("gate_g7_probe.py", "FAIL"),
          "g8-no-log": ("gate_g8_engine_probe.py", "NOT_RUN"), "g8-as-expected": ("gate_g8_engine_probe.py", "PASS"),
          "g8-lips-dry": ("gate_g8_engine_probe.py", "FAIL"), "g8-control-wet": ("gate_g8_engine_probe.py", "FAIL"),
          # review 2 of 15-10 (EV110 step 11): dry labels changed or dropped, non-finite readings
          "dry-expect-test": ("gate_g7_probe.py", "FAIL"), "dry-expect-absent": ("gate_g7_probe.py", "FAIL"),
          "g8-relabel-dry-all-wet": ("gate_g8_engine_probe.py", "FAIL"), "g8-dry-depth-nan": ("gate_g8_engine_probe.py", "FAIL"),
          "g8-ground-nan": ("gate_g8_engine_probe.py", "FAIL")}
DRY_KINDS = ("kit_side", "kit_joint_side", "old_bed")
modes = sys.argv[3:] or list(EXPECT)
real_run = subprocess.run
GEOM0 = G.GEOM


def seed(D, names):
    for f in names:
        (D / f).parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(N / f, D / f)


def gate(D, name):
    sys.argv = [str(I / name), str(D)]
    try:
        runpy.run_path(sys.argv[0], run_name="__main__")
    except SystemExit:
        pass


def probe_hook(mutate):
    def fake(cmd, *a, **kw):
        p = real_run(cmd, *a, **kw)
        if any(str(x).endswith("probe_points_kit.py") for x in cmd):
            j = pathlib.Path(next(x for x in cmd if str(x).endswith("points.json"))); c = pathlib.Path(next(x for x in cmd if str(x).endswith("points.csv")))  # EV112: G7 passes the sites file last
            ps = json.load(open(j)); rows = mutate(ps)
            json.dump(ps, open(j, "w"))
            c.write_text(rows if isinstance(rows, str) else "".join(f"{q['id']};{q['x']:.6f} 0 {q['z']:.6f}\n" for q in ps))
        return p
    subprocess.run = fake


def g8_log(D, depth_of, ground_of=None):
    ps = json.load(open(D / "probe/points.json"))
    L = ["BALTIC_BRIDGE_PROBE_V2;BalticTrial", f"BEGIN;{len(ps)}"]
    for p in ps:
        g = p.get("ground", 1.0) if ground_of is None else ground_of(p)
        s = "nan" if isinstance(g, str) else g + 0.2
        L.append(f"P;{p['id']};{g};false;true;{s};{depth_of(p)};{g};5")
    L.append(f"END;{len(ps)}")
    (D / "probe/baltic_bridge_probe_v2.log").write_text("\n".join(L) + "\n")


PROBE = ["terrain-ev108.npz", "kit-records.json", "bury-work/fp0/footprint.npz"]
results = {}
for mode in modes:
    D = BASE / f"neg-{mode}"; D.mkdir(parents=True, exist_ok=False)
    subprocess.run = real_run; G.GEOM = GEOM0
    gname, want = EXPECT[mode]
    if mode == "stray":
        seed(D, ["terrain-kit.npz", "kit-records.json", "kit-report.json"]); rs = json.load(open(D / "kit-records.json"))
        a = copy.deepcopy(next(r for r in rs if r["site"] == "kit-118" and r["piece"] == 8)); a["piece"] = 999
        a["matrix"][9] -= 60; a["matrix"][10] += 30; rs.append(a); json.dump(rs, open(D / "kit-records.json", "w"))
    elif mode.startswith("no-water-textures"):
        seed(D, ["terrain-kit.npz", "kit-records.json", "kit-report.json"] + (PROBE[:1] + PROBE[2:] if mode.endswith("g7") else []))
        g = json.load(open(G.GEOM))
        for m in g["models"].values():
            for f in m["road"]:
                f["tex"] = "concrete_ext.paa"
        gp = D / "geometry.json"; json.dump(g, open(gp, "w")); G.GEOM = str(gp)
    elif mode == "wide":
        seed(D, ["kit-records.json", "kit-report.json"]); z = np.load(N / "terrain-kit.npz"); arr = {k: z[k] for k in z.files}
        arr["heights"] = arr["heights"] - 50; np.savez(D / "terrain-kit.npz", **arr)
    elif mode in ("frozen", "steep"):
        z = np.load(N / "terrain-kit.npz"); arr = {k: z[k] for k in z.files}
        if mode == "frozen":
            r, c = np.argwhere(arr["platform"])[100]; arr["heights"][r, c] += .01
        else:
            r, c = 1000, 1000; arr["heights"][r, c] += 30
        np.savez(D / "terrain-kit.npz", **arr)
    elif mode == "envelope":
        seed(D, ["terrain-kit.npz", "cover-ev108.npy", "envelope-ev108.npy"]); e = np.load(D / "envelope-ev108.npy")
        c = np.load(D / "cover-ev108.npy"); r, col = np.argwhere(np.isfinite(c))[100]; e[r, col] = np.nan; np.save(D / "envelope-ev108.npy", e)
    elif mode == "g1-no-output":
        def fake(cmd, *a, **kw):
            if any(str(x).endswith("/tools/water/streambed_kit_v31.py") for x in cmd):
                return subprocess.CompletedProcess(cmd, 0, "", "")
            return real_run(cmd, *a, **kw)
        subprocess.run = fake
    elif mode.startswith("probe-") or mode == "old-bed-in-sheet" or mode.startswith("dry-expect-"):
        seed(D, PROBE)
        if mode == "probe-coordinates":
            def m(ps):
                for q in ps:
                    if q["kind"] in ("kit_axis", "kit_side"):
                        q["x"] = 100.0; q["z"] = 100.0
        elif mode == "probe-coordinates-all":
            def m(ps):
                for q in ps:
                    if q["kind"].startswith("kit_"):
                        q["x"] = 100.0; q["z"] = 100.0
        elif mode == "probe-csv":
            def m(ps):
                k = next(i for i, q in enumerate(ps) if q["kind"] == "kit_joint")
                return "".join(f"{q['id']};{q['x'] + (1.0 if i == k else 0):.6f} 0 {q['z']:.6f}\n" for i, q in enumerate(ps))
        elif mode == "probe-side":
            def m(ps):
                q = next(q for q in ps if q["kind"] == "kit_side"); q["side"] = -q["side"]
        elif mode == "probe-scale":
            def m(ps):
                q = next(q for q in ps if q["kind"] == "kit_axis" and "curve" in q["piece_kind"]); q["scale"] = 1.0
        elif mode in ("dry-expect-test", "dry-expect-absent"):
            def m(ps):
                for q in ps:
                    if q["kind"] in DRY_KINDS:
                        if mode == "dry-expect-test":
                            q["expect"] = "test"
                        else:
                            q.pop("expect", None)
        elif mode == "probe-lip-end":
            def m(ps):
                q = next(q for q in ps if q["kind"] == "kit_lip"); q["end"] = "upstream" if q["end"] == "downstream" else "downstream"
        else:
            def m(ps):
                ps.append(dict(id=len(ps), kind="old_bed", x=8718.0, z=11460.0, plane=2.575, ground=1.838073, expect="dry"))
        probe_hook(m)
    elif mode.startswith("g8-"):
        (D / "probe").mkdir(parents=True); shutil.copyfile(N / "probe/points.json", D / "probe/points.json")
        if mode == "g8-as-expected":
            g8_log(D, lambda p: 0.2 if p.get("expect") in ("wet", "test") else -0.5)
        elif mode == "g8-lips-dry":
            g8_log(D, lambda p: 0.2 if p.get("expect") == "wet" else -0.5)
        elif mode == "g8-control-wet":
            g8_log(D, lambda p: 0.2 if p.get("expect") in ("wet", "test") or p["kind"] == "old_bed" else -0.5)
        elif mode == "g8-relabel-dry-all-wet":                  # review 2: dry controls relabelled 'test', all of them wet
            ps = json.load(open(D / "probe/points.json"))
            for q in ps:
                if q["kind"] in DRY_KINDS:
                    q["expect"] = "test"
            json.dump(ps, open(D / "probe/points.json", "w"))
            g8_log(D, lambda p: 0.2 if p.get("expect") in ("wet", "test") else -0.5)
        elif mode == "g8-dry-depth-nan":                        # review 2: depth NaN on every dry control
            g8_log(D, lambda p: "nan" if p["kind"] in DRY_KINDS else (0.2 if p.get("expect") in ("wet", "test") else -0.5))
        elif mode == "g8-ground-nan":                           # review 2: engine ground NaN on every classified point
            g8_log(D, lambda p: 0.2 if p.get("expect") in ("wet", "test") else -0.5,
                   lambda p: "nan" if "expect" in p else p.get("ground", 1.0))
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        gate(D, gname)
    out = buf.getvalue().strip().splitlines()
    last = out[-1] if out else "(no output)"
    got = last.split()[1] if len(last.split()) > 1 else "?"
    (D / "negative.log").write_text(buf.getvalue())
    results[mode] = dict(gate=gname, expected=want, got=got, line=last, ok=got == want)
    print(mode, json.dumps(results[mode]), flush=True)
    subprocess.run = real_run
json.dump(results, open(BASE / "negative-controls-r1.json", "w"), indent=1)
print("NEGATIVE CONTROLS", "ALL AS EXPECTED" if all(r["ok"] for r in results.values()) else "UNEXPECTED")
sys.exit(0 if all(r["ok"] for r in results.values()) else 1)
