"""Consume the staged forest on the changed native terrain and custom pilot.

Reuses the independently authored G4 exact planar-disc consumer and its limits.
This is a support/water-clearance gate, not the complete forest or aesthetic gate.
"""
import argparse,hashlib,json,struct,sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,Point
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'terrain'))
from wrp0wzd import read

def transform_failures(A,scale_limits):
    """G5's existing Livonia bounds, applied again to staged float32 matrices."""
    A=np.asarray(A,float);bounds=np.asarray(scale_limits,float)
    if A.ndim!=3 or A.shape[1:]!=(3,3) or bounds.shape!=(len(A),2) or not np.isfinite(A).all() or not np.isfinite(bounds).all():
        raise ValueError('finite Nx3x3 transforms and Nx2 scale limits required')
    norms=np.linalg.norm(A,axis=1);s=norms.mean(axis=1)
    gram=np.einsum('nji,njk->nik',A,A)
    dots=np.max(abs(gram[:,[0,0,1],[1,2,2]]),axis=1)
    return dict(orthonormal_scale=(np.max(abs(norms-s[:,None]),axis=1)>1e-6*s)|(dots>1e-6*s*s),
                determinant=np.linalg.det(A)<=0,
                scale_range=(s<bounds[:,0]-1e-6)|(s>bounds[:,1]+1e-6))

def outside_measured_domain(origins,radius):
    origins=np.asarray(origins,float);radius=np.asarray(radius,float)
    if origins.ndim!=2 or origins.shape[1]!=3 or radius.shape!=(len(origins),) or not np.isfinite(origins).all() or not np.isfinite(radius).all() or (radius<0).any():
        raise ValueError('finite origins and nonnegative radii required')
    return (origins[:,0]-radius<0)|(origins[:,0]+radius>12282)|(origins[:,2]-radius<0)|(origins[:,2]+radius>12282)


