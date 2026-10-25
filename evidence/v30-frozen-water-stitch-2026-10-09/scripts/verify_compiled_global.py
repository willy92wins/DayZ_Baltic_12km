"""Check compiled geometry against source, frozen physical LODs and visible field."""
from pathlib import Path
import argparse,hashlib,io,json,sys
import numpy as np
from scipy.spatial import cKDTree

B=Path('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009')
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B10=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
sys.path[:0]=[str(B),str(W/'tools/terrain'),str(W/'tools/navigation'),str(W/'tools/water'),str(W/'tools/playtest')]
from audit_frozen_visual import visible_error,triangle_areas,clip,area,UNIT
from v30_common import tri_sample
from engine_water_model import ODOL
from water_mesh import py3d
from attach_navmesh import read_pbo

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def points(lod):return np.array([(v.x,v.y,v.z) for v in lod.vertices]).reshape(-1,3)


def match_geometry(a, av, b, bv):
    assert len(a.vertices)==len(b.vertices) and len(a.faces)==len(b.faces)
    assert a.named_properties==b.named_properties and a.textures==b.textures
    assert [m.material_name for m in a.materials]==[m.material_name for m in b.materials]
    if not len(av):return 0.
    unique,indices=np.unique(av,axis=0,return_inverse=True)
    distances,mapped=cKDTree(unique).query(bv)
    err=max(float(distances.max()),float(cKDTree(bv).query(av)[0].max()))
    assert err<2e-5,err
    def faces(lod,vertices,lookup):
        out=[]
        for face in lod.faces:
            ix=np.array(face.vertex_indices);xyz=vertices[ix]
            sign=int(np.sign(np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0])[1]))
            out.append((tuple(sorted(int(x) for x in lookup[ix])),sign))
        return sorted(out)
    assert faces(a,av,indices)==faces(b,bv,mapped),'Physical face topology/winding changed'
    return err


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--repaired',action='store_true');args=parser.parse_args()
    author=json.loads((B/'authoring.json').read_text())
    fieldpath=B/'preserved-field.npy';assert sha(fieldpath)==author['field_sha256'];field=np.load(fieldpath)
    terrain=np.load(B10/'measured-bank-bed-r2/terrain.npz');h=terrain['heights'].astype(float)
    plane=np.load(B10/'frozen-field-reference/plane.npy')
    oldpbo=Path('P:/Mods/@DayZ_Baltic_HaloFixV3/Addons/baltic_water_v30.pbo')
    assert sha(oldpbo)==author['water_sha256']
    _,props,oldpacked=read_pbo(oldpbo)
    patch=B/'compile/out/baltic_water_v30.pbo';_,props2,newpacked=read_pbo(patch)
    assert props==props2 and oldpacked['config.bin']==newpacked['config.bin']
    assert set(newpacked)=={r['new_model'] for r in author['models']}|{'config.bin'}
    removed=set();repairs={};patch2=None
    if args.repaired:
        from repair_visible_halos import reference_cell
        proof=json.loads((B/'removal-proof.json').read_text());assert proof['status']=='PASS_ZERO_INTENDED_COVERAGE_REMOVAL'
        removed=set(proof['removed_instance_ids'])
        repairs={r['object_id']:r for r in json.loads((B/'halo-repair.json').read_text())['repairs']}
        patch2=B/'compile-r2/out/baltic_water_v30.pbo';_,props3,packed3=read_pbo(patch2)
        assert props3==props and packed3['config.bin']==oldpacked['config.bin']
        assert set(packed3)=={r['model'] for r in repairs.values()}|{'config.bin'}
        newpacked.update(packed3)
    suffix='-r2' if args.repaired else ''
    out=B/('compiled-checks'+suffix+'.jsonl');assert not out.exists()
    oldcache={};rows=[]
    for n,row in enumerate(author['models']):
        if row['object_id'] in removed:continue
        oldname,newname=row['old_model'],row['new_model']
        if oldname not in oldcache:
            path=B10/'halo-fix-v3/water/temp/baltic_water_v30'/oldname
            assert path.read_bytes()==oldpacked[oldname]
            oldcache[oldname]=ODOL.from_file(str(path))
        old=oldcache[oldname]
        variant='compile-r2' if row['object_id'] in repairs else 'compile'
        path=B/variant/'temp/baltic_water_v30'/newname
        assert path.read_bytes()==newpacked[newname]
        new=ODOL.from_file(str(path));bc=new.model_info.bounding_center;newc=np.array([bc.x,bc.y,bc.z])
        oldc=np.array(row['old_center']);m=np.array(row['old_matrix']);newpos=np.array(m[9:12]+newc-oldc,dtype=np.float32).astype(float)
        horizontal=float(np.max(np.abs(newc[[0,2]]-oldc[[0,2]])))
        assert horizontal<2e-5,(newname,'Horizontal model centre moved',horizontal)
        assert np.array_equal(newpos[[0,2]],m[9:12][[0,2]]),('Horizontal WRP position changed',newname)
        for key in ('property_class','property_damage','property_frequent'):
            assert getattr(old.model_info,key)==getattr(new.model_info,key),(newname,key)
        assert len(old.lods)==len(new.lods)
        physical_error=0.
        for oldlod in old.lods:
            if abs(oldlod.resolution-1)<1e-6:continue
            newlod=min(new.lods,key=lambda l:abs(l.resolution-oldlod.resolution))
            assert newlod.resolution==oldlod.resolution
            av=points(oldlod)+m[9:12];bv=points(newlod)+newpos
            physical_error=max(physical_error,match_geometry(oldlod,av,newlod,bv))
        visible=min(new.lods,key=lambda l:abs(l.resolution-1));world=points(visible)+newpos
        mlodpath=B/variant/'source/baltic_water_v30'/newname
        assert sha(mlodpath)==(repairs[row['object_id']]['after_sha256'] if row['object_id'] in repairs else row['new_sha256'])
        mlod=py3d.P3D(io.BytesIO(mlodpath.read_bytes()))
        expected=np.array([p.coords for p in mlod.lods[0].points])+np.array(row['origin'])
        source_error=max(float(cKDTree(expected).query(world)[0].max()),float(cKDTree(world).query(expected)[0].max()))
        assert source_error<2e-5,(newname,'Compiled visible mesh differs',source_error)
        tri=np.array([world[face.vertex_indices] for face in visible.faces])
        assert tri.shape[1:]==(3,3)
        x,z=tri[:,:,0],tri[:,:,2];cx,cz=x.mean(1),z.mean(1)
        inside=(cx>=0)&(cx<12282)&(cz>0)&(cz<=12282)
        tri=tri[inside];x,z=tri[:,:,0],tri[:,:,2];cx,cz=x.mean(1),z.mean(1)
        r=np.clip(np.floor((12282-cz)/6).astype(int),0,2046);c=np.clip(np.floor(cx/6).astype(int),0,2046)
        levels=field[r,c];known=np.isfinite(levels).all(1)
        supported_halo=np.zeros(len(r),dtype=bool);ar,ac=r.copy(),c.copy()
        if row['object_id'] in repairs:
            for i in np.flatnonzero(~known):
                rr,cc,_=reference_cell(cx[i],cz[i],plane,row['origin'][1])
                ar[i],ac[i]=rr,cc;levels[i]=field[rr,cc];supported_halo[i]=True
        resolved=known|supported_halo
        levels=np.where(resolved[:,None],levels,row['origin'][1])
        fc=(x-ac[:,None]*6)/6;fr=(12282-ar[:,None]*6-z)/6
        upper=levels[:,0,None]+fc*(levels[:,1]-levels[:,0])[:,None]+fr*(levels[:,3]-levels[:,1])[:,None]
        lower=levels[:,0,None]+fr*(levels[:,2]-levels[:,0])[:,None]+fc*(levels[:,3]-levels[:,2])[:,None]
        target=np.where(((cx-ac*6)/6 >= (12282-ar*6-cz)/6)[:,None],upper,lower)
        ground=tri_sample(h,x,z);depth=tri[:,:,1]-ground
        surface_area=np.abs((x[:,1]-x[:,0])*(z[:,2]-z[:,0])-(z[:,1]-z[:,0])*(x[:,2]-x[:,0]))/2
        visible_area=triangle_areas(depth)/18*surface_area
        field_errors=visible_error(depth,target-tri[:,:,1],visible_area)
        max_field_error=float(field_errors.max(initial=0))
        p=plane[ar,ac];p=np.where(np.isfinite(p),p,row['origin'][1])
        delta=tri[:,:,1]-p[:,None]
        offset=visible_error(depth,delta,visible_area)
        unknown_area=float(visible_area[~resolved].sum())
        dry_added=0.;visible_shared_vertex_error=0.
        if args.repaired:
            upper_native=((cx-c*6)/6 >= (12282-r*6-cz)/6)
            classes=np.c_[terrain['cls'][r,c],np.where(upper_native,terrain['cls'][r,c+1],terrain['cls'][r+1,c]),terrain['cls'][r+1,c+1]]
            for i in np.flatnonzero(np.all(classes==0,axis=1)&(visible_area>0)):
                after=clip(UNIT,depth[i]);common=clip(after,row['origin'][1]-ground[i])
                dry_added+=max(0.,area(after)-area(common))/18*surface_area[i]
            # Independent internal continuity check: compiled vertices sharing XZ
            # may differ in height only when both remain buried.
            xy=np.round(world[:,[0,2]],5);unique,inv=np.unique(xy,axis=0,return_inverse=True)
            lo=np.full(len(unique),np.inf);hi=np.full(len(unique),-np.inf)
            np.minimum.at(lo,inv,world[:,1]);np.maximum.at(hi,inv,world[:,1])
            inmap=(unique[:,0]>=0)&(unique[:,0]<=12282)&(unique[:,1]>=0)&(unique[:,1]<=12282)
            exposed=np.zeros(len(unique),bool);exposed[inmap]=hi[inmap]>tri_sample(h,unique[inmap,0],unique[inmap,1])+2e-5
            visible_shared_vertex_error=float(np.max((hi-lo)[exposed],initial=0))
        gates=dict(physical=physical_error<2e-5,visible_source=source_error<2e-5,
                   visible_field=max_field_error<2e-5,visible_offset=float(offset.max(initial=0))<=.35003,
                   no_unknown_visible_area=unknown_area<=1e-8)
        if args.repaired:gates.update(no_new_dry_water=dry_added<=1e-8,internal_visible_continuity=visible_shared_vertex_error<2e-5)
        receipt=dict(object_id=row['object_id'],model=newname,compiled_sha256=sha(path),old_model=oldname,
                     new_center=newc.tolist(),new_position=newpos.tolist(),physical_error_m=physical_error,
                     visible_source_error_m=source_error,visible_field_error_m=max_field_error,
                     visible_offset_m=float(offset.max(initial=0)),unknown_visible_area_m2=unknown_area,
                     extrapolated_visible_halo_area_m2=float(visible_area[supported_halo].sum()),new_dry_water_m2=dry_added,
                     visible_shared_vertex_error_m=visible_shared_vertex_error,gates=gates)
        with out.open('a',encoding='utf-8') as log:log.write(json.dumps(receipt)+'\n')
        rows.append(receipt)
        if not all(gates.values()):
            print(json.dumps(receipt,indent=2),flush=True)
        if (n+1)%250==0:print('Verified compiled',n+1,'of',len(author['models']),flush=True)
    failures=[r for r in rows if not all(r['gates'].values())]
    report=dict(status='PASS_COMPILED_VISIBLE_GEOMETRY' if not failures else 'FAIL_COMPILED_VISIBLE_GEOMETRY',
                models=len(rows),failed_models=failures,patch_sha256=sha(patch),old_water_sha256=sha(oldpbo),
                max_physical_error_m=max(r['physical_error_m'] for r in rows),
                max_visible_source_error_m=max(r['visible_source_error_m'] for r in rows),
                max_visible_field_error_m=max(r['visible_field_error_m'] for r in rows),
                max_visible_offset_m=max(r['visible_offset_m'] for r in rows),
                unknown_visible_area_m2=sum(r['unknown_visible_area_m2'] for r in rows),
                repaired_patch_sha256=sha(patch2) if patch2 else None,
                removed_instance_ids=sorted(removed),new_dry_water_m2=sum(r['new_dry_water_m2'] for r in rows),
                max_visible_shared_vertex_error_m=max(r['visible_shared_vertex_error_m'] for r in rows),
                extrapolated_visible_halo_area_m2=sum(r['extrapolated_visible_halo_area_m2'] for r in rows),
                limits=['Compiled model checks; union coverage, WRP and runtime checks remain.',
                        'A lack of native render does not certify removal of the reported dry-land shine.'])
    (B/('compiled-verification'+suffix+'.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='failed_models'},indent=2))


if __name__=='__main__':main()
