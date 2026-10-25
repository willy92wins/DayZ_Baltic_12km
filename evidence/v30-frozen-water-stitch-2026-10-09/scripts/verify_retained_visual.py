"""Independent retained-model field check: constant pieces and exact clipped pilot faces."""
from pathlib import Path
from collections import Counter
import json,sys
import numpy as np
import shapely
from shapely.geometry import Polygon

B=Path('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009')
sys.path.insert(0,str(B))
from author_global_visual import sha,read,read_pbo,ODOL,polygons

def sample_cell(field,r,c,xz,kind):
    f=field[r,c];fc=(xz[:,0]-c*6)/6;fr=(12282-r*6-xz[:,1])/6
    return f[0]+fc*(f[1]-f[0])+fr*(f[3]-f[1]) if kind==0 else f[0]+fr*(f[2]-f[0])+fc*(f[3]-f[2])

def main():
    ref=json.loads((B/'package.json').read_text());water=B/'water/packed/baltic_water_v30.pbo'
    assert sha(water)==ref['water_sha256'];_,_,packed=read_pbo(water)
    wp=B/'world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp';assert sha(wp)==ref['world_source_sha256']
    objects={o['id']:o for o in read(wp)['objects']}
    retained=[r for r in map(json.loads,(B/'authoring-progress.jsonl').read_text().splitlines()) if r.get('unchanged')]
    field=np.load(B/'preserved-field.npy');cache={};checks=[]
    for n,row in enumerate(retained):
        obj=objects[row['object_id']];name=row['old_model'];path=B/'water/temp/baltic_water_v30'/name
        if name not in cache:
            assert path.read_bytes()==packed[name]
            od=ODOL.from_file(str(path));lod=min(od.lods,key=lambda l:abs(l.resolution-1))
            vertices=np.array([(v.x,v.y,v.z) for v in lod.vertices]);cache[name]=(vertices,np.array([f.vertex_indices for f in lod.faces]))
        vertices,faces=cache[name];world=vertices+np.array(obj['matrix'][9:12]);xz=world[:,[0,2]]
        r0=max(0,int(np.floor((12282-xz[:,1].max())/6)));r1=min(2047,int(np.ceil((12282-xz[:,1].min())/6)))
        c0=max(0,int(np.floor(xz[:,0].min()/6)));c1=min(2047,int(np.ceil(xz[:,0].max()/6)))
        error=0.;parts=0;known_area=0.;unknown_area=0.
        if row['unchanged']=='constant_field':
            assert np.ptp(world[:,1])<1e-6
            levels=field[r0:r1,c0:c1];finite=levels[np.isfinite(levels)]
            error=float(np.max(np.abs(finite-world[0,1]),initial=0))
            assert len(finite)>0,(row['object_id'],'No frozen field support')
        else:
            for face in faces:
                tri=world[face];xy=tri[:,[0,2]];poly=Polygon(xy)
                if poly.area<1e-12:continue
                coefficients=np.linalg.solve(np.c_[xy-xy[0],np.ones(3)],tri[:,1])
                fr0=max(r0,int(np.floor((12282-xy[:,1].max())/6)));fr1=min(r1,int(np.ceil((12282-xy[:,1].min())/6)))
                fc0=max(c0,int(np.floor(xy[:,0].min()/6)));fc1=min(c1,int(np.ceil(xy[:,0].max()/6)))
                for r in range(fr0,fr1):
                    for c in range(fc0,fc1):
                        nw=(c*6,12282-r*6);ne=(c*6+6,12282-r*6);sw=(c*6,12276-r*6);se=(c*6+6,12276-r*6)
                        for kind,base in enumerate((Polygon([nw,ne,se]),Polygon([nw,sw,se]))):
                            for part in polygons(poly.intersection(base)):
                                if part.area<1e-12:continue
                                if not np.isfinite(field[r,c]).all():unknown_area+=part.area;continue
                                pts=np.asarray(part.exterior.coords);actual=np.c_[pts-xy[0],np.ones(len(pts))]@coefficients
                                target=sample_cell(field,r,c,pts,kind)
                                error=max(error,float(np.max(abs(actual-target))));parts+=1;known_area+=part.area
            assert parts>0,(row['object_id'],'No native face portions checked')
        checks.append(dict(object_id=row['object_id'],model=name,reason=row['unchanged'],field_error_m=error,
                           known_native_parts=parts,known_area_m2=known_area,unknown_border_area_m2=unknown_area,passed=error<2e-5))
        if (n+1)%3000==0:print('Retained field checked',n+1,'of',len(retained),flush=True)
    failed=[r for r in checks if not r['passed']]
    result=dict(status='PASS_RETAINED_NATIVE_FIELD' if not failed else 'FAIL_RETAINED_NATIVE_FIELD',
                instances=len(checks),by_method=dict(Counter(r['reason'] for r in checks)),
                maximum_field_error_m=max(r['field_error_m'] for r in checks),failed=failed,
                water_sha256=sha(water),world_source_sha256=sha(wp),checks=checks,
                limits=['Confirms matching field on frozen native cells; retained unknown outer halos keep their original surface.',
                        'Whole-domain coverage and native graphics are separate gates.'])
    (B/'retained-visual-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))

if __name__=='__main__':main()
