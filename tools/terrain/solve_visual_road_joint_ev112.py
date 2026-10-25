"""P11: solve road profile and transition dihedrals simultaneously.

Default domain is the 231 changed vertices of rejected D. --own-road-domain
reconstructs the same 36m collar with independently proven dry verges of this
road. All other vertices are constants. Native triangular interpolation; the
unchanged full road and crease consumers decide after float32 rounding.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
from scipy.optimize import minimize
from scipy.ndimage import minimum_filter, binary_dilation, distance_transform_edt
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import repair_roads_v30 as R
import verify_roads_v30 as judge
import census_creases_v31 as C
import despike_v31 as guard


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def own_road_domain(B, data, h0):
    """Same 36m domain, including this road's verge after current-water proof."""
    fp = B/'visual-merged-20261024-b/bury-work/fp0/footprint.npz'
    f = np.load(fp)
    pond = guard.env_vertex_plane(f['plane'])[0]
    fixed = data['narva'] | pond | (h0 < .9)
    fixed |= guard.shoreline_vertices(h0, fp, np.ones_like(fixed))
    fixed |= guard.records_mask([str(B/'records-nonforest.json')])[0]
    for key in ('v31_kit','v31_bridge_cut','v31_bridge_fill','v31_dam',
                'v31_shore_ramp','v31_causeway','v31_continuous_pilot'):
        fixed |= binary_dilation(data[key], iterations=2)
    rr, cc = np.mgrid[:2048,:2048]
    fixed |= np.hypot(6*cc-10397.4,12282-6*rr-9421.9) <= 60
    chains = R.road_chains()
    s,q,n,_ = R.stations(chains[49]); ix = (s>1640)&(s<1702)
    pts = q[ix][None] + R.OFFSETS[:,None,None]*n[ix][None]
    ra,ca,_ = R.bary(pts[...,0].ravel(),pts[...,1].ravel())
    road = np.zeros_like(fixed); road[ra,ca] = True
    domain = distance_transform_edt(~road)*6 <= 36
    coords = np.argwhere(domain)
    xz = np.column_stack((coords[:,1]*6,12282-coords[:,0]*6))
    other = np.vstack([R.stations(ch)[1] for i,ch in enumerate(chains) if i!=49 and len(ch)>=4])
    distances = cKDTree(other).query(xz)[0]
    # This entire candidate is >60m from every sampled neighbouring road.
    assert distances.min()>60
    wet = np.load(B/'forest-visual-consumers-20261024-a/water1m.npy',mmap_mode='r')
    localmin = minimum_filter(h0,size=3)
    dry = np.zeros_like(fixed)
    for r,c in coords:
        x,z = int(c*6),int(12282-r*6)
        dry[r,c] = localmin[r,c]>.9 and not np.isfinite(f['plane'][r-1:r+1,c-1:c+1]).any() and not wet[12288-z-6:12288-z+6,x-6:x+6].any()
    free = domain & ~fixed & dry
    return free, dict(collar_m=36,domain_vertices=int(domain.sum()),free_vertices=int(free.sum()),
                     fixed_vertices=int((domain&fixed).sum()),nearest_other_road_m=float(distances.min()),
                     dry_legacy_vertices=int((free&data['water']).sum()),
                     reserve_vertices=int((free&data['reserve']).sum()),
                     footprint_sha256=sha(fp),records_sha256=sha(B/'records-nonforest.json'),
                     water1m_sha256=sha(B/'forest-visual-consumers-20261024-a/water1m.npy'))


