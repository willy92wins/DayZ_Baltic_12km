"""Read-only inventory of mixed land/water faces; no terrain edits or new PASS gate.

Native diagonal and gradients: v30_common.py:1-4, verify_terrain_v30.py:85-94.
Both triangles must be inspected separately; a cell is not a terrain face.
"""
from pathlib import Path
import argparse
import hashlib
import json

import numpy as np

CLASSES = {1: 'mar', 2: 'lagos', 3: 'navegables', 4: 'delta',
           5: 'rios', 6: 'arroyos', 7: 'lagunas'}


def faces(h, cls, cell=6.0):
    if h.ndim != 2 or h.shape != cls.shape or not np.isfinite(h).all():
        raise ValueError('Invalid height/class grid')
    if min(h.shape) < 2 or cell <= 0 or not np.isin(cls, range(8)).all():
        raise ValueError('Invalid dimensions, cell or classes')
    heights = [h[:-1, :-1], h[:-1, 1:], h[1:, :-1], h[1:, 1:]]
    codes = [cls[:-1, :-1], cls[:-1, 1:], cls[1:, :-1], cls[1:, 1:]]
    result = []
    for label, ids in [('NW_NE_SE', (0, 1, 3)), ('NW_SW_SE', (0, 2, 3))]:
        a, b, c = [heights[i] for i in ids]
        ca, cb, cc = [codes[i] for i in ids]
        wet = (ca > 0).astype('uint8') + (cb > 0) + (cc > 0)
        mixed = (wet > 0) & (wet < 3)
        r, col = np.nonzero(mixed)
        angle = np.degrees(np.arctan(np.hypot((b-a)/cell, (c-b)/cell)))
        # A bitmask preserves faces shared by multiple water classes without
        # choosing an arbitrary dominant class. Counts by class may overlap.
        signatures = np.zeros(len(r), dtype='uint16')
        for code in (ca[r, col], cb[r, col], cc[r, col]):
            signatures |= np.where(code > 0, 1 << code, 0).astype('uint16')
        result.append(dict(triangle=label, rows=r, cols=col,
                           slopes=angle[r, col], signatures=signatures))
    return result


