"""One local offline shoreline experiment; never overwrites or deploys a world."""
from pathlib import Path
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np
import shapely
from shapely.geometry import Point, box, shape

from v30_common import cell_planes, grid_xz, tri_sample, vertex_plane_bounds
from audit_fairway_triangles_v30 import records, save, sha

R = Path(__file__).resolve().parents[2]
SOURCE = Path('E:/DayZ-Baltic-Build/v30-fairway-candidate-bounded/terrain_v30.npz')
EXPECTED = '1117b4b11b38e9369ea8ad7179cd3bbbde0517e19a714968357b25fc166b36e0'
OUT = Path('E:/DayZ-Baltic-Build/v30-shore-pilot')
EV = R/'evidence/v30-shore-pilot-2026-10-02'
CENTER = (1062., 4836.)


def ease(t):
    t = np.clip(t, 0, 1)
    return t*t*t*(10+t*(-15+6*t))


def shore_segments(h, planes, rows, cols):
    segments, sampled_errors = [], []
    for r in rows:
        for c in cols:
            level = planes[r, c]
            if not np.isfinite(level):
                continue
            corners = [(r,c),(r,c+1),(r+1,c),(r+1,c+1)]
            for ids in [(0,1,3),(0,2,3)]:
                rc = [corners[i] for i in ids]
                hh = np.array([h[p] for p in rc])
                if np.min(hh) >= level or np.max(hh) <= level:
                    continue
                xy = np.array([[p[1]*6,12282-p[0]*6] for p in rc],float)
                cross = []
                for a,b in ((0,1),(1,2),(2,0)):
                    if (hh[a]-level)*(hh[b]-level) < 0:
                        f = (level-hh[a])/(hh[b]-hh[a])
                        cross.append(xy[a]+f*(xy[b]-xy[a]))
                if len(cross) != 2:
                    continue
                segments.append(np.array(cross))
                sampled_errors.extend(abs(tri_sample(h,cross[0][0],cross[0][1])-level).reshape(-1))
    assert segments and max(sampled_errors)<1e-7
    return np.array(segments)


def metrics(segments, boundary, region):
    # Uniform ~1 m sampling of the native waterline, not vertex-density weighting.
    pts=[]
    for a,b in segments:
        n=max(2,int(np.ceil(np.linalg.norm(b-a)))+1)
        pts.extend(a+(b-a)*t for t in np.linspace(0,1,n))
    pts=np.array(pts)
    keep=shapely.covers(region,shapely.points(pts))
    d=shapely.distance(shapely.points(pts[keep]),boundary)
    assert len(d)>0
    return dict(samples=len(d),mean_error_m=float(d.mean()),p95_error_m=float(np.percentile(d,95)),
                max_error_m=float(d.max()))


def mixed_slopes(h, water, local):
    nw,ne,sw,se=h[:-1,:-1],h[:-1,1:],h[1:,:-1],h[1:,1:]
    wnw,wne,wsw,wse=water[:-1,:-1],water[:-1,1:],water[1:,:-1],water[1:,1:]
    mu=(wnw|wne|wse)&~(wnw&wne&wse)&local
    ml=(wnw|wsw|wse)&~(wnw&wsw&wse)&local
    a=np.r_[np.degrees(np.arctan(np.hypot((ne-nw)/6,(se-ne)/6)))[mu],
            np.degrees(np.arctan(np.hypot((sw-nw)/6,(se-sw)/6)))[ml]]
    return dict(triangles=len(a),over_35=int(np.sum(a>35)),max_deg=float(a.max()))