def linear_roads(h0, free, water=None):
    nv = int(free.sum())
    lookup = np.full(h0.size, -1, int)
    lookup[free.ravel()] = np.arange(nv)
    blocks, lower, upper = [], [], []
    wd = distance_transform_edt(~water)*6 if water is not None else None
    for chain in R.road_chains():
        if len(chain) < 4:
            continue
        s, q, normal, _ = R.stations(chain)
        pts = q[None] + R.OFFSETS[:, None, None] * normal[None]
        rr, cc, w = R.bary(pts[..., 0].ravel(), pts[..., 1].ravel())
        iv = lookup[rr * 2048 + cc]
        touched = (iv >= 0).any(1).reshape(17, len(s)).any(0)
        if not touched.any():
            continue
        # Every touched station plus all endpoint/chord dependencies.
        ix = np.arange(max(0, np.flatnonzero(touched)[0] - 6), min(len(s), np.flatnonzero(touched)[-1] + 7))
        sel = (np.arange(17)[:, None] * len(s) + ix[None]).ravel()
        rr, cc, w, iv = rr[sel], cc[sel], w[sel], iv[sel]
        a = np.zeros((len(sel), nv))
        for j in range(3):
            ok = iv[:, j] >= 0
            a[np.flatnonzero(ok), iv[ok, j]] += w[ok, j]
        base = (h0[rr, cc] * w).sum(1)
        a = a.reshape(17, len(ix), nv)
        base = base.reshape(17, len(ix))
        valid = np.ones(len(ix),bool)
        if wd is not None:
            vr = np.clip(np.rint((12282-q[ix,1])/6).astype(int),0,2047)
            vc = np.clip(np.rint(q[ix,0]/6).astype(int),0,2047)
            valid = (wd[vr,vc]>judge.LIMITS['water_clear_m']) & (np.linalg.norm(q[ix]-judge.NARVA,axis=1)>judge.LIMITS['narva_clear_m']) & (s[ix]>judge.LIMITS['end_margin_m']) & (s[ix]<s[-1]-judge.LIMITS['end_margin_m'])
        def add(mat, value, bound, selected):
            active = np.any(mat != 0, axis=1)
            active &= selected
            blocks.append(mat[active])
            bound = np.broadcast_to(bound, value.shape)
            lower.append((-bound - value)[active])
            upper.append((bound - value)[active])
        for j in range(17):
            if j != 8:
                add(a[j] - a[8], base[j] - base[8], .0135, valid)
        add(np.diff(a[8], axis=0), np.diff(base[8]), .064 * np.diff(s[ix]), valid[:-1]&valid[1:])
        add(a[8, 3:-3] - .5 * (a[8, :-6] + a[8, 6:]),
            base[8, 3:-3] - .5 * (base[8, :-6] + base[8, 6:]), .028, valid[3:-3]&valid[:-6]&valid[6:])
    return np.vstack(blocks), np.concatenate(lower), np.concatenate(upper)


