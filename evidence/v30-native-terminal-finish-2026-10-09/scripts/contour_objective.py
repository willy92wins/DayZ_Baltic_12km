"""The EV13 contour objective with its analytic piecewise derivative."""
import numpy as np


class ContourObjective:
    def __init__(self, h, graph, ids):
        self.ids = np.asarray(ids)
        self.n = len(ids)
        endpoints = np.array([n['ids'] for n in graph['nodes']])
        self.xy = np.array([n['xz'] for n in graph['nodes']], dtype=float)
        self.depth = h.ravel()[endpoints] - np.array([n['water'] for n in graph['nodes']])
        lookup = {int(v): i for i, v in enumerate(ids)}
        self.J = np.zeros((*self.depth.shape, self.n))
        for k, pair in enumerate(endpoints):
            for side, index in enumerate(pair):
                if int(index) in lookup:
                    self.J[k, side, lookup[int(index)]] = 1
        p, _ = self.contour(np.zeros(self.n))
        self.samplers = []
        for chain in graph['chains']:
            chain = np.asarray(chain)
            length = np.linalg.norm(np.diff(p[chain], axis=0), axis=1).sum()
            if length > 24:
                self.samplers.append((chain, np.arange(0, length, 2) / length))

    def contour(self, x):
        d = self.depth + np.einsum('ijk,k->ij', self.J, x)
        den = d[:, 0] - d[:, 1]
        tau = d[:, 0] / den
        jt = (-d[:, 1, None] * self.J[:, 0] + d[:, 0, None] * self.J[:, 1]) / den[:, None]**2
        step = self.xy[:, 1] - self.xy[:, 0]
        return self.xy[:, 0] + tau[:, None] * step, step[:, :, None] * jt[:, None, :]

    def __call__(self, x):
        points, jp = self.contour(x)
        total = 0.; grad = np.zeros(self.n); count = 0
        for chain, fraction in self.samplers:
            p, j = points[chain], jp[chain]
            segment = np.diff(p, axis=0)
            length = np.linalg.norm(segment, axis=1)
            if np.any(length < 1e-12):
                raise ValueError('Collapsed contour edge is outside the differentiable domain')
            jl = np.einsum('ij,ijk->ik', segment / length[:, None], np.diff(j, axis=0))
            dist = np.r_[0., np.cumsum(length)]
            jd = np.vstack((np.zeros(self.n), np.cumsum(jl, axis=0)))
            sample = fraction * dist[-1]
            k = np.clip(np.searchsorted(dist, sample, side='right') - 1, 0, len(length) - 1)
            t = (sample - dist[k]) / length[k]
            jt = (fraction[:, None] * jd[-1] - jd[k] - t[:, None] * jl[k]) / length[k, None]
            q = p[k] + t[:, None] * segment[k]
            jq = (1 - t[:, None, None]) * j[k] + t[:, None, None] * j[k+1] + segment[k, :, None] * jt[:, None, :]
            a, b = q[3:-3] - q[:-6], q[6:] - q[3:-3]
            ja, jb = jq[3:-3] - jq[:-6], jq[6:] - jq[3:-3]
            cross = a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]
            theta = np.arctan2(abs(cross), np.sum(a * b, axis=1))
            a2, b2 = np.sum(a*a, axis=1), np.sum(b*b, axis=1)
            if np.any(a2 < 1e-12) or np.any(b2 < 1e-12):
                raise ValueError('Collapsed sample chord')
            jtheta = np.sign(cross)[:, None] * (
                (a[:, 1, None] * ja[:, 0] - a[:, 0, None] * ja[:, 1]) / a2[:, None] +
                (-b[:, 1, None] * jb[:, 0] + b[:, 0, None] * jb[:, 1]) / b2[:, None])
            excess = np.maximum(theta - np.pi/6, 0)
            total += np.sum(theta**2 + 4 * excess**2)
            grad += np.sum((2*theta + 8*excess)[:, None] * jtheta, axis=0)
            count += len(theta)
        if not count:
            raise ValueError('No metric contour observations')
        return float(total / count + .002*np.mean((x/2)**2)), grad/count + .001*x/self.n


