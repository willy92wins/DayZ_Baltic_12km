"""One isolated kit7/F/C source composition. No packaging, deployment or game."""
from pathlib import Path
from collections import Counter
import hashlib, json, shutil, struct, sys
import numpy as np
if not __debug__: raise RuntimeError('Assertions required')
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
B=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018')
S=R/'stage-rectangle-f'; K=R/'river-kit7-midpoint-a-20261026'; M=R/'river-kit7-merged-byteexact-20261026'
O=R/'stage-kit7-fc-20261026'; P=R/'pilot-kit7-fc-20261026'; V=R/'kit7-stage-review-20261026'
sys.path[:0]=[str(R),str(W/'tools/vegetation'),str(W/'tools/terrain'),str(W/'tools/water')]
from check_kit7_stage_inputs import validate
from prune_visual_forest_v31 import prefix,objects
from wrp0wzd import object_record
from streambed_kit_v31 import tri_h
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def read(p): return json.loads(Path(p).read_text())
def write(p,x): Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def key(name,matrix): return name.lower().replace('/','\\').lstrip('\\'),struct.pack('<12f',*matrix)

def main():
    frozen=read(V/'accepted.json'); validate(frozen)
    assert not O.exists() and not P.exists()
    source=S/'root/dayz_baltic_12km_dev/tb/narva_trial'; src=source/'baltic_trial.wrp'
    assert sha(src)=='6e649b72bf4ec6789a83050f21b7e5597de417e14f251f854728eb20d8b84bd8'
    assert read(R/'kit7-compiled-review-20261026/accepted.json')['status']=='ACCEPTED_KIT7_PACKED_OFFLINE'
    assert read(M/'merge-verification.json')['status']=='POND_GEOMETRY_EXACT_KIT7_PENDING_INTEGRATION'
    meta=read(S/'stage-report.json'); models=read(meta['forest_reference']['path'])['models']
    H0=np.load(R/'rectangle-pilot-f-merged/terrain-buried.npz')['heights']; H=np.load(M/'terrain-buried.npz')['heights']
    impact=read(R/'kit7-forest-impact-20261026/result.json')
    drops={int(x['id']):x for x in impact['conflicts']}; assert len(drops)==292
    candidates={int(x['id']):x for x in impact['height_candidates']}; assert len(candidates)==1915
    old=[r for r in read(B/'water-fix-b/kit/kit-records.json') if r['site']=='kit-7']
    remaining=Counter(key(r['model'],r['matrix']) for r in old); assert len(old)==174
    added=read(K/'records.json'); assert len(added)==139 and len({r['model'] for r in added})==139
    assert all(r['site']=='kit-7' for r in added)
    # Source manifest for the unchanged full forest consumer: 35 U2 + 27 C +139 kit7.
    u=read(R/'collision-overlap-u2/author-report.json'); c=read(R/'river-131-midpoint-c/author-report.json'); k=read(K/'author-report.json')
    cm={i['model']:i for i in c['instances']}; assert len(cm)==27
    instances=[]
    for inst in u['instances']:
        root=R/('river-131-midpoint-c' if inst['model'] in cm else 'collision-overlap-u2')
        chosen=cm.get(inst['model'],inst); instances.append((root,chosen))
    assert len(instances)==62 and set(cm)<={i['model'] for _,i in instances}
    instances.extend((K,i) for i in k['instances']); assert len(instances)==201
    assert len({i['model'] for _,i in instances})==201
    P.mkdir()
    for root,inst in instances:
        path=root/'source'/inst['model'].replace('\\','/'); assert sha(path)==inst['sha256']
        dest=P/'source'/inst['model'].replace('\\','/'); dest.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(path,dest)
    author=dict(schema='continuous-stream-composite-v1',sites=u['sites']+k['sites'],instances=[i for _,i in instances],terrain_sha256=sha(M/'terrain-buried.npz'),limits=['Source forest consumer manifest only. Packed composition and engine acceptance pending.'])
    assert len({s['site'] for s in author['sites']})==4
    write(P/'author-report.json',author)
    target=O/'root/dayz_baltic_12km_dev/tb/narva_trial'; target.parent.mkdir(parents=True)
    shutil.copytree(source,target,ignore=shutil.ignore_patterns('baltic_trial.wrp'))
    dest=target/'baltic_trial.wrp'; removed=[]; excluded=[]; shifts=[]; seen=set(); maximum_id=0; count=0; pilot=0
    def flush(batch,g):
        nonlocal maximum_id,count,pilot
        for ident,name,raw in batch:
            assert ident not in seen; seen.add(ident); maximum_id=max(maximum_id,ident)
            mat=struct.unpack_from('<12f',raw); tag=key(name,mat)
            if remaining[tag]:
                remaining[tag]-=1; removed.append(dict(id=ident,model=name,matrix=list(mat),record_sha256=hashlib.sha256(raw).hexdigest())); continue
            if ident in drops:
                d=drops[ident]; assert name==d['model'] and name in models
                root=np.array(mat[9:])-np.array(mat[:9]).reshape(3,3).T@models[name]['bc']
                assert np.allclose(root,d['root'],rtol=0,atol=1e-9)
                excluded.append(dict(id=ident,model=name,matrix=list(mat),record_sha256=hashlib.sha256(raw).hexdigest())); continue
            if ident in candidates:
                assert name in models and name==candidates[ident]['model']
                root=np.array(mat[9:])-np.array(mat[:9]).reshape(3,3).T@models[name]['bc']
                if 0<=root[0]<=12282 and 0<=root[2]<=12282:
                    delta=float(tri_h(H,root[0],root[2])-tri_h(H0,root[0],root[2]))
                    if delta:
                        after=float(np.float32(mat[10]+delta)); changed=struct.pack('<f',after)!=raw[40:44]
                        shifts.append(dict(id=ident,model=name,before=mat[10],after=after,ground_delta=delta,float32_changed=changed))
                        raw=raw[:40]+struct.pack('<f',after)+raw[44:]
            g.write(raw); count+=1; pilot+=name.startswith('baltic_stream_pilot\\')
    with src.open('rb') as f,dest.open('wb') as g:
        pre=prefix(f); assert np.array_equal(np.frombuffer(pre,'<f4',count=2048**2,offset=24).reshape(2048,2048),H0[::-1])
        g.write(pre[:24]+np.ascontiguousarray(H[::-1],dtype='<f4').tobytes()+pre[24+2048**2*4:])
        it=objects(f); batch=[]
        while True:
            try: batch.append(next(it))
            except StopIteration as stop: terminator=stop.value; break
            if len(batch)==4096: flush(batch,g); batch=[]
        if batch: flush(batch,g)
        assert sum(remaining.values())==0 and len(removed)==174 and {r['id'] for r in excluded}==set(drops)
        assert len(shifts)==1623 and pilot==62
        for i,r in enumerate(added,1):
            new_id=maximum_id+i; assert new_id<2**32 and new_id not in seen
            g.write(object_record(r['matrix'],new_id,r['model'].encode('ascii'))); count+=1
        g.write(terminator)
    assert count==2578398
    for name in ('baseline-config.bin','baseline-config.cpp','decode-config.log'): shutil.copy2(S/name,O/name)
    np.save(O/'forest-height-delta.npy',np.array([(r['id'],r['before'],r['after']) for r in shifts],float))
    write(O/'object-delta.json',dict(shifts=shifts,removed_old_kit=removed,excluded_forest=excluded,appended=added))
    report=dict(status='WRITTEN_PENDING_INDEPENDENT_READER',forest=True,source_wrp_sha256=sha(src),wrp_sha256=sha(dest),terrain_sha256=sha(M/'terrain-buried.npz'),object_count=count,remaining_objects=count-201,added_models=201,new_models=139,removed_old_kit_records=meta['removed_old_kit_records']+174,newly_removed_old_kit_records=174,forest_height_adjustments=len(shifts),forest_float32_changes=sum(r['float32_changed'] for r in shifts),forest_excluded=292,forest_reference=meta['forest_reference'],pilot=str(P),merged=str(M),terrain_vertices=int((H!=H0).sum()),limits=['No source acceptance before independent reader. No compiled WRP or runtime acceptance.'])
    write(O/'stage-report.json',report)
    assert all(sha(p)==h for p,h in frozen['inputs'].items()),'input drift during composition'
    print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__': main()
