"""Derive interval coverage from actual passing actor samples and original routes."""
from pathlib import Path
import argparse, hashlib, json
import numpy as np
import rasterio
from verify_regional_chase import verify,vec

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--reference',type=Path,required=True);ap.add_argument('--parent',type=Path,required=True);ap.add_argument('--log',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    if a.out.exists():raise ValueError('Preserve prior evidence')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    ref=json.loads(a.reference.read_text());parent=json.loads(a.parent.read_text());assert sha(a.parent)==ref['parent_reference_sha256']
    assert sha(Path(ref['terrain']))==ref['terrain_sha256']
    with rasterio.open(ref['terrain']) as ds:height=ds.read(1)
    raw=a.log.read_text();physical=verify(ref,raw,height)
    accepted={c['case'] for c in physical['cases'] if c['status']=='PASS'}
    samples={}
    for line in raw.splitlines():
        f=line.split(';')
        if f[0]=='A' and f[3] not in ('SETTLE','SETTLE_BEGIN'):
            samples.setdefault(int(f[1]),[]).append(vec(f[4])[[0,2]])
    requests=[]
    for source in (8,10,12):
        original=parent['cases'][source];start=np.array(original['start'])[[0,2]];end=np.array(original['goal'])[[0,2]];length=float(np.linalg.norm(end-start))
        requests.append(dict(name=f'original_reverse_{source}',origin=start,axis=(end-start)/length,domain=[0,length],
            selected=[c for c in ref['cases'] if c.get('source_case')==source]))
    bridge=parent['bridge']
    for reverse in (False,True):
        requests.append(dict(name='bridge_reverse_'+str(reverse),origin=np.array(bridge['center_xz']),axis=np.array(bridge['axis_xz']),domain=[-135,135],
            selected=[c for c in ref['cases'] if c['kind']=='bridge' and c['reverse']==reverse]))
    reports=[]
    for request in requests:
        intervals=[];failed=[]
        for case in request['selected']:
            ident=case['case']
            if ident not in accepted:failed.append(ident);continue
            station=(np.array(samples[ident])-request['origin'])@request['axis']
            intervals.append(dict(case=ident,lo=float(station.min()),hi=float(station.max())))
        ordered=sorted(intervals,key=lambda x:x['lo']);merged=[]
        for interval in ordered:
            lo,hi=interval['lo'],interval['hi']
            if merged and lo<=merged[-1][1]+.002:merged[-1][1]=max(merged[-1][1],hi)
            else:merged.append([lo,hi])
        radius=ref['criteria']['goal_radius_m'];domain=request['domain']
        coverage=bool(not failed and len(merged)==1 and merged[0][0]<=domain[0]+radius and merged[0][1]>=domain[1]-radius)
        reports.append(dict(name=request['name'],status='PASS' if coverage else 'FAIL',domain_m=domain,actual_intervals_m=ordered,merged_m=merged,failed_cases=failed))
    passed=physical['status'].startswith('PASS_') and all(r['status']=='PASS' for r in reports)
    result=dict(status='PASS_SHORT_OVERLAPPING_PHYSICAL_AI_COVERAGE' if passed else 'FAIL_SHORT_PHYSICAL_AI_COVERAGE',physical_status=physical['status'],groups=reports,
        source_sha256={str(p):sha(p) for p in [a.reference,a.parent,a.log]},
        limits=['Actual samples from independently spawned actors; not one long pursuit.','Coverage endpoints allow the original4.002m arrival radius; internal intervals must overlap within2mm.','Original V1/V2 failures remain preserved.','No ordinary perception or multiplayer capacity claim.'])
    a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status=result['status'],groups=[dict(name=r['name'],status=r['status'],failed_cases=r['failed_cases']) for r in reports]),indent=2))
    raise SystemExit(0 if passed else 1)

if __name__=='__main__':main()
