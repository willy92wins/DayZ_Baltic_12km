"""Consumer gates for actual restored pond faces and the local shore profile."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
import shapely
from shapely.geometry import Polygon,box,shape
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008')
E=W/'evidence/v30-curved-channel-pilot-2026-10-08'
sys.path[:0]=[str(W/'tools/terrain'),str(W/'tools/water')]
from v30_common import cell_planes,tri_sample,vertex_plane_bounds
from verify_channel_reaches_v30 import retained_pond_faces,check_face_coverage
from verify_roads_v30 import evaluate
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def corridor_faces(geom):
    # Independent box/triangle enumeration from the previous contract consumer.
    x0,z0,x1,z1=geom.bounds
    c0=max(0,int(np.floor(x0/6)));c1=min(2047,int(np.ceil(x1/6)))
    r0=max(0,int(np.floor((12282-z1)/6)));r1=min(2047,int(np.ceil((12282-z0)/6)))
    for r in range(r0,r1,64):
      for c in range(c0,c1,64):
        re,ce=min(r+64,r1),min(c+64,c1)
        if not geom.intersects(box(c*6,12282-re*6,ce*6,12282-r*6)):continue
        rr,cc=np.mgrid[r:re,c:ce];rr,cc=rr.ravel(),cc.ravel()
        for half,(dr,dc) in enumerate(((0,1),(1,0))):
          vertices=np.stack([np.column_stack((cc*6,12282-rr*6)),np.column_stack(((cc+dc)*6,12282-(rr+dr)*6)),np.column_stack(((cc+1)*6,12282-(rr+1)*6))],axis=1)
          clipped=shapely.intersection(shapely.polygons(vertices),geom)
          keep=shapely.area(clipped)>1e-9
          if np.any(keep):yield rr[keep],cc[keep],half,clipped[keep]

def main():
    source=Path('E:/DayZ-Baltic-Build/v30-navigation-contract-20261008/terrain_floor.npz')
    candidate=B/'flat-profile/terrain_flat.npz'
    a,b=np.load(source),np.load(candidate);old,new=a['heights'].astype(float),b['heights'].astype(float)
    planes=cell_planes(b['cls'],b['level']);pmin,pmax=vertex_plane_bounds(planes)
    masks=np.load(B/'flat-profile/masks.npz');changed=old!=new
    axes=json.loads(Path('E:/DayZ-Baltic-Build/v30-continuation-20261008/junction-fix-r2/axes.json').read_text())
    removed=sorted({tuple(rc) for reach in axes.values() for rc in reach['removed_cells']})
    domain=shapely.union_all([box(c*6,12282-(r+1)*6,(c+1)*6,12282-r*6) for r,c in removed])
    author=json.loads((E/'flat-water-authoring.json').read_text())
    tiles=shapely.union_all([box(tx*48,tz*48,(tx+1)*48,(tz+1)*48) for tx,tz in author['affected_tiles']])
    manifest=json.loads((B/'flat-water/water/pieces.json').read_text())
    print('Reading actual pond faces',flush=True)
    faces=retained_pond_faces(B/'flat-water',manifest,tiles.buffer(.05))
    polys=[f[0].intersection(tiles) for f in faces];surface=shapely.union_all(polys)
    redundant=max(0,sum(p.area for p in polys)-surface.area)/surface.area
    wet=[];full=[]
    for r,c in removed:
        if np.isfinite(planes[r,c]):full.append(box(c*6,12282-(r+1)*6,(c+1)*6,12282-r*6))
        for dr,dc in ((0,1),(1,0)):
            rc=[(r,c),(r+dr,c+dc),(r+1,c+1)]
            if all(b['cls'][u,v]>0 for u,v in rc):wet.append(Polygon([(v*6,12282-u*6) for u,v in rc]))
    coverage=check_face_coverage(wet,surface)
    complete_gap=shapely.union_all(full).difference(surface).area
    # Every class-zero corner touching the restored cells, plus every changed corner.
    inspect=masks['core']|changed
    bad_dry=inspect&(b['cls']==0)&np.isfinite(pmax)&(new<pmax-1e-6)
    bad_wet=inspect&np.isin(b['cls'],(2,3,5,6,7))&np.isfinite(pmin)&(new>pmin-.02+1e-6)
    coords=lambda m:[dict(row=int(r),col=int(c),x=int(c*6),z=int(12282-r*6),old=float(old[r,c]),new=float(new[r,c]),pmin=float(pmin[r,c]),pmax=float(pmax[r,c])) for r,c in zip(*np.nonzero(m))]
    reports=[]
    corpath=Path('E:/DayZ-Baltic-Build/v30-v11/06-evidence/corridors.geojson')
    assert sha(corpath)=='28866a8cf6ff57f2f825228046164ef939bc22bca9948eb96fe2463da46af343'
    print('Checking continuous 24 m corridors',flush=True)
    for feature in json.loads(corpath.read_text())['features']:
        geom=shape(feature['geometry']);count=0;area=0.;mind=1e30;bad=0
        for rr,cc,half,parts in corridor_faces(geom):
            xyz,owners=shapely.get_coordinates(parts,return_index=True)
            # The frozen contract uses low-water sea level 0.5 m for sea sections.
            lv=np.maximum(np.nan_to_num(planes[rr,cc],nan=-np.inf),.5)[owners]
            dep=lv-tri_sample(new,xyz[:,0],xyz[:,1]);mind=min(mind,float(dep.min()))
            bad+=int(np.unique(owners[dep<.95-1e-9]).size);count+=len(parts);area+=float(shapely.area(parts).sum())
        reports.append(dict(river=feature['properties']['river'],faces=count,min_depth_m=mind,bad_faces=bad,area_error_m2=abs(area-geom.area)))
    steep=[]
    for dr,dc in ((0,1),(1,0)):
        def slope(h):
            mid=h[dr:dr+2047,dc:dc+2047]
            return np.degrees(np.arctan(np.hypot(mid-h[:-1,:-1],h[1:,1:]-mid)/6))
        before,after=slope(old),slope(new);land=b['cls']==0
        touch=land[:-1,:-1]|land[dr:dr+2047,dc:dc+2047]|land[1:,1:]
        steep.extend((int(r),int(c),float(before[r,c]),float(after[r,c])) for r,c in zip(*np.nonzero(touch&(after>35.01)&(after>before+1e-6))))
    roads=evaluate(new,b['water'].astype(bool))
    floor=np.isin(b['cls'],(2,3,5,6,7))&(old>=1.)
    # Consumer negative: real coverage hole and duplicate footprint, not a mutated status.
    target=wet[len(wet)//2];missing=check_face_coverage(wet,surface.difference(target.buffer(.01)))
    duplicate_ratio=(sum(p.area for p in polys)+surface.area-surface.area)/surface.area
    controls=dict(hole_rejected=missing['uncovered_faces']>0,duplicate_rejected=duplicate_ratio>.01,depth_094_rejected=.94<.95)
    checks=dict(metadata_exact=all(np.array_equal(a[k],b[k],equal_nan=True) for k in a.files if k!='heights'),
                outside_exact=not bool(np.any(changed&~masks['allowed'])),frozen_exact=not bool(np.any(changed&masks['frozen'])),
                existing_floor_preserved=bool(np.all(new[floor]>=1)),no_dry_corner_under_water=not bool(bad_dry.any()),
                wet_corners_covered=not bool(bad_wet.any()),no_coverage_holes=coverage['uncovered_faces']==0 and complete_gap<1e-6,
                overlap_under_one_percent=redundant<=.01,corridors_095=len(reports)==19 and all(p['bad_faces']==0 and p['area_error_m2']<1e-5 for p in reports),
                no_steepening=not steep,roads_pass=roads['status']=='PASS',negative_controls=all(controls.values()))
    out=dict(status='PASS_OFFLINE_FLAT_FALLBACK' if all(checks.values()) else 'FAIL',checks=checks,
             inputs={str(p):sha(p) for p in (source,candidate,corpath,B/'flat-water/water/pieces.json',Path(__file__))},
             coverage=coverage,complete_cell_gap_m2=complete_gap,redundant_area_ratio=redundant,actual_roadway_faces=len(faces),
             dry_failures=coords(bad_dry),wet_failures=coords(bad_wet),corridors=reports,roads=roads,steep_faces=steep,controls=controls,
             limits=['Source MLOD geometry; compiled ODOL parity and engine/boat/visual checks remain.',
                     'Nominal levels; no maximum pond wave envelope claimed.',
                     'Frozen global navigation excludes Narva; local R1 consumer must be rerun.'])
    (E/'flat-verification.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ('status','checks','coverage','complete_cell_gap_m2','redundant_area_ratio','dry_failures','wet_failures')},indent=2),flush=True)
    assert all(checks.values())

if __name__=='__main__':main()
