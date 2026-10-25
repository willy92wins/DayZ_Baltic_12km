"""Classify the water that audit_visible_water_v30.py found outside the designed outline (BALTIC-016).

Every flooded component (8-connected 2 m pixels) gets one zone, checked in this order: map border (within 16 m of the
edge), Narva (half its pixels on the terrain's narva mask), delta (half its pixels on terrain delta vertices, class 4),
coast (within 30 m of the designed sea), bank (within 30 m of designed inland water), inland. The report adds the area
inside the protected 24 m corridors and the land vertices below the audited sea level (beach, Narva, other): land above
the highest sea surface cannot be reached by the engine sea at all.
Usage: classify_visible_water_v30.py --audit DIR [DIR ...] --out JSON [--overview PNG]
                                     [--crops PNG --views name:x:z,... [--crops-extra DIR]]
The figures use the first audit; --crops-extra marks in orange what another audit of the same terrain adds.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys
from types import SimpleNamespace

import numpy as np
from rasterio.features import rasterize
from scipy import ndimage as ndi
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'tools' / 'terrain'), str(ROOT / 'tools' / 'water')]
import audit_visible_water_v30 as A  # noqa: E402
from v30_common import N  # noqa: E402

ZONES = ('border', 'narva', 'delta', 'coast', 'bank', 'inland')
COLOURS = {'border': (0.35, 0.35, 0.35), 'narva': (0.55, 0.2, 0.75), 'delta': (0.95, 0.2, 0.75),
           'coast': (0.0, 0.75, 0.8), 'bank': (0.9, 0.1, 0.1), 'inland': (0.0, 0.0, 0.0)}
CORRIDORS = [ROOT / 'evidence/v30-offline-followup-2026-10-02/corridors.geojson',
             ROOT / 'evidence/v30-delta-fairways-2026-10-02/axes-corridors.geojson']
S = A.S
VR = np.clip(np.rint((1 + 2 * np.arange(S)) / 6.0).astype(int), 0, N - 1)  # nearest vertex of each pixel row/column


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def to_px(v):
    return v[VR][:, VR]


def corridor_mask():
    geoms = [shape(f['geometry']) for p in CORRIDORS for f in json.loads(p.read_text(encoding='utf-8'))['features']
             if f['properties'].get('kind', 'corridor24m') == 'corridor24m']
    return rasterize([(g, 1) for g in geoms], out_shape=(S, S), transform=A.TRANSFORM, fill=0, dtype='uint8') > 0


def classify(audit_dir, d_sea, d_inl, corr):
    doc = json.loads((audit_dir / 'audit.json').read_text(encoding='utf-8'))
    prm = doc['params']
    assert sha(doc['terrain']) == doc['terrain_sha256'], 'terrain changed since the audit'
    t = np.load(doc['terrain'])
    surf, ter, cause, vis = A.visible_fields(t['heights'], t['cls'], t['level'], prm, A.load_pieces(prm['channels']))
    m = np.load(audit_dir / 'masks.npz')
    assert (vis == m['visible']).all(), 'recomputed visibility differs from the audit'
    flooded, holes = m['flooded'], m['holes']
    lab, n = ndi.label(flooded, structure=np.ones((3, 3)))
    idx = np.arange(1, n + 1)
    st = {'area': ndi.sum(flooded, lab, idx), 'narva': ndi.mean(to_px(t['narva']), lab, idx),
          'delta': ndi.mean(to_px(t['cls'] == 4), lab, idx), 'dsea': ndi.minimum(d_sea, lab, idx),
          'dinl': ndi.minimum(d_inl, lab, idx), 'depth': ndi.maximum(surf - ter, lab, idx),
          'tmin': ndi.minimum(ter, lab, idx), 'sea': ndi.mean(cause == 1, lab, idx), 'corr': ndi.sum(corr, lab, idx)}
    rows, zone_of = [], np.zeros(n + 1, np.uint8)
    for k, sl in enumerate(ndi.find_objects(lab)):
        if sl[0].start <= 8 or sl[1].start <= 8 or sl[0].stop >= S - 8 or sl[1].stop >= S - 8:
            zone = 'border'
        elif st['narva'][k] >= 0.5:
            zone = 'narva'
        elif st['delta'][k] >= 0.5:
            zone = 'delta'
        elif st['dsea'][k] <= 30:
            zone = 'coast'
        elif st['dinl'][k] <= 30:
            zone = 'bank'
        else:
            zone = 'inland'
        zone_of[k + 1] = ZONES.index(zone) + 1
        jj, ii = np.nonzero(lab[sl] == k + 1)
        rows.append({'zone': zone, 'area_m2': float(st['area'][k] * 4),
                     'centroid': [round(float((1 + 2 * (sl[1].start + ii)).mean())),
                                  round(float((12281 - 2 * (sl[0].start + jj)).mean()))],
                     'sea_cause_frac': round(float(st['sea'][k]), 2), 'max_depth_m': round(float(st['depth'][k]), 2),
                     'terrain_min_m': round(float(st['tmin'][k]), 2), 'in_corridors_m2': float(st['corr'][k] * 4),
                     'dist_design_sea_m': round(float(st['dsea'][k]), 1),
                     'dist_design_inland_m': round(float(st['dinl'][k]), 1)})
    rows.sort(key=lambda r: -r['area_m2'])
    zones = {}
    for z in ZONES:
        sel = [r for r in rows if r['zone'] == z]
        zones[z] = {'components': len(sel), 'area_m2': round(sum(r['area_m2'] for r in sel)),
                    'sea_caused_area_m2': round(sum(r['area_m2'] * r['sea_cause_frac'] for r in sel)),
                    'in_corridors_m2': round(sum(r['in_corridors_m2'] for r in sel)), 'top': sel[:12]}
    low = (t['cls'] == 0) & (t['heights'].astype(np.float64) < prm['sea_level'] - 1e-6)
    out = {'terrain': doc['terrain'], 'terrain_sha256': doc['terrain_sha256'], 'sea_level_m': prm['sea_level'],
           'sea_cut_m': prm['sea_cut'], 'channels': prm['channels'],
           'flooded_area_m2': round(float(flooded.sum() * 4)), 'holes_area_m2': round(float(holes.sum() * 4)),
           'zones': zones,
           'land_vertices_below_sea_level': {'beach': int((low & t['beach']).sum()),
                                             'narva': int((low & t['narva'] & ~t['beach']).sum()),
                                             'other': int((low & ~t['narva'] & ~t['beach']).sum())}}
    return out, {'vis': vis, 'flooded': flooded, 'holes': holes, 'zone': zone_of[lab], 'ter': ter, 'name': audit_dir.name}


def blockmax(b):
    p = np.zeros((6144, 6144), bool)
    p[:S, :S] = b
    return p.reshape(2048, 3, 2048, 3).max(axis=(1, 3))


def overview(path, f, design_outline_note):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    img = np.full((2048, 2048, 3), 0.82)
    img[blockmax(f['vis'])] = (0.62, 0.76, 0.95)
    for k, z in enumerate(ZONES, 1):
        img[blockmax(f['zone'] == k)] = COLOURS[z]
    img[blockmax(f['holes'])] = (1.0, 0.85, 0.0)
    fig, ax = plt.subplots(figsize=(12, 12.6))
    ax.imshow(img, extent=[0, 12288, 12282 - 12288, 12282], interpolation='nearest')
    ax.set_xlim(0, 12282)
    ax.set_ylim(0, 12282)
    ax.legend(handles=[Patch(color=(0.62, 0.76, 0.95), label='visible water')]
              + [Patch(color=COLOURS[z], label=f'outside the design: {z}') for z in ZONES]
              + [Patch(color=(1.0, 0.85, 0.0), label='designed water shown dry')], loc='lower left', fontsize=9)
    ax.set_title(f"{f['name']}: water >3 m outside the designed outline by zone ({design_outline_note})", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=110)


def crops(path, f, extra, views):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    cols = 3
    rows = (len(views) + cols - 1) // cols
    fig, axs = plt.subplots(rows, cols, figsize=(5 * cols, 5 * rows), squeeze=False)
    for ax in axs.flat[len(views):]:
        ax.axis('off')
    for ax, (name, x, z) in zip(axs.flat, views):
        i, j, h = int((x - 1) / 2), int((12281 - z) / 2), 150
        js, is_ = slice(max(j - h, 0), min(j + h, S)), slice(max(i - h, 0), min(i + h, S))
        img = np.dstack([np.clip((f['ter'][js, is_] + 2) / 12, 0, 1)] * 3) * 0.6 + 0.3
        img[f['vis'][js, is_]] = (0.55, 0.7, 0.95)
        if extra is not None:
            img[extra['flooded'][js, is_] & ~f['flooded'][js, is_]] = (1.0, 0.6, 0.1)
        img[f['flooded'][js, is_]] = (0.9, 0.1, 0.1)
        img[f['holes'][js, is_]] = (1.0, 0.9, 0.1)
        x0, z0 = 2 * is_.start, 12282 - 2 * js.start
        ax.imshow(img, extent=[x0, x0 + 2 * img.shape[1], z0 - 2 * img.shape[0], z0], interpolation='nearest')
        ax.plot([x], [z], 'k+', ms=12)
        ax.set_title(f'{name} ({x:.0f}, {z:.0f})', fontsize=9)
        ax.tick_params(labelsize=7)
    note = f", orange: added in {extra['name']}" if extra is not None else ''
    fig.suptitle(f"{f['name']}: blue visible water, red >3 m outside the design, yellow designed water shown dry{note}",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=80)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--audit', type=Path, nargs='+', required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--overview', type=Path)
    ap.add_argument('--crops', type=Path)
    ap.add_argument('--views', default='', help='name:x:z,name:x:z,...')
    ap.add_argument('--crops-extra', type=Path)
    a = ap.parse_args()
    code, _ = A.design_raster(A.design_geometries(SimpleNamespace(**A.DEFAULTS)),
                              np.load(A.DEFAULTS['ocean'])['ocean'].astype(bool))
    d_sea = ndi.distance_transform_edt(code != 7) * 2.0
    d_inl = ndi.distance_transform_edt(~((code > 0) & (code < 7))) * 2.0
    corr = corridor_mask()
    report = {'tool_sha256': sha(__file__), 'audit_tool_sha256': sha(A.__file__), 'zones_order': list(ZONES),
              'audits': {}}
    first = None
    for d in a.audit:
        res, fields = classify(d, d_sea, d_inl, corr)
        report['audits'][d.name] = res
        first = first or fields
        print(d.name, {z: (v['components'], v['area_m2']) for z, v in res['zones'].items()},
              res['land_vertices_below_sea_level'], flush=True)
    a.out.write_text(json.dumps(report, indent=1) + '\n', encoding='utf-8')
    if a.overview:
        overview(a.overview, first, 'water_v3, streams, contour-v2 lakes, smoothed v33 sea')
    if a.crops:
        extra = classify(a.crops_extra, d_sea, d_inl, corr)[1] if a.crops_extra else None
        views = [(v.split(':')[0], float(v.split(':')[1]), float(v.split(':')[2])) for v in a.views.split(',') if v]
        crops(a.crops, first, extra, views)


if __name__ == '__main__':
    main()
