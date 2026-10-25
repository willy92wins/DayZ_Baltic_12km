"""V3 physical validation plus transition witnesses, against frozen V2 geometry."""
from pathlib import Path
import argparse, hashlib, json, re
import numpy as np
import rasterio
from verify_regional_boat_consumer import verify

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def vector(value):
    m=re.fullmatch(r'<(-?\d+\.\d{6}),\s*(-?\d+\.\d{6}),\s*(-?\d+\.\d{6})>',value)
    if not m:raise ValueError('Bad precise vector')
    p=np.array(list(map(float,m.groups())))
    if not np.isfinite(p).all():raise ValueError('Nonfinite vector')
    return p

def events(case,lines,criteria):
    ts=[];bs=[];arr=[];errors=[]
    for line in lines:
        f=line.split(';')
        try:
            if f[0]=='T':
                if len(f)!=7 or int(f[1])!=case['case']:raise ValueError('Transition schema/case')
                t=float(f[2]);a=int(f[3]);b=int(f[4]);p=vector(f[5]);d=float(f[6])
                if not np.isfinite([t,d]).all():raise ValueError('Nonfinite transition')
                ts.append((t,a,b,p,d))
            elif f[0]=='B':
                if len(f)!=23:raise ValueError('Motion schema')
                bs.append((float(f[2]),int(f[17]),vector(f[22]),f[9],float(f[7])))
            elif f[0]=='ARRIVED':arr.append(float(f[2]))
        except (ValueError,IndexError) as exc:errors.append(str(exc))
    way=np.asarray(case['waypoints_xz']);expected=list(range(1,len(way)-1))
    sequence=[a for _,a,_,_,_ in ts]==expected and all(b==a+1 for _,a,b,_,_ in ts)
    checks={'parse':not errors,'complete_transition_sequence':sequence,'transition_clock':bool(ts and all(x[0]<y[0] for x,y in zip(ts,ts[1:])))}
    geometry=True;witness=True
    for t,a,b,p,d in ts:
        if not 0<=a<len(way):geometry=False;continue
        measured=float(np.linalg.norm(p[[0,2]]-way[a]))
        geometry &= 0<=d<criteria['max_transition_distance_m'] and abs(measured-d)<=.0001
        matches=[q for q in bs if abs(q[0]-t)<=criteria['max_transition_sample_dt_s']]
        witness &= len(matches)==1 and matches[0][1]==b and np.max(np.abs(matches[0][2]-p))<=.00001
    checks.update(transition_geometry=bool(geometry and ts),same_tick_physical_witness=bool(witness and ts))
    # Every physical target must equal the last recorded event at that timestamp.
    consistency=bool(bs);i=0;target=1
    for t,current,_,_,_ in bs:
        while i<len(ts) and ts[i][0]<=t+.000001:target=ts[i][2];i+=1
        if current!=target:consistency=False
    checks['physical_targets_match_events']=consistency
    arrival_ok=False;engine_off=False;observed=0.;final_speed=None
    if len(arr)==1 and bs:
        witnessed=[q for q in bs if abs(q[0]-arr[0])<=criteria['max_transition_sample_dt_s']]
        if len(witnessed)==1:
            q=witnessed[0]
            arrival_ok=np.linalg.norm(q[2][[0,2]]-way[-1])<criteria['arrival_distance_m'] and q[4]<=criteria['arrival_speed_mps']
        after=[q for q in bs if q[0]>=arr[0]-.000001]
        observed=bs[-1][0]-arr[0];final_speed=bs[-1][4]
        engine_off=bool(after and all(q[3]=='false' for q in after) and observed>=criteria['engine_off_observation_s'])
    checks.update(arrival_distance_and_speed=bool(arrival_ok),engine_off_observation=engine_off)
    return dict(status='PASS' if all(checks.values()) else 'FAIL',checks=checks,parse_errors=errors,transitions=len(ts),engine_off_observed_s=observed,final_speed_mps=final_speed,limit='Engine off and endpoint retained; no stationary-moored claim.')

def check(ref,folder,height):
    result=[]
    for case in ref['cases']:
        path=folder/f'{ref["log_prefix"]}{case["case"]}.log'
        if not path.exists():result.append(dict(case=case['case'],status='INCOMPLETE',reason='Missing log'));continue
        lines=path.read_text(encoding='utf-8-sig').splitlines()
        physical=verify(dict(ref,cases=[case]),lines,height)
        event=events(case,lines,ref['event_criteria'])
        passed=physical['status'].startswith('PASS_') and event['status']=='PASS'
        result.append(dict(case=case['case'],status='PASS' if passed else 'FAIL',physical=physical,events=event,log_sha256=sha(path)))
    return dict(status='PASS_FOUR_SELECTED_RIVER_SEGMENTS_V3' if all(x['status']=='PASS' for x in result) else 'FAIL_OR_INCOMPLETE',cases=result,limits=ref['limits'])

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--reference',required=True,type=Path);ap.add_argument('--folder',required=True,type=Path);ap.add_argument('--out',required=True,type=Path)
    a=ap.parse_args();assert not a.out.exists(),'Preserve prior result'
    ref=json.loads(a.reference.read_text(encoding='utf-8'))
    for p,d in {**ref['mission'],ref['terrain']:ref['terrain_sha256']}.items():assert sha(Path(p))==d,p
    with rasterio.open(ref['terrain']) as ds:height=ds.read(1)
    report=check(ref,a.folder,height);report['reference_sha256']=sha(a.reference)
    a.out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=report['status'],cases=[dict(case=x['case'],status=x['status']) for x in report['cases']])))
    raise SystemExit(0 if report['status'].startswith('PASS_') else 1)

if __name__=='__main__':main()
