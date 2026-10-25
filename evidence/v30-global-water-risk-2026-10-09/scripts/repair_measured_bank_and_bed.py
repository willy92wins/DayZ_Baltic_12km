"""Ten declared native vertices: nine physically flooded Narva banks and one exposed stream bed."""
from pathlib import Path
import json,hashlib,sys,csv,math
import numpy as np
from shapely.geometry import shape
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290');E=W/'evidence/v30-global-water-risk-2026-10-09'
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009');sys.path.insert(0,str(W/'tools/terrain'))
from v30_common import cell_planes,tri_sample
from audit_fairway_triangles_v30 import records,depths
from verify_roads_v30 import evaluate
from audit_pond_topology import compare,controls
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
src=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008/candidate-c1r3p/terrain_valley.npz')
assert sha(src)=='9c3011b8af5279e807630d4e91512d2e95a434463d3523a5b4074e70bc7cc8f6'
t=dict(np.load(src));h=t['heights'].astype(float);v=h.copy();allowed=np.zeros_like(h,dtype=bool)
classification={(p['row'],p['col']):p for p in json.loads((E/'native-anomaly-classification.json').read_text())['points']}
banks=[p for p in csv.DictReader((E/'halo-physical-anomalies.csv').open()) if p['cls']=='0' and classification[p['row'],p['col']]['reason']=='source_dry_below_neighbor_pond_plane']
assert len(banks)==9
changed=[]
for p in banks:
    r,c=int(p['row']),int(p['col']);assert t['cls'][r,c]==0
    target=float(p['plane'])+.35;assert target>h[r,c]
    v[r,c]=target;allowed[r,c]=True
    changed.append(dict(kind='flooded_dry_bank',row=r,col=c,x=c*6,z=12282-r*6,before=h[r,c],after=target,measured_water=float(p['plane'])))
series=json.loads((E/'halo-consumers-runtime-verification.json').read_text())['series']['results']
probe=json.loads((E/'halo-consumers-reference.json').read_text())['points'];byid={p['id']:p for p in probe}
observed=[p for p in series if byid[p['id']].get('case')=='closed_microgap' and abs(p['x']-9174)<.1 and abs(p['z']-756)<.1]
assert len(observed)==5 and all(p['pond_true']==62 for p in observed)
worst=min(p['ranges']['depth_bed']['min'] for p in observed);lower=math.ceil((.02-worst)/.01)*.01
r,c=1921,1529;assert 0<lower<=.08 and t['cls'][r,c]==6
v[r,c]-=lower;allowed[r,c]=True
changed.append(dict(kind='wave_exposed_stream_bed',row=r,col=c,x=9174,z=756,before=h[r,c],after=v[r,c],worst_observed_depth=worst,lowering=lower,target_observed_margin=.02))
v=v.astype(t['heights'].dtype).astype(float)
w=np.load('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008/r3-transition-proposal/terrain_flat.npz');plane=cell_planes(w['cls'],w['level'])
nav=[];navsupport=np.zeros_like(allowed)
for path in [Path('E:/DayZ-Baltic-Build/v30-v11/06-evidence/corridors.geojson'),W/'evidence/v30-delta-fairways-2026-10-02/axes-corridors.geojson']:
    for f in json.loads(path.read_text())['features']:
        if f['properties'].get('kind','corridor24m')!='corridor24m':continue
        rec=records(shape(f['geometry']),plane);navsupport.ravel()[np.unique(rec['ids'])]=True
        a,b=depths(h,rec),depths(v,rec)
        nav.append(dict(name=f['properties'].get('name',f['properties'].get('river')),faces=rec['faces'],minimum_before=float(a.min()),minimum_after=float(b.min()),exact=bool(np.array_equal(a,b))))
struct=t['reserve']|t['platform']|t['beach'];wet=t['cls']>0
refs=[]
for path in [W/'evidence/v30-valley-smoothing-2026-10-08/c1r3p-probe-reference.json',W/'evidence/v30-bug-recheck-2026-10-08/wave-fixed-reference.json']:
    refs+=json.loads(path.read_text())['points']
xy=np.array([[p['x'],p['z']] for p in refs])
def judge(a):
    return dict(finite=bool(np.isfinite(a).all()),scope=not bool(((a!=h)&~allowed).any()),
        engineering_exact=not bool(((a!=h)&struct).any()),corridor_support_exact=not bool(((a!=h)&navsupport).any()),
        historical_exact=bool(np.max(np.abs(tri_sample(a,xy[:,0],xy[:,1])-tri_sample(h,xy[:,0],xy[:,1])))<1e-6),
        bed_floor=bool(np.min(a[allowed&wet])>=1.),
        bank_clearance=all(a[p['row'],p['col']]>=p['measured_water']+.34999 for p in changed if p['kind']=='flooded_dry_bank'),
        measured_bed_lowered=bool(a[1921,1529]<=h[1921,1529]-lower+1e-5))
checks=judge(v);bad=0
for dr,dc in ((0,1),(1,0)):
    def slopes(a):
        mid=a[dr:dr+2047,dc:dc+2047]
        return np.degrees(np.arctan(np.hypot(mid-a[:-1,:-1],a[1:,1:]-mid)/6))
    land=~wet[:-1,:-1]|~wet[dr:dr+2047,dc:dc+2047]|~wet[1:,1:]
    bad+=int((land&(slopes(v)>np.maximum(slopes(h),35)+1e-4)).sum())
checks['slopes']=bad==0
topology,_=compare(h,v,plane);checks['pond_topology']=topology['status']=='PASS_FROZEN_POND_MODEL'
roads=evaluate(v,t['water'].astype(bool));checks['roads']=roads['status']=='PASS'
neg={}
for key,p,amount,gate in [('bank_unfixed',(changed[0]['row'],changed[0]['col']),None,'bank_clearance'),('bed_unfixed',(1921,1529),None,'measured_bed_lowered'),('bed_below_floor',(1921,1529),.99,'bed_floor')]:
    a=v.copy();a[p]=h[p] if amount is None else amount;neg[key]=not judge(a)[gate]
r,c=np.argwhere(struct&~wet)[100];a=v.copy();a[r,c]+=.1;neg['engineering_changed']=not judge(a)['engineering_exact']
neg.update(controls());assert all(neg.values())
out=B/'measured-bank-bed-r1';out.mkdir(exist_ok=False)
np.savez_compressed(out/'terrain.npz',**dict(t,heights=v.astype(t['heights'].dtype)))
u=dict(np.load(out/'terrain.npz'));checks['metadata_exact']=all(np.array_equal(t[k],u[k],equal_nan=True) for k in t if k!='heights')
report=dict(status='PASS_OFFLINE_MEASURED_BANK_BED' if all(checks.values()) else 'FAIL_NOT_FOR_PACKAGING',checks=checks,negative=neg,changes=changed,
    terrain_sha256=sha(out/'terrain.npz'),source_sha256=sha(src),navigation=nav,topology=topology,roads=roads,
    limits=['Ten declared vertices only; physical readback and complete raster repeat required.','The visual residual at 2718.485/6812.813 is not changed or closed.'])
(E/'measured-bank-bed-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('navigation','roads','topology')},indent=2))
print(json.dumps(dict(topology=topology['status'],road_status=roads['status'],navigation_support_changes=sum(not p['exact'] for p in nav))))
