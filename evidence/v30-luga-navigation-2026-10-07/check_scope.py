"""Independent native-face invariants, frozen stations and interleaved holdout."""
from pathlib import Path
import sys, json, hashlib, importlib.util
import numpy as np
import shapely
from shapely.geometry import shape
W=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(W/'tools/terrain'),str(W/'tools/water')]
from audit_waterline_v30 import measure
spec=importlib.util.spec_from_file_location('previous_check',W/'evidence/v30-smoothing-pilot-2026-10-07/scripts/check_luga.py')
previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous)
B=Path('E:/DayZ-Baltic-Build/v30-smoothing-pilot-20261007')
OUT=Path('E:/DayZ-Baltic-Build/v30-luga-navigation-20261007')
BASE=Path('E:/DayZ-Baltic-Build/v30-v12/inland/terrain_inland.npz')
CAND=OUT/'luga-scoped/terrain_inland.npz'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def faces_unchanged(a,b,cls):
    # Explicit cells/corners, independent of the producer's dilation operation.
    foreign=(cls>0)&(cls!=3)
    touching=foreign[:-1,:-1]|foreign[:-1,1:]|foreign[1:,:-1]|foreign[1:,1:]
    changed=a!=b
    changed_cells=changed[:-1,:-1]|changed[:-1,1:]|changed[1:,:-1]|changed[1:,1:]
    return int(np.count_nonzero(touching&changed_cells))

def main():
    assert sha(BASE)=='8b3a8c5541403abaf852e14fb4c0651175e6dcaa541f6f8a151f1db04ac7a8a6'
    with np.load(BASE) as f:base=dict(f)
    with np.load(CAND) as f:new=dict(f)
    with np.load(B/'luga-18-vector/terrain_inland.npz') as f:old=f['heights']
    with np.load(B/'luga-frozen-masks.npz') as f:fixed=f['frozen'];allowed=f['allowed'];corridor=f['corridor']
    with np.load(B/'luga-waterline-stations.npz') as f:s=dict(f)
    gates={'metadata_exact':all(np.array_equal(v,new[k],equal_nan=True) for k,v in base.items() if k!='heights'),
           'corridor_exact':np.array_equal(base['heights'][corridor],new['heights'][corridor]),
           'outside_allowed_exact':np.array_equal(base['heights'][~allowed],new['heights'][~allowed]),
           'foreign_water_cells_exact':faces_unchanged(base['heights'],new['heights'],base['cls'])==0}
    bad_old=faces_unchanged(base['heights'],old,base['cls'])
    wrong=new['heights'].copy();vertex=tuple(np.argwhere(base['cls']==2)[0]);wrong[vertex]+=.1
    negative={'old_candidate_rejected':bad_old>0,'corrupted_foreign_vertex_rejected':faces_unchanged(base['heights'],wrong,base['cls'])>0}
    fc=json.loads(Path('E:/DayZ-Baltic-Build/v30-redesign/design/water_v3.geojson').read_text(encoding='utf8'))['features']
    luga=next(shape(f['geometry']) for f in fc if f['properties'].get('id')=='Luga_0')
    others=shapely.union_all([shape(f['geometry']) for f in fc if f['properties'].get('id')!='Luga_0'])
    pp=[];nn=[];rid=[]
    for poly in getattr(luga,'geoms',[luga]):
        for ring in [poly.exterior,*poly.interiors]:
            count=int(ring.length//2)
            if count<4:continue
            p=np.array([ring.interpolate(d).coords[0] for d in np.arange(count)*2.+1])
            tangent=np.roll(p,-1,axis=0)-np.roll(p,1,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1,keepdims=True),1e-12)
            normal=np.column_stack([tangent[:,1],-tangent[:,0]]);normal[shapely.contains(poly,shapely.points(p+normal))]*=-1
            rid.append(np.full(count,len(rid)));pp.append(p);nn.append(normal)
    P=np.vstack(pp);N=np.vstack(nn);RID=np.concatenate(rid)
    keep=(P[:,0]>66)&(P[:,0]<12216)&(P[:,1]>66)&(P[:,1]<12216)&(np.hypot(P[:,0]-2417.1428,P[:,1]-6889.885)>620)&(shapely.distance(shapely.points(P),others)>18)
    c=np.clip(np.rint(P[:,0]/6).astype(int),0,2047);r=np.clip(np.rint((12282-P[:,1])/6).astype(int),0,2047);keep &= ~fixed[r,c]
    results={}
    for label,p,n,ring,k in [('frozen',s['points'],s['normal'],s['ring_id'],s['keep']),('interleaved_1m',P,N,RID,keep)]:
        previous.NORMAL=n
        _,before=measure(str(BASE),p,n,np.full(len(p),'river'),ring,np.ones(len(p),bool))
        _,after=measure(str(CAND),p,n,np.full(len(p),'river'),ring,np.ones(len(p),bool))
        sectors={'all':k,'west':k&(p[:,0]<5000),'central':k&(p[:,0]>=5000)&(p[:,0]<8000),'east':k&(p[:,0]>=8000)}
        data={}
        for sec,mask in sectors.items():
            a=previous.stats(p,ring,before,mask);b=previous.stats(p,ring,after,mask)
            newly_missing=np.flatnonzero(mask&np.isfinite(before)&~np.isfinite(after))
            checks={'missing_count':b['missing']<=a['missing'],'no_new_missing_individually':len(newly_missing)==0,'offset_p90':b['offset_p90_m']<=a['offset_p90_m'],'zigzag':b['zigzag_rms_m']<a['zigzag_rms_m']}
            data[sec]={'before':a,'after':b,'checks':checks,'new_missing_indices':newly_missing.tolist()}
            gates.update({label+'_'+sec+'_'+key:bool(val) for key,val in checks.items()})
        results[label]=data
        np.savez_compressed(OUT/('stations-'+label+'.npz'),points=p,normal=n,ring_id=ring,keep=k,before=before,after=after)
    gates={k:bool(v) for k,v in gates.items()}
    report={'status':'PASS_OFFLINE_SHORE_ONLY' if all(gates.values()) and all(negative.values()) else 'FAIL','gates':gates,'negative_controls':negative,'old_candidate_changed_foreign_cells':bad_old,'source_sha256':sha(BASE),'candidate_sha256':sha(CAND),'by_station_set':results}
    (OUT/'scope-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps({'status':report['status'],'failed_gates':[k for k,v in gates.items() if not v],'negative':negative,'frozen':results['frozen']['all'],'holdout':results['interleaved_1m']['all']},indent=2))
    return 0 if report['status'].startswith('PASS') else 1

if __name__=='__main__':sys.exit(main())