def main():
    assert sha(SOURCE)==EXPECTED
    assert not OUT.exists() and not EV.exists(), 'Fresh candidate and evidence required'
    OUT.mkdir(); EV.mkdir()
    t=np.load(SOURCE); wpath=R/'tests/terrain_v30/water_v30.npz'; w=np.load(wpath)
    h=t['heights'].astype(float); x,z=grid_xz(); radial=np.hypot(x-CENTER[0],z-CENTER[1])
    planes=cell_planes(t['cls'],t['level'].astype(float))
    domain=box(CENTER[0]-160,CENTER[1]-160,CENTER[0]+160,CENTER[1]+160)
    fixed=np.zeros(h.shape,bool); corridor_count=0
    corridors=R/'evidence/v30-offline-followup-2026-10-02/corridors.geojson'
    for f in json.loads(corridors.read_text())['features']:
        g=shape(f['geometry']).intersection(domain)
        if g.is_empty or g.area<1e-9: continue
        rec=records(g,planes)
        fixed.ravel()[np.unique(rec['ids'])]=True
        corridor_count+=1
    sd=w['sd'].astype(float)
    allowed=(radial<150)&(t['cls']==3)&np.isfinite(sd)&(sd<0)&(sd>-6)
    allowed&=~fixed&~t['platform']&~t['reserve']&~t['narva']
    allowed&=np.hypot(x-2417.1428225906,z-6889.8850822322)>620
    blend=ease((150-radial)/50)*ease((6-np.abs(sd))/3)
    pmin,_=vertex_plane_bounds(planes)
    # 1 mm guard avoids promoting float32 rounding to a depth violation.
    target=np.minimum(t['level'].astype(float)-np.maximum(.101,.12*np.abs(sd)),pmin-.025)
    delta=np.zeros_like(h)
    delta[allowed]=blend[allowed]*np.clip(target[allowed]-h[allowed],0,4)
    candidate=(h+delta).astype('float32'); changed=candidate!=t['heights']
    assert changed.any() and np.all(allowed[changed])
    assert np.array_equal(candidate[fixed],t['heights'][fixed])
    assert float(np.max(candidate.astype(float)-h)) <=4.000001
    rows=range(int((12282-(CENTER[1]+160))//6),int((12282-(CENTER[1]-160))//6)+1)
    cols=range(int((CENTER[0]-160)//6),int((CENTER[0]+160)//6)+1)
    before=shore_segments(h,planes,rows,cols)
    after=shore_segments(candidate.astype(float),planes,rows,cols)
    design=R/'tests/water_v3/water_v3.geojson'
    geoms=[shape(f['geometry']) for f in json.loads(design.read_text())['features']
           if f['properties']['class']=='navigable' and shape(f['geometry']).intersects(domain)]
    boundary=shapely.union_all(geoms).boundary
    region=Point(CENTER).buffer(100)
    bm,am=metrics(before,boundary,region),metrics(after,boundary,region)
    local=(radial[:-1,:-1]<150)
    bs,as_=mixed_slopes(h,t['water'],local),mixed_slopes(candidate.astype(float),t['water'],local)
    gates=dict(mean_waterline_error_reduced=am['mean_error_m']<bm['mean_error_m'],
               p95_waterline_error_not_worse=am['p95_error_m']<=bm['p95_error_m'],
               max_waterline_error_not_worse=am['max_error_m']<=bm['max_error_m']+1e-6,
               no_more_steep_mixed_faces=as_['over_35']<=bs['over_35'],
               max_mixed_slope_not_worse=as_['max_deg']<=bs['max_deg']+1e-6)
    path=OUT/'terrain_v30.npz'
    with path.open('xb') as f: np.savez_compressed(f,**{k:candidate if k=='heights' else t[k] for k in t.files})
    back=np.load(path)
    assert all(np.array_equal(back[k],candidate if k=='heights' else t[k],equal_nan=True) for k in t.files)
    report=dict(status='LOCAL_GEOMETRY_PASS_PENDING_FULL_GATES' if all(gates.values()) else 'REJECTED_LOCAL_GEOMETRY',
      inputs={str(p):sha(p) for p in [SOURCE,wpath,corridors,design,Path(__file__)]},
      file=str(path),sha256=sha(path),changed_vertices=int(changed.sum()),max_raise_m=float((candidate-h).max()),
      local_corridors_preserved=corridor_count,
      all_other_arrays_identical=True,dry_heights_identical=True,fairway_face_vertices_identical=True,
      waterline_before=bm,waterline_after=am,mixed_slopes_before=bs,mixed_slopes_after=as_,gates=gates,
      limits=['150 m pilot only; first 6 m of wet bank; full blend inside 100 m',
              'No deployment; geometry comparison does not certify visual quality or engine water.'],
      changes=[dict(row=int(r),col=int(c),before=float(h[r,c]),after=float(candidate[r,c])) for r,c in np.argwhere(changed)])
    save(EV/'pilot.json',report)
    fig,ax=plt.subplots(figsize=(9,8))
    for g in geoms:
        for part in (g.geoms if hasattr(g,'geoms') else [g]):
            xy=np.asarray(part.exterior.coords);ax.fill(xy[:,0],xy[:,1],color='#cce8f3',alpha=.7)
    for seg,color,label in [(before,'#c36331','V30 desplegada / orilla actual'),(after,'#136b4f','Piloto, sin desplegar')]:
        ax.add_collection(LineCollection(seg,colors=color,linewidths=1.1,label=label))
    rr,cc=np.nonzero(changed);ax.scatter(cc*6,12282-rr*6,c='#9c36ad',s=8,label='Fondo elevado')
    ax.scatter(*CENTER,c='black',marker='^',label='Observador');ax.set_aspect('equal')
    ax.set(xlim=(CENTER[0]-140,CENTER[0]+140),ylim=(CENTER[1]-140,CENTER[1]+140),
           xlabel='X local (m)',ylabel='Z local (m)',title='Narva sur — comparación geométrica del contorno')
    ax.legend(loc='upper left',fontsize=8);ax.grid(alpha=.2)
    fig.text(.5,.01,'Diseño azul; contornos de los triángulos nativos. Pendiente de A/B en DayZ.',ha='center',fontsize=8)
    fig.tight_layout(rect=(0,.025,1,1));fig.savefig(EV/'comparacion-orilla.png',dpi=150);plt.close(fig)
    print(json.dumps({k:report[k] for k in ['status','changed_vertices','max_raise_m','waterline_before','waterline_after','mixed_slopes_before','mixed_slopes_after','gates']}))


if __name__=='__main__': main()