def controls():
    # Analytic plane z=2*x has arctan(2) slope on both native triangles.
    h = np.array([[0., 12.], [0., 12.]])
    cls = np.array([[0, 1], [0, 1]], dtype='uint8')
    found = faces(h, cls)
    assert sum(len(f['rows']) for f in found) == 2
    assert all(np.allclose(f['slopes'], np.degrees(np.arctan(2))) for f in found)
    assert all(np.all(f['signatures'] == 2) for f in found)
    assert all(len(f['rows']) == 0 for f in faces(h, np.zeros_like(cls)))
    assert all(len(f['rows']) == 0 for f in faces(h, np.ones_like(cls)))
    assert all(np.all(f['slopes'] == 0) for f in faces(np.zeros_like(h), cls))
    # Only the NW_NE_SE face is mixed when NE is the single wet corner.
    one = faces(h, np.array([[0, 3], [0, 0]], dtype='uint8'))
    assert [len(f['rows']) for f in one] == [1, 0]
    bad = h.copy(); bad[0, 0] = np.nan
    try:
        faces(bad, cls)
    except ValueError:
        pass
    else:
        raise AssertionError('NaN must fail')
    return ['analytic_slope_both_triangles', 'all_dry_excluded', 'all_wet_excluded',
            'flat_mixed_zero', 'single_triangle_identity', 'nan_rejected']


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--terrain', type=Path, required=True)
    ap.add_argument('--expected-sha256', required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    digest = hashlib.sha256(a.terrain.read_bytes()).hexdigest()
    if digest != a.expected_sha256 or a.out.exists():
        raise ValueError('Source mismatch or evidence destination already exists')
    checks = controls()
    with np.load(a.terrain) as t:
        h, cls = t['heights'].astype(float), t['cls'].copy()
        if h.shape != (2048, 2048):
            raise ValueError('This report uses the approved Baltic 2048/6m grid')
        surface = faces(h, cls)
    all_slopes = np.concatenate([f['slopes'] for f in surface])
    signatures = np.concatenate([f['signatures'] for f in surface])
    per_class = {}
    for code, name in CLASSES.items():
        s = all_slopes[(signatures & (1 << code)) != 0]
        per_class[name] = dict(faces=len(s), over_35=int((s > 35).sum()),
                              max_deg=float(s.max()) if len(s) else None)
    clusters, features = {}, []
    for f in surface:
        for i in np.flatnonzero(f['slopes'] > 35):
            r, c = int(f['rows'][i]), int(f['cols'][i])
            upper = f['triangle'] == 'NW_NE_SE'
            x = c*6 + (4 if upper else 2)
            z = 12282 - r*6 - (2 if upper else 4)
            key = (int(x//250), int(z//250))
            cl = clusters.setdefault(key, dict(cell_250m_xz=list(key), count=0,
                max_deg=0., water_classes=set(), bounds_xz=[key[0]*250, key[1]*250,
                                                          (key[0]+1)*250, (key[1]+1)*250]))
            code_list = [code for code in CLASSES if f['signatures'][i] & (1 << code)]
            cl['count'] += 1
            cl['max_deg'] = max(cl['max_deg'], float(f['slopes'][i]))
            cl['water_classes'].update(CLASSES[code] for code in code_list)
            corners = [[c*6, 12282-r*6], [(c+1)*6, 12282-r*6],
                       [c*6, 12282-(r+1)*6], [(c+1)*6, 12282-(r+1)*6]]
            xy = [corners[j] for j in ((0, 1, 3) if upper else (0, 2, 3))]
            features.append(dict(type='Feature', properties=dict(row=r, col=c,
                triangle=f['triangle'], slope_deg=float(f['slopes'][i]),
                water_classes=[CLASSES[j] for j in code_list]),
                geometry=dict(type='Polygon', coordinates=[xy+[xy[0]]])))
    ordered = sorted(clusters.values(), key=lambda c: (-c['count'], -c['max_deg']))
    for c in ordered:
        c['water_classes'] = sorted(c['water_classes'])
    report = dict(status='DIAGNOSTIC_ONLY_NO_TERRAIN_CHANGE', terrain=str(a.terrain),
        terrain_sha256=digest, script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        controls=checks, mixed_faces=len(all_slopes), over_35=int((all_slopes > 35).sum()),
        max_deg=float(all_slopes.max()), by_water_class=per_class, hotspots_250m=ordered,
        limits=['Geometric slopes of mixed vertex-class triangles, not visibility or flooding proof.',
                'Each class counts shared faces; class totals need not equal the global total.',
                'Includes protected Narva, bridges and road reserves; not every steep face can be changed.',
                'No change to the existing acceptance gates and no smoothing or deployment.'])
    a.out.mkdir(parents=True)
    (a.out/'summary.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    # This is local metre-space JSON, not RFC7946 lon/lat GeoJSON.
    (a.out/'steep-faces-game-xz.json').write_text(json.dumps(dict(type='FeatureCollection',
        coordinate_space='Baltic game X/Z metres, origin SW, no geographic CRS',
        features=features))+'\n', encoding='utf-8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 9))
    ax.imshow(cls, extent=(-3, 12285, -3, 12285), origin='upper', cmap='Blues',
              interpolation='nearest', alpha=.25)
    for rank, cl in enumerate(ordered[:15], 1):
        x0, z0, x1, z1 = cl['bounds_xz']
        ax.add_patch(plt.Rectangle((x0,z0),250,250,facecolor='#b04416',alpha=.3))
        ax.text((x0+x1)/2, (z0+z1)/2, str(rank), ha='center', va='center', fontsize=8)
    ax.set(xlim=(0,12288), ylim=(0,12288), xlabel='X local (m)', ylabel='Z local (m)',
           title='V30 — 15 zonas con más caras de orilla por encima de 35°')
    ax.set_aspect('equal'); ax.grid(alpha=.2)
    fig.text(.5,.015,'Diagnóstico geométrico; no prueba visual ni lista de cambios aprobados.',
             ha='center', fontsize=9)
    fig.tight_layout(rect=(0,.03,1,1)); fig.savefig(a.out/'hotspots.png',dpi=140); plt.close(fig)
    print(json.dumps({k:report[k] for k in ['status','mixed_faces','over_35','max_deg','by_water_class']}))


if __name__ == '__main__':
    main()
