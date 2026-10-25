"""Bounded candidate for the current 1 m / 24 m fairway contract.

Uses the frozen corridor/native-triangle intersections, never axis-only samples.
Preserves all water levels/classes and dry vertices. A separate candidate may
lower high-water bed vertices below the approved 1 m floor: that conflict is
reported explicitly and prevents promotion without a product decision.
"""
from pathlib import Path
import argparse
import json

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix
from shapely.geometry import shape

from audit_fairway_triangles_v30 import records, depths, sha
from v30_common import cell_planes


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--terrain', type=Path, required=True)
    ap.add_argument('--corridors', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    t = np.load(a.terrain)
    h = t['heights'].astype(float)
    plane = cell_planes(t['cls'], t['level'], sea_cut=.51)
    # This is the ROAD reserve (build_v30.py), not the separate nature mask.
    # An earlier bed-raising operation does not authorize lowering its vertices.
    rows, cols = np.indices(h.shape)
    narva = np.hypot(cols*6-2417.1428225906, 12282-rows*6-6889.8850822322) <= 620
    mutable = (t['cls'] == 3) & ~t['platform'] & ~t['reserve'] & ~narva
    recs = {f['properties']['river']: records(shape(f['geometry']), plane)
            for f in json.loads(a.corridors.read_text())['features']}
    ids, weights, deficits = [], [], []
    for rec in recs.values():
        depth = depths(h, rec)
        take = depth < 1.001
        ids.append(rec['ids'][take])
        weights.append(rec['weights'][take])
        deficits.append(1.001-depth[take])
    ids, weights, deficits = np.concatenate(ids), np.concatenate(weights), np.concatenate(deficits)
    variables = np.unique(ids[mutable.ravel()[ids]])
    lookup = np.full(h.size, -1, dtype=np.int32)
    lookup[variables] = np.arange(len(variables))
    cols = lookup[ids]
    use = (cols >= 0) & (weights > 0)
    rows = np.broadcast_to(np.arange(len(ids))[:, None], ids.shape)
    matrix = coo_matrix((weights[use], (rows[use], cols[use])), shape=(len(ids), len(variables))).tocsr()
    high = t['level'].ravel()[variables] >= 2.0
    ceiling = np.full(len(variables), .10)
    # Keep high-water beds above 0.90 m, i.e. above the measured sea crest 0.85 m.
    ceiling[high] = np.minimum(ceiling[high], np.maximum(0., h.ravel()[variables[high]]-.90))
    solve = linprog(np.ones(len(variables)), A_ub=-matrix, b_ub=-deficits,
                    bounds=np.column_stack([np.zeros(len(variables)), ceiling]), method='highs')
    report = dict(status='INFEASIBLE', source_sha256=sha(a.terrain), corridor_sha256=sha(a.corridors),
                  constraints=len(ids), variables=len(variables), max_lowering_bound_m=.10,
                  target_depth_m=1.001, minimum_high_water_bed_m=.90, solver_message=solve.message)
    if solve.success:
        new = t['heights'].copy()
        raw = h.ravel()[variables]-solve.x
        rounded = raw.astype(new.dtype)
        rounded = np.where(rounded.astype(float) > raw, np.nextafter(rounded, -np.inf), rounded)
        new.ravel()[variables] = rounded
        changed = new != t['heights']
        report.update(status='EXPERIMENTAL_REQUIRES_FLOOR_DECISION', changed_vertices=int(changed.sum()),
                      max_lowering_m=float((h-new).max()),
                      high_water_vertices_below_1m=int((changed & (t['level'] >= 2) & (new < 1)).sum()),
                      changes=[dict(row=int(r), col=int(c), x=int(c*6), z=int(12282-r*6),
                                    before=float(h[r,c]), after=float(new[r,c]), level=float(t['level'][r,c]))
                               for r,c in zip(*np.nonzero(changed))],
                      rivers=[dict(name=name, before_min=float(depths(h, rec).min()),
                                   after_min=float(depths(new.astype(float), rec).min()),
                                   failing_faces=int(np.unique(rec['face'][depths(new.astype(float), rec)<.99]).size))
                              for name,rec in recs.items()])
        np.savez_compressed(a.out/'terrain_fairways.npz', **{k:new if k=='heights' else t[k] for k in t.files})
        report['candidate_sha256'] = sha(a.out/'terrain_fairways.npz')
    (a.out/'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['changes','rivers']}, indent=1))
    return 0 if solve.success else 2


if __name__ == '__main__':
    raise SystemExit(main())
