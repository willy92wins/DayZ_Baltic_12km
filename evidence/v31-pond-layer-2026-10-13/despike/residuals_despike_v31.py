"""Classify the free-domain pyramids (> T) left by a despike run: sea islet (all 6 neighbours below 0.75 m), held by the
lowering floor (ended at the floor), held by the slope or protected guards (ended above both floor and ring mean), other.
Usage: residuals_despike_v31.py <in.npz> <out.npz> <envelope.npy> <records.json> <T>"""
import numpy as np, sys, os, json
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools", "terrain")))
import despike_v31 as d
inp, out, envp, rec, T = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5])
z = np.load(inp); a = {k: z[k] for k in z.files}
H0 = a["heights"].astype(np.float64); H1 = np.load(out)["heights"].astype(np.float64)
env = np.load(envp).astype(np.float64)
free, prot, envv = d.free_domain(a, env, [rec])
floor = np.minimum(H0, d.lower_floor(a, env))
pk, pt = d.prominence(H1)
m6 = d.mean6(H1)
Hp = np.pad(H1, 1, mode="edge")
nmax = np.max([Hp[1 + dr:1 + dr + d.N, 1 + dc:1 + dc + d.N] for dr, dc in d.NB], axis=0)
res = free & ((pk > T) | (pt > T))
islet = res & (nmax < 0.75)
at_floor = res & ~islet & (np.abs(H1 - floor) < 1e-4) & (pk > T)
other = res & ~islet & ~at_floor
out_ = dict(T=T, residual=int(res.sum()), sea_islet=int(islet.sum()), held_by_floor=int(at_floor.sum()),
            held_by_slope_or_protected_guard=int(other.sum()),
            islet_xz=[[6 * int(c), 12282 - 6 * int(r), round(float(H1[r, c]), 2)] for r, c in np.argwhere(islet)[:40]],
            floor_xz=[[6 * int(c), 12282 - 6 * int(r), round(float(max(pk[r, c], pt[r, c])), 2)] for r, c in np.argwhere(at_floor)[:40]],
            other_xz=[[6 * int(c), 12282 - 6 * int(r), round(float(max(pk[r, c], pt[r, c])), 2)] for r, c in np.argwhere(other)[:40]])
print(json.dumps(out_, indent=None))
