"""Measure an existing proposed water field on exact visible native triangles.

Read-only consumer before model authoring. One analysis of the rejected field;
it neither changes its thresholds nor authorizes packaging from a corner census.
"""
from pathlib import Path
import csv
import hashlib
import json
import sys

import numpy as np

W = Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B = Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
sys.path.insert(0, str(W / 'tools/terrain'))
from v30_common import cell_planes

UNIT = np.eye(3)


def clip(poly, values):
    """Clip barycentric polygon by one linear strictly positive half-plane."""
    if len(poly) == 0:
        return np.empty((0, 3))
    result = []
    prev = poly[-1]
    pv = float(prev @ values)
    for cur in poly:
        cv = float(cur @ values)
        if (pv > 0) != (cv > 0):
            result.append(prev + (cur-prev) * (pv / (pv-cv)))
        if cv > 0:
            result.append(cur)
        prev, pv = cur, cv
    return np.asarray(result).reshape((-1, 3))


def area(poly):
    if len(poly) < 3:
        return 0.0
    x, y = poly[:, 1], poly[:, 2]
    return abs(float(x @ np.roll(y, -1)-y @ np.roll(x, -1))) * 18


def measure(ground, original, field):
    before = clip(UNIT, original-ground)
    after = clip(UNIT, field-ground)
    shared = clip(before, field-ground)
    a, b, common = area(before), area(after), area(shared)
    error = field-original
    max_old = float(np.max(np.abs(before @ error), initial=0)) if a > 1e-10 else 0.0
    max_new = float(np.max(np.abs(after @ error), initial=0)) if b > 1e-10 else 0.0
    excessive_old = area(clip(before, error-.35001)) + area(clip(before, -error-.35001))
    excessive_new = area(clip(after, error-.35001)) + area(clip(after, -error-.35001))
    return dict(before_area_m2=a, after_area_m2=b,
                gained_area_m2=max(0.0, b-common), lost_area_m2=max(0.0, a-common),
                max_error_on_old_visible_m=max_old, max_error_on_new_visible_m=max_new,
                old_visible_area_over_35cm_m2=excessive_old,
                new_visible_area_over_35cm_m2=excessive_new)


def controls():
    # Independent areas on an 18 m2 triangle, not a comparison to the field author.
    zero = measure(np.zeros(3), 1.0, np.ones(3))
    assert zero['before_area_m2'] == 18 and zero['gained_area_m2'] == zero['lost_area_m2'] == 0
    hidden = measure(np.full(3, 5.0), 1.0, np.full(3, 3.0))
    assert hidden['max_error_on_new_visible_m'] == hidden['max_error_on_old_visible_m'] == 0
    flood = measure(np.full(3, 1.8), 1.0, np.array([1., 2., 2.]))
    assert abs(flood['gained_area_m2']-6.48) < 1e-10
    assert flood['max_error_on_new_visible_m'] == 1.0
    loss = measure(np.zeros(3), 1.0, np.array([-1., 1., 1.]))
    assert loss['lost_area_m2'] == 4.5
    same = measure(np.ones(3), 1.0, np.ones(3))
    assert same['before_area_m2'] == same['after_area_m2'] == 0
    return ['unchanged_18m2', 'buried_2m_delta_not_visible', 'new_water_6.48m2_rejected',
            'lost_quarter_4.5m2_rejected', 'zero_depth_excluded']


def main():
    tests = controls()
    source = B / 'measured-bank-bed-r2/terrain.npz'
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    assert digest == 'e7daa6c62cde457b666507ec7eae7e6d16015ad714028585fdb352ace678e52c'
    candidate = B / 'connected_visual_corners.npy'
    field = np.load(candidate)
    t = np.load(source)
    h = t['heights'].astype(float)
    p = cell_planes(t['cls'], t['level'], sea_cut=.51)
    assert field.shape == p.shape+(4,)
    assert np.isfinite(field[np.isfinite(p)]).all()
    changed = np.isfinite(p) & (np.max(np.abs(field-p[:, :, None]), axis=-1) > 1e-10)
    out = B / 'visible-field-domain'
    assert not out.exists(), 'Preserve previous evidence; this is a single read-only analysis.'
    out.mkdir()
    records = []
    for r, c in np.argwhere(changed):
        ground = h[r:r+2, c:c+2].ravel()
        classes = t['cls'][r:r+2, c:c+2].ravel()
        for tri, corners in enumerate(([0, 1, 3], [0, 2, 3])):
            result = measure(ground[corners], p[r, c], field[r, c, corners])
            records.append(dict(row=int(r), col=int(c), tri=tri, x=int(c*6), z=int(12282-r*6),
                                fully_dry_source_face=bool(np.all(classes[corners] == 0)), **result))
    assert records, 'An empty changed-domain census is not a pass.'
    with (out / 'faces.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    summed = ['before_area_m2', 'after_area_m2', 'gained_area_m2', 'lost_area_m2',
              'old_visible_area_over_35cm_m2', 'new_visible_area_over_35cm_m2']
    totals = {key: sum(row[key] for row in records) for key in summed}
    for key in ['max_error_on_old_visible_m', 'max_error_on_new_visible_m']:
        totals[key] = max(row[key] for row in records)
    totals['new_water_on_fully_dry_source_faces_m2'] = sum(
        row['gained_area_m2'] for row in records if row['fully_dry_source_face'])
    report = dict(status='ANALYSIS_OF_REJECTED_FIELD_NO_AUTHORING', terrain_sha256=digest,
                  field_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),
                  all_grid_cells_scanned=int(p.size), changed_cells=int(changed.sum()),
                  changed_native_faces=len(records), totals=totals, controls=tests,
                  worst_faces=sorted(records, key=lambda r: -max(r['max_error_on_old_visible_m'],
                                                                r['max_error_on_new_visible_m']))[:30],
                  limits=['The field remains rejected and was not changed or written to P3D.',
                          'Exact on proposed linear native triangles; not compiled geometry, shader waves or a runtime pass.',
                          'Outside changed cells field equals the original plane; only changed faces need polygon clipping.',
                          'New and lost projected water are reported, including mixed shoreline faces. No shoreline exclusions.',
                          'The 538 currently stitched meshes remain untouched; source planes are the analytical reference.'])
    (out / 'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'worst_faces'}, indent=2))


if __name__ == '__main__':
    main()
