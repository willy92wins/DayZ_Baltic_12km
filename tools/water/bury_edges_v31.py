"""Pond layer v31: bury the footprint border vertices that a terrain pass newly exposed (H < highest incident plane +
EDGE_MARGIN, not in the reference list). A free vertex is raised to plane + EDGE_MARGIN + PAD; a frozen one gets its free
8-neighbours back to the reference terrain. The footprint is recomputed after each pass (pond_footprint_v31.py), at most
PASSES times. Usage: bury_edges_v31.py <terrain.npz> <ref_terrain.npz> <cover.npy> <envelope.npy> <ref_footprint_report.json>
<out_terrain.npz> <work_dir> <report.json>
"""
import json, os, subprocess, sys
import numpy as np

EDGE_MARGIN, PAD, PASSES = 0.05, 0.01, 4
HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def footprint(terrain, cover, env, out):
    subprocess.run([PY, "-I", os.path.join(HERE, "pond_footprint_v31.py"), terrain, cover, out, env], check=True, stdout=subprocess.DEVNULL)
    return json.load(open(os.path.join(out, "footprint-report.json"))), np.load(os.path.join(out, "footprint.npz"))


def main():
    tpath, refpath, cover, env, refrep, out_t, work, rep_path = sys.argv[1:9]
    os.makedirs(work, exist_ok=False)
    ref_exposed = {tuple(x) for x in json.load(open(refrep))["exposed_xz"]}
    z = np.load(tpath); arrays = {k: z[k].copy() for k in z.files}
    H = arrays["heights"].astype(np.float64); Href = np.load(refpath)["heights"].astype(np.float64)
    frozen = arrays["reserve"] | arrays["platform"] | arrays["narva"]
    log, cur = [], tpath
    for it in range(PASSES):
        rep, fp = footprint(cur, cover, env, os.path.join(work, f"fp{it}"))
        new = [tuple(x) for x in rep["exposed_xz"] if tuple(x) not in ref_exposed]
        log.append(dict(pass_=it, exposed=rep["exposed_border_lt_0p05"], new=new))
        if not new:
            break
        plane = fp["plane"].astype(np.float64)
        vp = np.full(H.shape, -np.inf)
        cp = np.where(np.isfinite(plane), plane, -np.inf)
        for dr in (0, 1):
            for dc in (0, 1):
                vp[dr:dr + 2047, dc:dc + 2047] = np.maximum(vp[dr:dr + 2047, dc:dc + 2047], cp)
        for x, zz in new:
            r, c = 2047 - zz // 6, x // 6
            if not frozen[r, c]:
                H[r, c] = max(H[r, c], vp[r, c] + EDGE_MARGIN + PAD)
            else:
                w = (slice(max(0, r - 1), r + 2), slice(max(0, c - 1), c + 2))
                H[w] = np.where(frozen[w], H[w], Href[w])
        arrays["heights"] = H.astype(np.float32)
        cur = os.path.join(work, f"t{it}.npz"); np.savez(cur, **arrays)
        H = arrays["heights"].astype(np.float64)
    np.savez(out_t, **arrays)
    res = dict(schema="bury-edges-v31.v1", passes=log, final_new_exposed=log[-1]["new"], changed_vs_input=int((H != z["heights"]).sum()))
    json.dump(res, open(rep_path, "w"), indent=1, default=str)
    print(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