def forest_arrays(path,oldids,model_names,expected,H):
    """Stream the verified 0WZD layout, avoiding millions of Python object dicts."""
    names_index={n:i for i,n in enumerate(model_names)}
    ids=np.empty(expected,np.uint32);indices=np.empty(expected,np.uint16);matrices=np.empty((expected,12),np.float32);count=0;seen=[]
    with path.open('rb') as f:
        header=f.read(24);magic,tx,tz,nx,nz,cell=struct.unpack('<4s4If',header);assert magic==b'0WZD'
        terrain=np.frombuffer(f.read(nx*nz*4),'<f4').reshape(nz,nx);assert np.array_equal(terrain,H[::-1]);del terrain
        f.seek(tx*tz*2,1);materials=struct.unpack('<I',f.read(4))[0]
        for _ in range(materials):
            while True:
                length=struct.unpack('<I',f.read(4))[0]
                if not length:break
                f.seek(length,1)
        while True:
            row=f.read(56);assert len(row)==56
            oid,length=struct.unpack_from('<2I',row,48)
            if not length:break
            raw=f.read(length);assert len(raw)==length;name=raw.decode('ascii').rstrip('\0').lower();seen.append(oid)
            if oid in oldids or name.startswith('baltic_stream_pilot\\'):continue
            assert count<expected and name in names_index,('unknown/extra forest record',name)
            ids[count]=oid;indices[count]=names_index[name];matrices[count]=struct.unpack_from('<12f',row);count+=1
        assert not f.read(1),'trailing WRP bytes'
    assert count==expected and len(set(seen))==len(seen)
    return np.array(model_names,object)[indices],ids,matrices


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('build');ap.add_argument('stage');ap.add_argument('pilot');ap.add_argument('merged');ap.add_argument('--output',type=Path);a=ap.parse_args()
    if a.output and a.output.exists():raise FileExistsError(a.output)
    B=Path(a.build);S=Path(a.stage);P=Path(a.pilot);T=Path(a.merged)/'terrain-buried.npz'
    geompath=B/'forest-final-tools/r2/gates';sys.path.insert(0,str(geompath));import geom
    sr=json.loads((S/'stage-report.json').read_text());assert sr['forest']
    reference=Path(sr['forest_reference']['path']);assert hashlib.sha256(reference.read_bytes()).hexdigest()==sr['forest_reference']['sha256']
    models=json.loads(reference.read_text())['models']
    nf=read(B/'stage-nonforest-c/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp');oldids={o['id'] for o in nf['objects']};del nf
    path=S/'root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
    H=np.load(T)['heights'];assert np.isfinite(H).all(),'non-finite terrain'
    count=sr['remaining_objects']-(len(oldids)-sr['removed_old_kit_records'])
    names,ids,matrices=forest_arrays(path,oldids,sorted(models),count,H)
    A=matrices[:,:9].reshape(-1,3,3).transpose(0,2,1).astype(np.float64)
    assert np.isfinite(matrices).all(),'non-finite forest transform'
    assert all(n in models for n in set(names))
    transforms=transform_failures(A,[[models[n]['scale_q'][0],models[n]['scale_q'][-1]] for n in names])
    bc=np.array([models[n]['bc'] for n in names]);origin=matrices[:,9:]-np.einsum('nij,nj->ni',A,bc)
    scale=np.linalg.norm(A[:,:,0],axis=1);families=np.array([models[n]['family'] for n in names]);ground=geom.h_at(H,origin[:,0],origin[:,2])
    assert np.isfinite(origin).all() and np.isfinite(ground).all() and (scale>0).all(),'invalid forest root or scale'
    dy=origin[:,1]-ground;bad_origin=np.flatnonzero(abs(dy)>.005)
    selected=np.flatnonzero(np.isin(families,['conifer','broadleaf','bush']))
    trunk=np.array([models[n]['trunk_radius'] for n in names])*scale
    embed=np.array([-min(models[n]['visual_bottom_local'],0.) for n in names])*scale
    gap=np.zeros(count);native_water=np.zeros(count,bool);sea_band=np.zeros(count,bool)
    fp=np.load(Path(a.merged)/'bury-work/fp0/footprint.npz');plane=fp['plane'];env=fp['env_plane']
    base=np.array([models[n]['base_radius_plan'] for n in names])*scale
    radius=np.where(families=='reed',.25,base+.25)
    support_radius=np.where(np.isin(families,['conifer','broadleaf','bush']),trunk,0.)
    required_radius=np.maximum(radius,support_radius)
    boundary=outside_measured_domain(origin,required_radius)
    for start in range(0,count,100000):
        ix=np.arange(start,min(start+100000,count));xx=origin[ix,0];zz=origin[ix,2];rr=radius[ix]
        pond=geom.disc_min(H,xx,zz,rr,lambda r,c:plane[r,c])
        sea=geom.disc_min(H,xx,zz,rr,lambda r,c:np.full(r.shape,.75))
        band=geom.disc_min(H,xx,zz,rr,lambda r,c:np.where(np.isfinite(env[r,c]),np.nan,1.))
        native_water[ix]=(pond<0)|(sea<0);sea_band[ix]=band<0
        trees=ix[np.isin(families[ix],['conifer','broadleaf','bush'])]
        if len(trees):gap[trees]=ground[trees]-geom.disc_min(H,origin[trees,0],origin[trees,2],trunk[trees],lambda r,c:np.zeros(r.shape))-embed[trees]
        print('forest support/water',min(start+100000,count),'/',count,flush=True)
    bad_support=np.flatnonzero(gap>.01)
    # geom.disc_min explicitly returns +inf when no native triangle meets a
    # disc. The 12282..12288 outer strip is not represented by this consumer;
    # retain it as unknown instead of passing -inf gaps or assuming engine Z.
    invalid_support=np.flatnonzero(~np.isfinite(gap)&~boundary)
    tilt=np.degrees(np.arccos(np.clip(A[:,1,1]/scale,-1,1)));max_tilt=np.array([models[n]['tilt_q'][-1]+.01 for n in names]);bad_tilt=np.flatnonzero(tilt>max_tilt)
    water_hits=[];bed_hits=[]
    sys.path.insert(0,'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/py3d');import py3d
    authored=json.loads((P/'author-report.json').read_text())
    for site in authored['sites']:
        beds=[];waters=[]
        for inst in authored['instances']:
            if inst['site']!=site['site']:continue
            source=P/'source'/inst['model'].replace('\\','/')
            assert hashlib.sha256(source.read_bytes()).hexdigest()==inst['sha256']
            # P3D.read header + LOD(f), verified in py3d:3007-3013/1978-2006.
            # Read visual LOD only; collision component tags are irrelevant here.
            with source.open('rb') as f:
                magic,version,nlod=struct.unpack('<4s2I',f.read(12));assert magic==b'MLOD' and nlod==4
                lod=py3d.LOD(f)
            vertices=np.array([v.coords for v in lod.points])+inst['origin']
            for face in lod.faces:
                poly=Polygon(vertices[[v.point_index for v in face.vertices]][:,[0,2]])
                (waters if 'water_streambed' in face.material else beds).append(poly)
        bp=unary_union(beds);wp=unary_union(waters);assert bp.is_valid and wp.is_valid
        bounds=bp.bounds;lo=np.array(bounds[:2])-np.max(base)-1;hi=np.array(bounds[2:])+np.max(base)+1
        near=np.flatnonzero((origin[:,0]>=lo[0])&(origin[:,0]<=hi[0])&(origin[:,2]>=lo[1])&(origin[:,2]<=hi[1]))
        for i in near:
            pt=Point(origin[i,[0,2]])
            if wp.distance(pt)<radius[i]:water_hits.append(int(i))
            if bp.distance(pt)<base[i]+.5:bed_hits.append(int(i))
    failures=dict(origin=bad_origin,trunk_support=bad_support,tilt=bad_tilt,native_water=np.flatnonzero(native_water),sea_band=np.flatnonzero(sea_band),pilot_water=np.array(water_hits,int),pilot_bed_margin=np.array(bed_hits,int))
    failures.update({k:np.flatnonzero(v) for k,v in transforms.items()})
    failures['nonfinite_interior_support']=invalid_support
    detailed={k:[dict(id=int(ids[i]),model=names[i],root=origin[i].tolist(),root_delta=float(dy[i]),trunk_gap=float(gap[i]) if np.isfinite(gap[i]) else None) for i in ix[:50]] for k,ix in failures.items()}
    bad=any(len(ix) for ix in failures.values())
    result=dict(status='FAIL' if bad else ('INCONCLUSIVE_BOUNDARY_SUPPORT' if boundary.any() else 'SUPPORT_CLEARANCE_PASS'),instances=count,counts={k:len(ix) for k,ix in failures.items()},examples=detailed,
                boundary_pending=dict(count=int(boundary.sum()),ids=ids[boundary].astype(int).tolist(),
                                      examples=[dict(id=int(ids[i]),model=names[i],root=origin[i].tolist(),required_radius=float(required_radius[i])) for i in np.flatnonzero(boundary)[:50]]),
                violations={k:[int(ids[i]) for i in ix] for k,ix in failures.items()},
                max_origin_error=float(abs(dy).max()),max_trunk_gap=float(gap[selected][np.isfinite(gap[selected])].max()),
                source_wrp_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),terrain_sha256=hashlib.sha256(T.read_bytes()).hexdigest(),
                geom_consumer_sha256=hashlib.sha256((geompath/'geom.py').read_bytes()).hexdigest(),
                limits=['Source WRP support and saved model base water/bed margins only.','Boundary discs crossing the measured 0..12282 grid require an engine/reference contract; no clamp-based PASS.','No compiled forest WRP, engine, density, AI or appearance verdict.'])
    (a.output or S/'forest-support-review-full.json').write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k not in ('examples','violations','boundary_pending')},indent=2))
    raise SystemExit(0 if result['status']=='SUPPORT_CLEARANCE_PASS' else 1)


if __name__=='__main__':main()