class Edges:
    def __init__(self, h0, free):
        self.nv = int(free.sum())
        lookup = np.full(h0.size, -1, int)
        lookup[free.ravel()] = np.arange(self.nv)
        active = C.pair_union(*C.tri_any(free))
        base_angles = C.angles(h0)
        a_ids, b_ids, limits, ac, bc = [], [], [], [], []
        # Face A=(NW,NE,SE), B=(NW,SW,SE), unnormalised normal Y=1.
        coef_a = np.array([[1, -1, 0], [0, -1, 1]], float) / 6
        coef_b = np.array([[0, 1, -1], [-1, 1, 0]], float) / 6
        def face(r, c, kind):
            nw = r * 2048 + c
            return [nw, nw + (1 if kind == 'A' else 2048), nw + 2049]
        for key, mask in active.items():
            for r, c in np.argwhere(mask):
                if key == 'diagonal':
                    left, right, ca, cb = face(r,c,'A'), face(r,c,'B'), coef_a, coef_b
                elif key == 'east':
                    left, right, ca, cb = face(r,c,'A'), face(r,c+1,'B'), coef_a, coef_b
                else:
                    left, right, ca, cb = face(r,c,'B'), face(r+1,c,'A'), coef_b, coef_a
                a_ids.append(left); b_ids.append(right); ac.append(ca); bc.append(cb)
                limits.append(max(19.9, float(base_angles[key][r,c]) - .01))
        self.ia, self.ib = np.array(a_ids), np.array(b_ids)
        self.va, self.vb = lookup[self.ia], lookup[self.ib]
        self.ac, self.bc = np.array(ac), np.array(bc)
        self.ba, self.bb = h0.ravel()[self.ia], h0.ravel()[self.ib]
        self.threshold = np.cos(np.radians(limits))

    def values_jac(self, x):
        def evaluate(base, iv, coef):
            heights = base + np.where(iv >= 0, x[np.maximum(iv, 0)], 0)
            slopes = np.einsum('eij,ej->ei', coef, heights)
            vec = np.column_stack((slopes[:,0], np.ones(len(slopes)), slopes[:,1]))
            length = np.linalg.norm(vec, axis=1)
            return vec, length
        a, la = evaluate(self.ba, self.va, self.ac)
        b, lb = evaluate(self.bb, self.vb, self.bc)
        cos = np.einsum('ij,ij->i', a, b) / (la * lb)
        da = b / (la*lb)[:,None] - cos[:,None] * a / la[:,None]**2
        db = a / (la*lb)[:,None] - cos[:,None] * b / lb[:,None]**2
        jac = np.zeros((len(cos), self.nv))
        for iv, coeff, derivative in ((self.va,self.ac,da), (self.vb,self.bc,db)):
            grad = np.einsum('ei,eij->ej', derivative[:,[0,2]], coeff)
            for j in range(3):
                ok = iv[:,j] >= 0
                np.add.at(jac, (np.flatnonzero(ok),iv[ok,j]), grad[ok,j])
        return cos - self.threshold, jac


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('build', type=Path); ap.add_argument('out', type=Path)
    ap.add_argument('--feasibility-first', action='store_true')
    ap.add_argument('--own-road-domain', action='store_true')
    args = ap.parse_args(); B, out = args.build, args.out
    assert not out.exists()
    source = B/'visual-merged-20261024-b/terrain-buried.npz'
    prior_path = B/'road-repair-20261024-d/review.json'
    prior = json.loads(prior_path.read_text())
    assert sha(source) == prior['terrain_input_sha256']
    assert all(v for k,v in prior['checks'].items() if k != 'no_regressed_sharp_edges')
    data = dict(np.load(source)); h0 = data['heights'].astype(float)
    free = np.zeros(h0.shape, bool)
    for rec in prior['changes']:
        r,c = rec['row'],rec['col']; assert h0[r,c] == rec['before']; free[r,c] = True
    assert int(free.sum()) == 231
    domain_report = None
    if args.own_road_domain:
        free, domain_report = own_road_domain(B, data, h0)
    nv = int(free.sum())
    wet=np.load(B/'roads-visual-review-20261024-c/water-vertices.npz')['wet']
    A, low, high = linear_roads(h0, free, wet)
    edge = Edges(h0, free)
    # Known good analytic Jacobian check, at a nonzero interior perturbation.
    rng = np.random.default_rng(20261024); probe = rng.normal(0,.03,nv)
    value, jac = edge.values_jac(probe); eps=1e-5
    error=0.
    for j in rng.choice(nv, 12, replace=False):
        p=probe.copy();p[j]+=eps;m=probe.copy();m[j]-=eps
        numeric=(edge.values_jac(p)[0]-edge.values_jac(m)[0])/(2*eps)
        error=max(error,float(np.max(np.abs(numeric-jac[:,j]))))
    assert error < 1e-7
    print(json.dumps(dict(vertices=nv,linear=len(low),edges=len(value),jacobian_max_error=error,domain=domain_report)),flush=True)
    # Hard road and edge inequalities are simultaneous; one bounded solve.
    def constraints(x):
        ax=A@x
        return np.r_[ax-low,high-ax,edge.values_jac(x)[0]]
    def constraint_jac(x):
        return np.vstack((A,-A,edge.values_jac(x)[1]))
    start=time.monotonic(); iteration=[0]
    def callback(x):
        iteration[0]+=1
        if iteration[0]%20==0:print(json.dumps(dict(iteration=iteration[0],seconds=time.monotonic()-start,violation=float(min(0,constraints(x).min())))),flush=True)
        if time.monotonic()-start>240:raise TimeoutError('bounded joint trial exceeded 240s')
    initial_grid=np.zeros_like(h0)
    for rec in prior['changes']:initial_grid[rec['row'],rec['col']]=rec['after']-rec['before']
    initial=initial_grid[free]
    phase_one=None
    if args.feasibility_first:
        # A feasible starting point in augmented space. Slack is only a solver
        # diagnostic: final acceptance still requires every original constraint.
        scale=np.r_[np.full(2*len(low),.03),np.full(len(value),.06)]
        zero=np.zeros(nv)
        y0=np.r_[zero,max(0.,float(-(constraints(zero)/scale).min()))+1e-5]
        def fun1(y):return float(y[-1]+1e-7*(y[:-1]@y[:-1]))
        def jac1(y):return np.r_[2e-7*y[:-1],1.]
        def cons1(y):return constraints(y[:-1])/scale+y[-1]
        def jaccons1(y):return np.column_stack((constraint_jac(y[:-1])/scale[:,None],np.ones(len(scale))))
        phase_one=minimize(fun1,y0,jac=jac1,method='SLSQP',
            constraints=[dict(type='ineq',fun=cons1,jac=jaccons1)],
            bounds=[(-2.5,2.5)]*nv+[(0,None)],callback=lambda y:callback(y[:-1]),
            options=dict(maxiter=160,ftol=1e-10,disp=False))
        initial=phase_one.x[:-1]
        print(json.dumps(dict(phase_one_success=bool(phase_one.success),slack=float(phase_one.x[-1]),min_constraint=float(constraints(initial).min()))),flush=True)
    result=minimize(lambda x:.5*float(x@x),initial,jac=lambda x:x,method='SLSQP',
                    constraints=[dict(type='ineq',fun=constraints,jac=constraint_jac)],
                    bounds=[(-2.5,2.5)]*nv,callback=callback,
                    options=dict(maxiter=200,ftol=1e-10,disp=False))
    h=h0.copy();h[free]+=result.x;h=h.astype(np.float32).astype(float)
    changed=h!=h0
    wet=np.load(B/'roads-visual-review-20261024-c/water-vertices.npz')['wet']
    road=judge.evaluate(h,wet)
    a0,a1=C.angles(h0),C.angles(h)
    reg={k:int((a1[k]>np.maximum(20,a0[k])+1e-4).sum()) for k in a0}
    checks=dict(outside_declared_vertices_exact=not bool((changed&~free).any()),
                sea_classification_exact=bool(np.array_equal(h<.75,h0<.75)),
                changed_stars_stay_dry=bool((minimum_filter(h,size=3)[free]>.9).all()),
                road_gate=road['status']=='PASS',no_regressed_sharp_edges=not any(reg.values()))
    out.mkdir(parents=True);data['heights']=h.astype(np.float32);data['v31_road_repair']=changed
    np.savez_compressed(out/'terrain.npz',**data)
    report=dict(status='OFFLINE_CANDIDATE_PASS' if all(checks.values()) else 'REJECTED_NOT_INTEGRATED',
                checks=checks,solver=dict(success=bool(result.success),message=str(result.message),iterations=int(result.nit),
                    seconds=time.monotonic()-start,min_constraint=float(constraints(result.x).min()),jacobian_max_error=error,
                    feasibility_slack=None if phase_one is None else float(phase_one.x[-1])),
                domain=domain_report,changed_vertices=int(changed.sum()),delta_range_m=[float((h-h0).min()),float((h-h0).max())],
                regressed_sharp_edges=reg,road=road,terrain_input_sha256=sha(source),terrain_output_sha256=sha(out/'terrain.npz'),
                sources={str(p):sha(p) for p in (Path(__file__),prior_path,Path(R.__file__),Path(judge.__file__),Path(C.__file__))},
                changes=[dict(row=int(r),col=int(c),before=float(h0[r,c]),after=float(h[r,c])) for r,c in np.argwhere(changed)],
                limits=['Not integrated: requires independent water/protection, forest support, bury, build and runtime review.'])
    (out/'review.json').write_text(json.dumps(report,indent=2))
    np.savez_compressed(out/'domain.npz',free=free)
    (out/'producer.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps({k:v for k,v in report.items() if k not in ('changes','sources','road')},indent=2))


if __name__=='__main__':
    main()
