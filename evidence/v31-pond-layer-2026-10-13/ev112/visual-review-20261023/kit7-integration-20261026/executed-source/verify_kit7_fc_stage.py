"""Independent 0WZD streaming comparison; does not trust writer delta/digest."""
from pathlib import Path
from collections import Counter
import hashlib,json,struct,sys
import numpy as np
if not __debug__: raise RuntimeError('Assertions required')
R=Path(__file__).parent; V=R/'kit7-stage-review-20261026'; O=R/'stage-kit7-fc-20261026'
B=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018')
sys.path.insert(0,str(R))
from check_kit7_stage_inputs import validate
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text())
def pre(f):
    header=f.read(24); magic,tx,tz,nx,nz,cell=struct.unpack('<4s4If',header); assert magic==b'0WZD' and (nx,nz)==(2048,2048)
    heights=f.read(nx*nz*4); assert len(heights)==nx*nz*4
    materials=bytearray(f.read(tx*tz*2)); raw=f.read(4); materials.extend(raw); n=struct.unpack('<I',raw)[0]
    for _ in range(n):
        while True:
            raw=f.read(4); materials.extend(raw); length=struct.unpack('<I',raw)[0]
            if not length:break
            raw=f.read(length); assert len(raw)==length; materials.extend(raw)
    return header,heights,bytes(materials)
def row(f):
    h=f.read(56); assert len(h)==56; ident,n=struct.unpack_from('<II',h,48)
    if n==0: assert not f.read(1); return None,h,None,None
    name=f.read(n); assert len(name)==n
    return ident,h+name,name.decode('ascii').rstrip('\0').lower(),struct.unpack('<12f',h[:48])
def ground(grid,x,z):
    # Separate barycentric implementation of the documented NW-SE native split.
    col=x/6; rr=(12282-z)/6; c=min(2046,max(0,int(np.floor(col)))); r=min(2046,max(0,int(np.floor(rr))))
    u=col-c; v=rr-r
    # Preserve native float32 vertex differences, then evaluate in float64.
    nw,ne,sw,se=grid[r,c],grid[r,c+1],grid[r+1,c],grid[r+1,c+1]
    if u>=v:return float(nw)+u*float(ne-nw)+v*float(se-ne)
    return float(nw)+v*float(sw-nw)+u*float(se-sw)
