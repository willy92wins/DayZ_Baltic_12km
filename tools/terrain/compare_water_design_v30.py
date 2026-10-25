"""Compare the approved vector water design with a candidate's physical envelope.

The independent reference is water_v3.geojson plus approved stream candidates
(tier >= 2500 m), not the candidate's own raster classification. Native terrain
triangles and existing pond planes predict water at sea levels 0.5/0.75/1 m.
Results diagnose representation loss; they are not an engine or navigation PASS.
Overlapping vector bodies are measured independently, never summed as map area.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from affine import Affine
from rasterio.features import rasterize
from shapely.geometry import shape

from v30_common import cell_planes, tri_sample

ROOT = Path(__file__).resolve().parents[2]
SEAS = (.5, .75, 1.)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sample_body(geom, heights, planes, step=1.):
    """Raster pixel centres in a tight local bbox; process at most 128 rows."""
    x0, z0, x1, z1 = geom.bounds
    x0, z0 = max(0., math.floor(x0/step)*step), max(0., math.floor(z0/step)*step)
    x1, z1 = min(12282., math.ceil(x1/step)*step), min(12282., math.ceil(z1/step)*step)
    w, h = math.ceil((x1-x0)/step), math.ceil((z1-z0)/step)
    if w <= 0 or h <= 0:
        return dict(samples=0, reason='outside native grid')
    xs = x0+(np.arange(w)+.5)*step
    total, counts, depths = 0, np.zeros(3, dtype=np.int64), []
    plane_covered = 0
    for r in range(0, h, 128):
        n = min(128, h-r)
        north = z1-r*step
        mask = rasterize([(geom, 1)], out_shape=(n,w),
                         transform=Affine(step,0,x0,0,-step,north), dtype='uint8') > 0
        if not mask.any():
            continue
        xx, zz = np.meshgrid(xs, north-(np.arange(n)+.5)*step)
        x, z = xx[mask], zz[mask]
        ground = tri_sample(heights,x,z)
        rr = np.clip(np.floor((12282-z)/6).astype(int),0,2046)
        cc = np.clip(np.floor(x/6).astype(int),0,2046)
        pond = planes[rr,cc]
        plane_covered += int(np.isfinite(pond).sum())
        pond = np.nan_to_num(pond, nan=-np.inf)
        for i, sea in enumerate(SEAS):
            counts[i] += int((ground < np.maximum(pond,sea)).sum())
        depths.append(np.maximum(pond,.75)-ground)
        total += len(ground)
    if not total:
        return dict(samples=0, reason='no pixel centres inside vector')
    depth = np.concatenate(depths)
    return dict(samples=total, sampled_area_m2=total*step*step,
                wet_fraction={str(s):float(n/total) for s,n in zip(SEAS,counts)},
                pond_plane_fraction=plane_covered/total,
                nominal_depth_percentiles_m={str(p):float(np.percentile(depth,p)) for p in (0,5,50,95)},
                nominal_depth_at_least_1m_fraction=float((depth>=1.).mean()),
                nominal_depth_at_least_2m_fraction=float((depth>=2.).mean()))


def draw(geom, heights, planes, row, target):
    x0,z0,x1,z1 = geom.bounds
    pad = max(12., .06*max(x1-x0,z1-z0))
    x0,z0,x1,z1 = max(0,x0-pad),max(0,z0-pad),min(12282,x1+pad),min(12282,z1+pad)
    w,h = max(16,int(x1-x0)),max(16,int(z1-z0))
    scale = max(w,h)/700
    if scale>1:
        w,h=max(16,int(w/scale)),max(16,int(h/scale))
    xx,zz=np.meshgrid(np.linspace(x0,x1,w),np.linspace(z1,z0,h))
    ground=tri_sample(heights,xx,zz)
    rr=np.clip(np.floor((12282-zz)/6).astype(int),0,2046)
    cc=np.clip(np.floor(xx/6).astype(int),0,2046)
    depth=np.maximum(np.nan_to_num(planes[rr,cc],nan=-np.inf),.75)-ground
    fig,ax=plt.subplots(figsize=(8,7),dpi=140)
    ax.imshow(ground,extent=(x0,x1,z0,z1),origin='upper',cmap='gist_earth',alpha=.55)
    ax.contourf(xx,zz,depth,levels=[0,1000],colors=['#218fc9'],alpha=.8)
    parts=list(geom.geoms) if hasattr(geom,'geoms') else [geom]
    for part in parts:
        x,z=part.exterior.xy
        ax.plot(x,z,color='#db2525',lw=1.2)
        for ring in part.interiors:
            x,z=ring.xy
            ax.plot(x,z,color='#db2525',lw=1.2)
    ax.set(xlabel='Game X (m)',ylabel='Game Z (m)',aspect='equal',
           title=f"{row['key']} | {row['class']}\nVector rojo / agua nominal predicha azul\n"
                 f"Cobertura {100*row['wet_fraction']['0.75']:.1f}% — diagnóstico offline")
    fig.tight_layout();fig.savefig(target);plt.close(fig)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--candidate',type=Path,required=True)
    ap.add_argument('--expected-sha256',required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    assert sha(a.candidate)==a.expected_sha256.lower()
    assert not a.out.exists(), 'Fresh output required'
    water=ROOT/'tests/water_v3/water_v3.geojson'
    streams=ROOT/'tests/water_v3/streams_candidates.geojson'
    feats=json.loads(water.read_text(encoding='utf-8'))['features']
    feats += [f for f in json.loads(streams.read_text(encoding='utf-8'))['features']
              if f['properties']['tier_m']>=2500]
    t=np.load(a.candidate)
    heights=t['heights'].astype(float)
    planes=cell_planes(t['cls'],t['level'])
    rows=[];geoms=[]
    for i,feat in enumerate(feats):
        geom=shape(feat['geometry']);prop=feat['properties']
        assert geom.is_valid and not geom.is_empty, (i,prop)
        row=dict(index=i,key=str(prop.get('id',i)),**{'class':prop['class']},
                 name=prop.get('river',prop.get('name','')), vector_area_m2=float(geom.area),
                 representative_xz=list(geom.representative_point().coords[0]),
                 **sample_body(geom,heights,planes))
        rows.append(row);geoms.append(geom)
    groups={}
    for code in sorted(set(r['class'] for r in rows)):
        subset=[r for r in rows if r['class']==code and r['samples']]
        fractions=[r['wet_fraction']['0.75'] for r in subset]
        groups[code]=dict(bodies=len(subset),coverage_min=float(min(fractions)),
                          coverage_median=float(np.median(fractions)),
                          diagnostic_under_50pct=sum(f<.5 for f in fractions),
                          diagnostic_under_80pct=sum(f<.8 for f in fractions),
                          completely_dry=sum(f==0 for f in fractions))
    worst=sorted((r for r in rows if r['samples']),key=lambda r:r['wet_fraction']['0.75'])[:12]
    result=dict(status='MEASURED_OFFLINE_DESIGN_COVERAGE',terrain_sha256=sha(a.candidate),
                sources={str(p):sha(p) for p in (water,streams)},resolution_m=1.,sea_levels_m=SEAS,
                groups=groups,worst=worst,bodies=rows,
                limits=['No engine, visuals, swimming, boating or navmesh acceptance.',
                        'Sea and pond envelope uses the higher physical plane, not proof that a low pond exists.',
                        'Vector polygons overlap; per-body areas must not be summed as total map area.',
                        'Boundary representation on a 6 m height grid can lose design area; percentages are diagnostics, not new product thresholds.',
                        'Scope: approved V3 navigable/rivers/delta/ponds and >=2500 m streams; preserved lakes and full sea coast are outside this comparison.'])
    a.out.mkdir(parents=True)
    (a.out/'coverage.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    for order,row in enumerate(worst):
        draw(geoms[row['index']],heights,planes,row,a.out/f'{order+1:02d}-{row["index"]}.png')
    print(json.dumps(dict(status=result['status'],groups=groups,worst=[{k:r[k] for k in ('key','class','wet_fraction')} for r in worst]),indent=2))


if __name__=='__main__':main()
