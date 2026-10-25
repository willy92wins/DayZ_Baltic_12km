from pathlib import Path
from collections import defaultdict
import hashlib,json,math,datetime
O=Path(__file__).parent;D=O/'water-temporal-ae';raw=D/'baltic_water_temporal_ev112.log'
ps={p['id']:p for p in json.loads((D/'points.json').read_text())};lines=raw.read_text().splitlines()
assert lines[0]=='BALTIC_WATER_TEMPORAL_EV112;BalticTrial'
assert lines[1]=='BEGIN;30;8' and lines[-1]=='END;30;8' and len(lines)==243
launch=json.loads((D/'launch.json').read_text());assert raw.stat().st_mtime>=datetime.datetime.fromisoformat(launch['requested_at_utc']).timestamp()
rows=defaultdict(list);keys=set()
for l in lines[2:-1]:
 a=l.split(';');assert len(a)==13 and a[0]=='P';sample,ms,pid=map(int,a[1:4]);assert 0<=sample<30 and pid in ps and (sample,pid) not in keys;keys.add((sample,pid))
 assert a[5] in ('true','false') and a[6] in ('true','false')
 r=dict(sample=sample,ms=ms,ground=float(a[4]),sea=a[5]=='true',pond=a[6]=='true',nofake=float(a[7]),depth=float(a[8]),road=float(a[9]),objects=int(a[10]),withfake=float(a[11]),sea_wave_current=float(a[12]));assert all(math.isfinite(v) for v in r.values());rows[pid].append(r)
result={}
for pid,rs in rows.items():
 assert len(rs)==30 and sorted(r['sample'] for r in rs)==list(range(30))
 rng=lambda k:[min(r[k] for r in rs),max(r[k] for r in rs)]
 result[str(pid)]=dict(kind=ps[pid]['kind'],family_id=ps[pid]['family_id'],expect=ps[pid]['expect'],samples=30,duration_ms=rs[-1]['ms']-rs[0]['ms'],ground_range=rng('ground'),depth_range=rng('depth'),nofake_range=rng('nofake'),withfake_range=rng('withfake'),sea_values=sorted(set(r['sea'] for r in rs)),pond_values=sorted(set(r['pond'] for r in rs)),positive_depths=sum(r['depth']>0 for r in rs),crosses_zero=min(r['depth'] for r in rs)<=0<max(r['depth'] for r in rs),max_depth_minus_withfake_ground_error=max(abs(r['depth']-(r['withfake']-r['ground'])) for r in rs),max_depth_minus_withfake_query_error=max(abs(r['depth']-(r['withfake']-r['ground']-0.01)) for r in rs),objects_range=rng('objects'))
out=dict(status='DIAGNOSTIC_COMPLETE_NOT_ACCEPTANCE',rows=len(keys),run_id=launch['tool_result']['run_id'],raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),points=result,required_points_cross_zero=all(result[str(i)]['crosses_zero'] for i in (2733,3807,3808,3836)),limits='One minute, fixed weather, eight points. No bound for all weather; original strict FAIL unchanged.')
(D/'diagnosis.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