def main():
    gate=read(V/'accepted.json'); validate(gate)
    src=R/'stage-rectangle-f/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'; dst=O/'root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
    sr=read(R/'stage-rectangle-f/stage-report.json'); models=read(sr['forest_reference']['path'])['models']
    H0=np.load(R/'rectangle-pilot-f-merged/terrain-buried.npz')['heights']; H=np.load(R/'river-kit7-merged-byteexact-20261026/terrain-buried.npz')['heights']
    old=Counter((r['model'].lower(),struct.pack('<12f',*r['matrix'])) for r in read(B/'water-fix-b/kit/kit-records.json') if r['site']=='kit-7')
    drops={x['id']:x for x in read(R/'kit7-forest-impact-20261026/result.json')['conflicts']}
    oldids=set()
    with (B/'stage-nonforest-c/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp').open('rb') as f:
        pre(f)
        while True:
            ident,_,_,_=row(f)
            if ident is None:break
            assert ident not in oldids; oldids.add(ident)
    added=read(R/'river-kit7-midpoint-a-20261026/records.json'); ids=set(); outids=set(); maximum=0; removed=[]; excluded=[]; changed=[]; calculated=[]; oldpilot=0; pilotnames=[]; srcn=0; dstn=0; outside=0; exact=0
    with src.open('rb') as a,dst.open('rb') as b:
        ha,ya,ma=pre(a); hb,yb,mb=pre(b); assert ha==hb and ma==mb
        assert ya==np.ascontiguousarray(H0[::-1],dtype='<f4').tobytes() and yb==np.ascontiguousarray(H[::-1],dtype='<f4').tobytes()
        while True:
            ident,raw,name,mat=row(a)
            if ident is None: term=raw; break
            assert ident not in ids; ids.add(ident); maximum=max(maximum,ident); srcn+=1
            tag=(name,raw[:48])
            if old[tag]: old[tag]-=1; removed.append(ident); continue
            if ident in drops:
                assert name==drops[ident]['model'] and name in models; excluded.append(ident); continue
            oi,actual,on,om=row(b); assert oi==ident and on==name and oi not in outids; outids.add(oi); dstn+=1
            expect=raw
            if ident not in oldids and not name.startswith('baltic_stream_pilot\\'):
                assert name in models
                bc=models[name]['bc']; root=[mat[9+j]-sum(mat[3*k+j]*bc[k] for k in range(3)) for j in range(3)]
                if 0<=root[0]<=12282 and 0<=root[2]<=12282:
                    delta=ground(H,root[0],root[2])-ground(H0,root[0],root[2])
                    if delta: calculated.append(ident)
                    expect=raw[:40]+struct.pack('<f',mat[10]+delta)+raw[44:]
                else: outside+=1
            assert actual==expect,('unexpected object bytes',ident,name)
            if raw!=actual: changed.append(ident)
            else: exact+=1
            if name.startswith('baltic_stream_pilot\\'): assert raw==actual; oldpilot+=1;pilotnames.append(name)
        assert not sum(old.values()) and len(removed)==174 and set(excluded)==set(drops) and len(excluded)==292
        for ix,add in enumerate(added,1):
            oi,actual,on,om=row(b); assert oi==maximum+ix and oi not in outids; outids.add(oi); dstn+=1
            assert on==add['model'].lower() and actual[:48]==struct.pack('<12f',*add['matrix'])
            assert actual[56:]==add['model'].encode('ascii')
        oi,end,_,_=row(b); assert oi is None and end==term
    assert (srcn,dstn,oldpilot,len(calculated),outside)==(2578725,2578398,62,1623,2918)
    P=R/'pilot-kit7-fc-20261026';pa=read(P/'author-report.json')
    u=read(R/'collision-overlap-u2/author-report.json');c=read(R/'river-131-midpoint-c/author-report.json');k=read(R/'river-kit7-midpoint-a-20261026/author-report.json')
    cm={i['model']:i for i in c['instances']}; expected_instances=[cm.get(i['model'],i) for i in u['instances']]+k['instances']
    assert pa['instances']==expected_instances and pa['sites']==u['sites']+k['sites']
    assert len({i['model'] for i in pa['instances']})==len(pa['instances'])==201 and len({s['site'] for s in pa['sites']})==4
    assert set(pilotnames)=={i['model'].lower() for i in u['instances']} and len(pilotnames)==62
    assert {a['model'] for a in added}=={i['model'] for i in k['instances']}
    for inst in pa['instances']:assert sha(P/'source'/inst['model'].replace('\\','/'))==inst['sha256']
    # All non-WRP source world files and baseline configuration must remain byte-exact.
    base=src.parent; new=dst.parent
    files={str(p.relative_to(base)):sha(p) for p in base.rglob('*') if p.is_file() and p!=src}
    got={str(p.relative_to(new)):sha(p) for p in new.rglob('*') if p.is_file() and p!=dst}; assert files==got
    for n in ['baseline-config.bin','baseline-config.cpp','decode-config.log']: assert sha(R/'stage-rectangle-f'/n)==sha(O/n)
    assert all(sha(p)==h for p,h in gate['inputs'].items())
    result=dict(status='PASS_INDEPENDENT_SOURCE_COMPOSITION',source_wrp_sha256=sha(src),wrp_sha256=sha(dst),source_objects=srcn,objects=dstn,removed_old_kit=len(removed),removed_forest=len(excluded),retained_byte_exact=exact,existing_pilot_poses_exact=oldpilot,new_pilot_poses=len(added),calculated_height_deltas=len(calculated),effective_float32_height_changes=len(changed),outside_roots_unchanged=outside,world_side_files_byte_exact=len(files),inputs_unchanged=True,limits=['Source bytes/heights only. Full forest, compiled WRP, package, native/nav/client acceptance pending.'])
    (O/'independent-source-review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__': main()
