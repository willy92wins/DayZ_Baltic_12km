"""Exhaustive analytic shared-edge census; separate hydraulic contacts from dry divides."""
from pathlib import Path
import hashlib, json, sys
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
W = Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B = Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
sys.path.insert(0, str(W / 'tools/terrain'))
from v30_common import cell_planes
from audit_pond_topology import domain


def submerged_fraction(a, b, water):
    """Exact portion of a linear edge strictly below both adjacent water levels."""
    low, high = np.minimum(a, b), np.maximum(a, b)
    return np.where(high - low > 1e-12, np.clip((water - low) / np.maximum(high - low, 1e-12), 0, 1), (water > low).astype(float))


def main():
    source = B / 'measured-bank-bed-r2/terrain.npz'
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    assert digest == 'e7daa6c62cde457b666507ec7eae7e6d16015ad714028585fdb352ace678e52c'
    t = np.load(source)
    h = t['heights'].astype(float)
    p = cell_planes(t['cls'], t['level'], sea_cut=.51)
    n = p.shape[0]
    active = np.isfinite(p) & (np.minimum.reduce([h[:-1, :-1], h[:-1, 1:], h[1:, :-1], h[1:, 1:]]) < p - 1e-5)
    ids = np.full(p.shape, -1, np.int32)
    ids[active] = np.arange(int(active.sum()))
    edges = []
    summaries = []
    for axis in [0, 1]:
        if axis == 0:
            a, b = p[:-1], p[1:]
            left, right = ids[:-1], ids[1:]
            h0, h1 = h[1:-1, :-1], h[1:-1, 1:]
        else:
            a, b = p[:, :-1], p[:, 1:]
            left, right = ids[:, :-1], ids[:, 1:]
            h0, h1 = h[:-1, 1:-1], h[1:, 1:-1]
        both = (left >= 0) & (right >= 0)
        fraction = submerged_fraction(h0, h1, np.minimum(a, b))
        contact = both & (fraction > 1e-8)
        changed = both & (np.abs(a - b) > .001)
        rr, cc = np.nonzero(changed)
        for r, c in zip(rr, cc):
            edges.append((axis, int(r), int(c), float(a[r, c]), float(b[r, c]), float(fraction[r, c]), bool(contact[r, c])))
        summaries.append(dict(axis=axis, adjacent_active=int(both.sum()), wet_contacts=int(contact.sum()),
            differing_planes=int(changed.sum()), wet_differing_planes=int((changed & contact).sum()),
            dry_divides_differing_planes=int((changed & ~contact).sum()),
            length_wet_steps_m=float((fraction[changed & contact] * 6).sum()),
            max_wet_step_m=float(np.max(np.abs(a[changed & contact] - b[changed & contact]), initial=0))))
        if axis == 0:
            ii, jj = left[contact], right[contact]
        else:
            ii, jj = np.concatenate([ii, left[contact]]), np.concatenate([jj, right[contact]])
    graph = coo_matrix((np.ones(len(ii), np.uint8), (ii, jj)), shape=(int(active.sum()), int(active.sum()))).tocsr()
    ncomp, labels = connected_components(graph, directed=False)
    grid = np.full(p.shape, -1, np.int32)
    grid[active] = labels
    np.savez_compressed(B / 'water-connection-fields.npz', component=grid, plane=p, active=active)
    # Analytic fixtures independent of the map: half-edge, entirely dry divide, flat wet edge.
    cases = [(-1., 1., 0., .5), (2., 3., 1., 0.), (0., 0., 1., 1.), (1., 1., 1., 0.)]
    for x, y, w, expected in cases:
        assert abs(float(submerged_fraction(np.array(x), np.array(y), np.array(w))) - expected) < 1e-12
    rows = []
    for axis, r, c, a, b, frac, wet in edges:
        r2, c2 = (r + 1, c) if axis == 0 else (r, c + 1)
        rows.append(dict(axis=axis, row=r, col=c, level_a=a, level_b=b, difference_m=abs(a-b),
            wet_contact_length_m=frac*6, wet_contact=wet, component_a=int(grid[r,c]), component_b=int(grid[r2,c2]),
            x=6*c+(3 if axis==0 else 6), z=12282-6*r-(6 if axis==0 else 3)))
    exact_domain = domain(h, p)
    # One cell can contain two disconnected wet triangles. Do not call the
    # coarser one-node-per-cell graph a hydraulic connectivity certificate.
    fixture = domain(np.array([[2., 0.], [0., 2.]]), np.ones((1, 1)))
    assert len(fixture['body_area']) == 2
    report = dict(status='ANALYTIC_POND_CONNECTION_INVENTORY_NOT_RENDER_ACCEPTANCE', terrain_sha256=digest,
        active_cells=int(active.sum()), cell_graph_groups_not_hydraulic_components=int(ncomp),
        native_triangle_components=int(len(exact_domain['body_area'])),
        native_triangle_components_gt1m2=int((exact_domain['body_area']>=1).sum()), axes=summaries,
        wet_steps_over_35cm=sum(q['wet_contact'] and q['difference_m']>.35001 for q in rows),
        independent_linear_edge_controls='PASS_4', opposite_wet_corners_remain_two_components=True,
        largest_wet=sorted([q for q in rows if q['wet_contact']],key=lambda q:-q['difference_m'])[:30],
        limits=['Uses exact terrain edge interpolation and frozen horizontal pond planes, not shader displacement.',
                'Some 538 visible meshes are already stitched; this predicts source level steps, not remaining visible defects.',
                'An indirect connection elsewhere does not authorize averaging a local dry divide.',
                'water-connection-fields component is a coarse cell-graph label; exact hydraulic counts use both native triangles separately.'])
    (B / 'water-connections.json').write_text(json.dumps(report, indent=2)+'\n')
    (B / 'water-connection-edges.json').write_text(json.dumps(rows)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='largest_wet'},indent=2))


if __name__ == '__main__':
    main()
