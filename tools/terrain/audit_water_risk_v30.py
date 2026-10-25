"""Census of geometric water risk on every V30 native vertex and face.

Consumer: terrain authoring/release review. Produces coordinates for every lowland
component and checks calibrated observations. It never certifies native rendering
from SurfaceY, a configured tide, or an empty set of screenshot detections.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy import ndimage
from v30_common import tri_sample, cell_planes

TOLERANCE = 1e-5  # Stored float32(1.8) lies about 4.8e-8 below the nominal target.


def clearance_depths(threshold, heights):
    return threshold-TOLERANCE-np.asarray(heights, dtype=float)


def clipped_area(depth):
    """Area below a horizontal threshold, exactly on a native 18 m2 triangle."""
    d = np.asarray(depth, dtype=float)
    pos = d > 0
    count = pos.sum(-1)
    area = np.where(count == 3, 18., 0.)
    for i in range(3):
        j, k = [n for n in range(3) if n != i]
        one = (count == 1) & pos[..., i]
        two = (count == 2) & ~pos[..., i]
        for mask, complement in ((one, False), (two, True)):
            a, b, c = d[mask, i], d[mask, j], d[mask, k]
            fraction = a / (a-b) * a / (a-c)
            area[mask] = 18 * (1-fraction if complement else fraction)
    return area


def analytical_controls():
    values = clipped_area(np.array([[1., -1, -1], [1, 1, -1], [1, 1, 1], [-1, -1, -1]]))
    assert np.allclose(values, [4.5, 13.5, 18, 0])
    assert clipped_area(np.array([[0., 0., 0.]])).item() == 0
    stored = np.full((1,3),1.8,dtype=np.float32)
    assert clipped_area(clearance_depths(1.8,stored)).item() == 0
    return dict(half_edge_triangle=bool(values[0] == 4.5), complement=bool(values[1] == 13.5),
                full_positive=bool(values[2] == 18), high_negative=bool(values[3] == 0), equality_excluded=True,
                float32_nominal_target_excluded=True)


def pond_risks(terrain, water_source, water_sha, water_manifest, out):
    """Inventory dry vertices against every incident frozen pond plane, independent of native presence flags."""
    digest = hashlib.sha256(water_source.read_bytes()).hexdigest()
    if digest != water_sha:
        raise ValueError('Water source hash does not match its reference')
    water = dict(np.load(water_source))
    manifest = json.loads(water_manifest.read_text(encoding='utf-8'))
    cutoff = float(manifest['sea_cutoff_m'])
    plane = cell_planes(water['cls'], water['level'], sea_cut=cutoff)
    h, dry = terrain['heights'].astype(float), terrain['cls'] == 0
    maximum = np.full(h.shape, -np.inf)
    values = np.where(np.isfinite(plane), plane, -np.inf)
    for dr, dc in ((0, 0), (0, 1), (1, 0), (1, 1)):
        view = maximum[dr:dr+2047, dc:dc+2047]
        np.maximum(view, values, out=view)
    nominal = dry & (h < maximum-TOLERANCE)
    screening = dry & (h < maximum+.35-TOLERANCE)
    rows = []
    for r, c in np.argwhere(screening):
        rows.append(dict(row=int(r), col=int(c), x=int(c*6), z=int(12282-r*6),
            ground_m=float(h[r,c]), highest_incident_plane_m=float(maximum[r,c]),
            nominally_submerged=bool(nominal[r,c]), clearance_m=float(h[r,c]-maximum[r,c]),
            **{name:bool(terrain[name][r,c]) for name in ('reserve','platform','beach')}))
    with (out/'pond-dry-vertices.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]) if rows else ['row','col'])
        writer.writeheader();writer.writerows(rows)
    area=0.;faces=0
    for dr,dc in ((0,1),(1,0)):
        selected=dry[:-1,:-1]&dry[dr:dr+2047,dc:dc+2047]&dry[1:,1:]&np.isfinite(plane)
        heights=np.stack([h[:-1,:-1][selected],h[dr:dr+2047,dc:dc+2047][selected],h[1:,1:][selected]],axis=-1)
        submerged=clipped_area(plane[selected,None]-TOLERANCE-heights)
        area+=float(submerged.sum());faces+=int((submerged>1e-8).sum())
    return dict(water_source=str(water_source),water_source_sha256=digest,
        manifest_sha256=hashlib.sha256(water_manifest.read_bytes()).hexdigest(),sea_cutoff_m=cutoff,
        nominally_submerged_dry_vertices=int(nominal.sum()),dry_vertices_within_35cm=int(screening.sum()),
        fully_dry_faces_with_pond_area=faces,pond_area_on_fully_dry_faces_m2=area,
        limits=['Frozen source planes; exact compiled footprints and temporal depth remain separate consumers.',
                '35 cm is a bank-clearance screening value, not a proven wave envelope. Shore contact is not automatically an inland flooding defect.'])


def audit(source, expected_sha, out, projection, sea_max=.85, empirical=1.8,
          water_source=None, water_sha=None, water_manifest=None):
    sha = hashlib.sha256(source.read_bytes()).hexdigest()
    if sha != expected_sha:
        raise ValueError('Source hash does not match the package reference')
    if out.exists():
        raise ValueError('Use a fresh output directory to preserve prior evidence')
    if any(v is not None for v in (water_source,water_sha,water_manifest)) and not all(v is not None for v in (water_source,water_sha,water_manifest)):
        raise ValueError('Pond audit requires water source, its hash and the production manifest together')
    t = dict(np.load(source))
    h = t['heights'].astype(float)
    if h.shape != (2048, 2048) or not np.isfinite(h).all():
        raise ValueError('Expected finite native 2048 x 2048 terrain')
    dry = t['cls'] == 0
    low = dry & (h < empirical-1e-5)
    physical = dry & (h < sea_max-1e-5)
    wet_distance = ndimage.distance_transform_edt(dry, sampling=6.)
    support = np.zeros_like(dry)
    face_counts = dict(total=0, fully_dry=0, low_fully_dry=0, dry_sea_intersections=0,
                       dry_low_area_m2=0., dry_below_sea_area_m2=0.)
    for dr, dc in ((0, 1), (1, 0)):
        ds = [dry[:-1, :-1], dry[dr:dr+2047, dc:dc+2047], dry[1:, 1:]]
        all_dry = np.logical_and.reduce(ds)
        mixed = ~all_dry
        for rr, cc in ((0, 0), (dr, dc), (1, 1)):
            support[rr:rr+2047, cc:cc+2047] |= mixed
        heights = np.stack([h[:-1, :-1], h[dr:dr+2047, dc:dc+2047], h[1:, 1:]], axis=-1)
        values = heights[all_dry]
        lo = clipped_area(clearance_depths(empirical,values))
        below = clipped_area(clearance_depths(sea_max,values))
        face_counts['total'] += all_dry.size
        face_counts['fully_dry'] += int(all_dry.sum())
        face_counts['low_fully_dry'] += int((lo > 1e-8).sum())
        face_counts['dry_sea_intersections'] += int((below > 1e-8).sum())
        face_counts['dry_low_area_m2'] += float(lo.sum())
        face_counts['dry_below_sea_area_m2'] += float(below.sum())
    assert face_counts['total'] == 2*2047**2
    structure = np.array([[1, 1, 0], [1, 1, 1], [0, 1, 1]], bool)
    labels, n = ndimage.label(low, structure)
    rows = []
    for ident, sl in enumerate(ndimage.find_objects(labels), 1):
        if sl is None:
            continue
        rr, cc = np.nonzero(labels[sl] == ident)
        rr += sl[0].start
        cc += sl[1].start
        k = np.argmin(h[rr, cc])
        masks = {name: t[name][rr, cc] for name in ('reserve', 'platform', 'beach')}
        fixed = np.logical_or.reduce(list(masks.values()))
        reason = 'engineering_or_beach' if fixed.all() else 'shore_transition' if support[rr, cc].all() else 'interior_or_mixed'
        rows.append(dict(id=ident,vertices=len(rr),x=int(cc[k]*6),z=int(12282-rr[k]*6),
            minimum_m=float(h[rr[k],cc[k]]),maximum_m=float(h[rr,cc].max()),reason=reason,
            below_measured_sea=int(physical[rr,cc].sum()),
            water_face_support=int(support[rr,cc].sum()),beyond_18m_water=int((wet_distance[rr,cc]>18).sum()),
            **{name+'_vertices':int(mask.sum()) for name,mask in masks.items()}))
    out.mkdir(parents=True)
    with (out/'components.csv').open('w', newline='', encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]) if rows else ['id'])
        writer.writeheader();writer.writerows(rows)
    observations=[]
    if projection:
        registered=json.loads(projection.read_text(encoding='utf-8'))
        if registered['status']!='NATIVE_PROJECTION_CALIBRATED':
            raise ValueError('Observations require native camera calibration')
        for p in registered['points']:
            x,_,z=p['world'];r=int(round((12282-z)/6));c=int(round(x/6))
            ground=float(tri_sample(h,x,z))
            observations.append(dict(name=p['name'],x=x,z=z,ground_m=ground,nearest_vertex_class=int(t['cls'][r,c]),
                empirical_risk=bool(ground<empirical-1e-5 and dry[r,c]),component=int(labels[r,c]),
                vertex_distance_to_water_m=float(wet_distance[r,c])))
    np.savez_compressed(out/'masks.npz',lowland=low,physical_subsea=physical,labels=labels,water_face_support=support)
    report=dict(status='RISK_INVENTORY_RENDER_GATE_OPEN',source=str(source),source_sha256=sha,
        grid=dict(vertices=h.size,faces=face_counts['total'],cell_m=6),thresholds=dict(measured_physical_sea_max_m=sea_max,empirical_m=empirical),
        counts=dict(dry_vertices=int(dry.sum()),low_vertices=int(low.sum()),physical_subsea_vertices=int(physical.sum()),
                    low_away_from_water_faces=int((low&~support).sum()),components=n),faces=face_counts,
        observations=observations,analytical_controls=analytical_controls(),
        limits=['All source vertices and both native triangles are evaluated; compiled rendering is a separate consumer.',
                '1.80 m is an empirical screening threshold, not a proven sea-shader upper bound.',
                'Classified shoreline/engineering risks remain in the census; classification is not acceptance.',
                'Areas use fully dry source faces. Mixed shore faces remain in the vertex inventory, not the area sum.',
                'No hypothetical coarse grid is used as a native LOD or as authority to edit heights.'])
    if water_source is not None:
        report['ponds']=pond_risks(t,water_source,water_sha,water_manifest,out)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report


if __name__ == '__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--source-sha',required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--projection',type=Path)
    ap.add_argument('--water-source',type=Path)
    ap.add_argument('--water-sha')
    ap.add_argument('--water-manifest',type=Path)
    args=ap.parse_args()
    result=audit(args.source,args.source_sha,args.out,args.projection,
                 water_source=args.water_source,water_sha=args.water_sha,water_manifest=args.water_manifest)
    print(json.dumps({k:v for k,v in result.items() if k not in ('observations','limits')},indent=2))
