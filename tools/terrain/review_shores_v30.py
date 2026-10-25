"""Post-build shore review: immutable fields, tidal exposure, native faces and
waterline diagnostics against the pre-existing signed outline field.
The outline metric is diagnostic (interpolated field), not a render verdict.
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np
import rasterio
from shapely.geometry import shape

from audit_fairway_triangles_v30 import records, describe, save, sha
from audit_v30_shore_triangles import faces
from v30_common import cell_planes, tri_sample, vertex_plane_bounds

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path('E:/DayZ-Baltic-Build/v30-delta-candidate/terrain_v30.npz')


def waterline(h, plane, scope):
    rr, cc = np.nonzero(scope)
    xy = np.stack([np.stack([cc*6,12282-rr*6],1),
                   np.stack([(cc+1)*6,12282-rr*6],1),
                   np.stack([cc*6,12282-(rr+1)*6],1),
                   np.stack([(cc+1)*6,12282-(rr+1)*6],1)],1)
    hh = np.stack([h[rr,cc],h[rr,cc+1],h[rr+1,cc],h[rr+1,cc+1]],1)
    level = np.nan_to_num(plane[rr,cc],nan=.75)
    result = []
    for ix in ((0,1,3),(0,2,3)):
        v = hh[:,ix]-level[:,None]
        p = xy[:,ix]
        pts = np.full((len(rr),3,2),np.nan)
        for k,(a,b) in enumerate(((0,1),(1,2),(2,0))):
            cross = v[:,a]*v[:,b] < 0
            fraction = -v[cross,a]/(v[cross,b]-v[cross,a])
            pts[cross,k] = p[cross,a]+fraction[:,None]*(p[cross,b]-p[cross,a])
        valid = np.isfinite(pts[:,:,0]).sum(1)==2
        for row in pts[valid]:
            result.append(row[np.isfinite(row[:,0])])
    return np.asarray(result)


def field_error(segments, field):
    # Equal length weighting with 1 m samples on the actual native waterline.
    points=[]
    for a,b in segments:
        n=max(2,int(np.ceil(np.linalg.norm(b-a)))+1)
        points.extend(a+(b-a)*t for t in np.linspace(0,1,n))
    p=np.asarray(points)
    err=np.abs(tri_sample(field,p[:,0],p[:,1]))
    err=err[np.isfinite(err)]
    return dict(samples=int(len(err)), mean_m=float(err.mean()),
                p95_m=float(np.percentile(err,95)),max_m=float(err.max()))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--candidate',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    if a.out.exists(): raise ValueError('Fresh review destination required')
    a.out.mkdir(parents=True)
    source=np.load(SOURCE); candidate=np.load(a.candidate)
    old=source['heights'].astype(float); new=candidate['heights'].astype(float)
    cls=source['cls']; level=source['level'].astype(float)
    changed=old!=new
    assert old.shape==new.shape==(2048,2048) and changed.any()
    planes=cell_planes(cls,level)
    checks={f'field_{k}_identical':bool(np.array_equal(source[k],candidate[k],equal_nan=True))
            for k in source.files if k!='heights'}
    checks['dry_never_raised']=bool(np.all(new[cls==0]<=old[cls==0]))
    checks['wet_never_lowered']=bool(np.all(new[cls>0]>=old[cls>0]))
    pmin,pmax=vertex_plane_bounds(planes)
    tidal=(cls>0)&((level<=.8)|~np.isfinite(pmin))
    checks['nonpond_water_in_tidal_domain']=bool(np.all(tidal[(cls>0)&~np.isfinite(pmin)]))
    wet_changed=changed&(cls>0)&np.isfinite(pmin)
    dry_changed=changed&(cls==0)&np.isfinite(pmax)
    checks['changed_wet_piece_depth_5cm']=bool(np.all(new[wet_changed] <= pmin[wet_changed]-.05+1e-5))
    checks['changed_dry_piece_freeboard_3cm']=bool(np.all(new[dry_changed] >= pmax[dry_changed]+.03-1e-5))
    exposure=tidal&(old<.5)&(new>=.5)
    checks['no_new_low_tide_exposed_vertices']=not bool(exposure.any())
    checks['changed_coastal_bed_below_low_tide']=bool(np.all(new[tidal&changed] <= .450001))
    for k in ['platform','reserve','narva']:
        checks[f'protected_{k}_heights']=bool(np.array_equal(old[source[k]],new[source[k]]))
    nature=np.load(ROOT/'tests/regional_outline_v1/reference.npz')['reserve'].astype(bool)
    checks['nature_envelope_heights']=bool(np.array_equal(old[nature],new[nature]))
    with rasterio.open(a.candidate.parent/'baltic_terrain_v30.asc') as ds:
        checks['asc_heights_exact']=bool(np.array_equal(ds.read(1),candidate['heights']))
        checks['asc_grid_origin_exact']=ds.shape==(2048,2048) and ds.transform.a==6 and ds.transform.e==-6 and ds.bounds.left==200000 and ds.bounds.bottom==0
    corridors=[]
    paths=[ROOT/'evidence/v30-offline-followup-2026-10-02/corridors.geojson',
           ROOT/'evidence/v30-delta-fairways-2026-10-02/axes-corridors.geojson']
    for path in paths:
        for f in json.loads(path.read_text())['features']:
            if f['properties'].get('kind','corridor24m')!='corridor24m': continue
            rec=records(shape(f['geometry']),planes)
            ids=np.unique(rec['ids']); exact=bool(np.array_equal(old.ravel()[ids],new.ravel()[ids]))
            corridors.append(dict(name=f['properties'].get('name',f['properties'].get('river')),
                                  heights_identical=exact,**describe(new,rec)))
    checks['all_main_and_delta_corridors_unchanged']=len(corridors)==23 and all(c['heights_identical'] and c['failing_faces']==0 for c in corridors)
    before=faces(old,cls); after=faces(new,cls)
    angles0=np.concatenate([f['slopes'] for f in before]); angles1=np.concatenate([f['slopes'] for f in after])
    worsened=(angles1>35.+1e-4)&(angles1>angles0+1e-4)
    checks['no_new_or_worsened_steep_shore_faces']=not bool(worsened.any())
    shore=dict(mixed_faces=len(angles0),before_over35=int((angles0>35).sum()),
               after_over35=int((angles1>35).sum()),before_max_deg=float(angles0.max()),after_max_deg=float(angles1.max()),
               new_or_worsened_over35=int(worsened.sum()))
    scope=changed[:-1,:-1]|changed[:-1,1:]|changed[1:,:-1]|changed[1:,1:]
    w=np.load(ROOT/'tests/terrain_v30/water_v30.npz')
    sd=w['sd'].astype(float); sea_sd=w['sd_sea'].astype(float)
    use=np.isfinite(sea_sd)&(~np.isfinite(sd)|(np.abs(sea_sd)<np.abs(sd)))
    field=np.where(use,sea_sd,sd)
    wb,wa=waterline(old,planes,scope),waterline(new,planes,scope)
    bm,am=field_error(wb,field),field_error(wa,field)
    report=dict(status='PASS_OFFLINE_INVARIANTS' if all(checks.values()) else 'FAIL_OFFLINE_INVARIANTS',
                checks=checks,source_sha256=sha(SOURCE),candidate_sha256=sha(a.candidate),
                changed=int(changed.sum()),newly_exposed_coastal_vertices=int(exposure.sum()),
                corridors=corridors,shore_faces=shore,outline_field_before=bm,outline_field_after=am,
                limits=['Outline signed-field diagnostic is an interpolation of the approved geometry at grid vertices.',
                        'Native waterline is computed per triangle; rendered water and visual quality remain untested.',
                        'Physical shore, road gates and engine/navmesh consumer are recorded separately.'])
    save(a.out/'review.json',report)
    # Regional overview and four equal-scale patches are made only after the
    # complete candidate, not used as substitutes for native engine captures.
    fig,axes=plt.subplots(2,3,figsize=(18,11))
    ax=axes[0,0]
    ax.imshow(cls,extent=(-3,12285,-3,12285),origin='upper',cmap='Blues',alpha=.25)
    r,c=np.nonzero(changed)
    im=ax.scatter(c*6,12282-r*6,c=(new-old)[r,c],s=.5,cmap='coolwarm',vmin=-3,vmax=3)
    fig.colorbar(im,ax=ax,label='Cambio de altura (m)')
    ax.set_title('Región: corrección acotada de bancos')
    axes[0,1].hist([angles0,angles1],bins=np.arange(0,70,2),label=['Antes','Candidato'],histtype='step',log=True)
    axes[0,1].set(xlabel='Pendiente de cara mixta (grados)',ylabel='Número de caras');axes[0,1].legend()
    for ax,(cx,cz,title) in zip([axes[0,2],*axes[1]],[(1062,4836,'Narva sur'),(7470,3550,'Luga'),(9400,10330,'Delta de San Petersburgo'),(9100,6150,'Lagunas / reserva')]):
        for seg,color,label in [(wb,'#bd713c','Antes'),(wa,'#096870','Candidato')]:
            centre=seg.mean(1); take=(abs(centre[:,0]-cx)<200)&(abs(centre[:,1]-cz)<200)
            ax.add_collection(LineCollection(seg[take],colors=color,linewidths=.9,label=label))
        take=(abs(c*6-cx)<200)&(abs(12282-r*6-cz)<200)
        ax.scatter(c[take]*6,12282-r[take]*6,c=(new-old)[r[take],c[take]],s=5,cmap='coolwarm',vmin=-3,vmax=3,alpha=.6)
        ax.set(xlim=(cx-200,cx+200),ylim=(cz-200,cz+200),title=title);ax.legend(fontsize=7)
    for ax in [axes[0,0],axes[0,2],*axes[1]]:
        ax.set_aspect('equal');ax.set(xlabel='X (m)',ylabel='Z (m)');ax.grid(alpha=.2)
    fig.suptitle('V30: orillas completas — revisión geométrica, pendiente del juego')
    fig.tight_layout();fig.savefig(a.out/'shore-review.png',dpi=140);plt.close(fig)
    print(json.dumps({k:report[k] for k in ['status','checks','changed','newly_exposed_coastal_vertices','shore_faces','outline_field_before','outline_field_after']},indent=2))
    return 0 if all(checks.values()) else 2


if __name__=='__main__': raise SystemExit(main())