def derivative_controls():
    """Exercise production derivatives on real graphs plus a separate scalar function."""
    import json, sys
    from pathlib import Path
    parent = Path('E:/DayZ-Baltic-Build/v30-native-turn-optimizer-20261009')
    sys.path.insert(0, str(parent))
    from optimize_native_turns import bounds_for
    from discover_native_turns import B10, B12
    h = np.load(parent/'candidate-feasible/terrain.npz')['heights'].astype(float)
    field = np.load(B12/'preserved-field.npy'); plane = np.load(B10/'frozen-field-reference/plane.npy')
    rng = np.random.default_rng(20261009); results = []
    for reach in ('R1', 'R2'):
        graph = json.loads((parent/(reach+'-graph.json')).read_text())
        ids = np.load(parent/(reach+'-constraints.npz'))['movable']
        lo, hi, _ = bounds_for(ids, h, field, plane)
        keep = hi-lo > 1e-8; ids, lo, hi = ids[keep], lo[keep], hi[keep]
        fn = ContourObjective(h, graph, ids)
        x = lo + .413*(hi-lo)
        value, jac = fn(x)
        errors = []
        for _ in range(12):
            direction = rng.normal(size=len(ids)); direction /= np.linalg.norm(direction)
            step = 1e-5
            estimate = (fn(x+step*direction)[0]-fn(x-step*direction)[0])/(2*step)
            exact = jac@direction
            error = abs(estimate-exact) / max(1., abs(exact), abs(estimate))
            errors.append(float(error))
        assert max(errors) < 1e-4, (reach, errors)
        # The original EV13 arccos value calculation, independent of the analytic gradient.
        points, _ = fn.contour(x); angles = []
        for chain, fraction in fn.samplers:
            p=points[chain]; dist=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
            s=fraction*dist[-1];q=np.c_[np.interp(s,dist,p[:,0]),np.interp(s,dist,p[:,1])]
            a=q[3:-3]-q[:-6];b=q[6:]-q[3:-3]
            angle=np.arccos(np.clip(np.sum(a*b,axis=1)/(np.linalg.norm(a,axis=1)*np.linalg.norm(b,axis=1)),-1,1))
            angles.extend((angle**2+4*np.maximum(angle-np.pi/6,0)**2).tolist())
        reference=np.mean(angles)+.002*np.mean((x/2)**2)
        assert abs(value-reference) < 1e-10
        results.append(dict(reach=reach, variables=len(ids), directions=12,
                            maximum_directional_error=max(errors), original_value_error=float(abs(value-reference))))
    for name in ('straight', 'right_angle', 'curved'):
        xx=np.arange(0.,54.,2.); zz=np.zeros_like(xx)
        if name=='right_angle':
            zz=np.maximum(xx-26,0);xx=np.minimum(xx,26)
        elif name=='curved':
            zz=4*np.sin(xx/14)
        n=len(xx); heights=np.tile([.5,1.5],n)
        nodes=[dict(ids=[2*k,2*k+1],water=[1.,1.],
                    xz=[[float(xx[k]),float(zz[k]-.5)],[float(xx[k]),float(zz[k]+.5)]]) for k in range(n)]
        fn=ContourObjective(heights,dict(nodes=nodes,chains=[list(range(n))]),np.arange(2*n))
        basevalue=fn(np.zeros(2*n))[0]
        if name=='straight': assert basevalue==0
        if name=='right_angle': assert basevalue>.1
        x=rng.uniform(-.02,.02,2*n); value,jac=fn(x);errors=[]
        for _ in range(12):
            direction=rng.normal(size=2*n);direction/=np.linalg.norm(direction)
            estimate=(fn(x+1e-5*direction)[0]-fn(x-1e-5*direction)[0])/2e-5
            errors.append(float(abs(estimate-jac@direction)/max(1.,abs(estimate),abs(jac@direction))))
        assert max(errors)<1e-4,(name,errors)
        results.append(dict(fixture=name,directions=12,maximum_directional_error=max(errors),base_objective=basevalue))
    return results


if __name__ == '__main__':
    import json
    from pathlib import Path
    result = dict(status='PASS_PRODUCTION_DERIVATIVE', controls=derivative_controls())
    Path(__file__).with_name('derivative-controls.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
