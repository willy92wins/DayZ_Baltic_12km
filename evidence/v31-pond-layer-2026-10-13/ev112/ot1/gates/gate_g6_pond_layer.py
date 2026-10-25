"""G6: pond layer after the kit. Runs HANDOFF step 2 (tools/water/bury_edges_v31.py of the worktree) on the kit outputs:
bury_edges_v31.py terrain-kit.npz bridges/terrain-ev107.npz cover-ev108.npy envelope-ev108.npy bridges/fp-ev107/footprint-report.json
terrain-ev108.npz bury-work bury-report.json (bury-work must not exist; the gate refuses to reuse one). bury_edges calls
pond_footprint_v31.py with the envelope, whose assertion 'given envelope must contain every base cover cell' must pass.
Pass: exit 0, pass 0 has no new exposed edge, the bury pass changed 0 heights, cover subset of envelope (checked again here),
and no new engine-sea vertex (terrain < 0.75 not incident to an envelope cell) compared with the input terrain.
Usage: gate_g6_pond_layer.py [run_dir]"""
import json, os, subprocess, sys
import numpy as np
sys.dont_write_bytecode = True; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gatelib as G
run = sys.argv[1] if len(sys.argv) > 1 else G.OUT
work = run + "/bury-work"
assert not os.path.exists(work), "bury-work exists: use a fresh run dir"
cmd = [sys.executable, "-I", G.WT + "/tools/water/bury_edges_v31.py", run + "/terrain-kit.npz", G.B + "/bridges/terrain-ev107.npz",
       run + "/cover-ev108.npy", run + "/envelope-ev108.npy", G.B + "/bridges/fp-ev107/footprint-report.json",
       run + "/terrain-ev108.npz", work, run + "/bury-report.json"]
pr = subprocess.run(cmd, capture_output=True, text=True)
res = dict(cmd=" ".join(cmd), exit=pr.returncode, stderr_tail=pr.stderr[-800:])
cov = np.load(run + "/cover-ev108.npy"); env = np.load(run + "/envelope-ev108.npy")
res["cover_not_in_envelope"] = int((np.isfinite(cov) & ~np.isfinite(env)).sum())
def sea(H, env):
    e = np.isfinite(env); inc = np.zeros(H.shape, bool)
    for dr in (0, 1):
        for dc in (0, 1):
            inc[dr:dr + e.shape[0], dc:dc + e.shape[1]] |= e
    return (H < 0.75) & ~inc
H0 = np.load(G.B + "/bridges/terrain-ev107.npz")["heights"]; env0 = np.load(G.B + "/bridges/envelope-ev107.npy")
H1 = np.load(run + "/terrain-kit.npz")["heights"]
s0, s1 = sea(H0, env0), sea(H1, env)
res["sea_vertices_before_after_new"] = [int(s0.sum()), int(s1.sum()), int((s1 & ~s0).sum())]
if pr.returncode == 0:
    b = json.load(open(run + "/bury-report.json"))
    res["passes"] = [dict(pass_=p["pass_"], exposed=p["exposed"], new=len(p["new"])) for p in b["passes"]]
    res["changed_vs_input"] = b["changed_vs_input"]
    res["passed"] = (b["passes"][0]["new"] == [] and b["changed_vs_input"] == 0 and res["cover_not_in_envelope"] == 0
                     and res["sea_vertices_before_after_new"][2] == 0)
else:
    res["passed"] = False
print(json.dumps(res))
json.dump(res, open(run + "/gate-g6.json", "w"), indent=1)
print("G6", "PASS" if res["passed"] else "FAIL")
sys.exit(0 if res["passed"] else 1)
