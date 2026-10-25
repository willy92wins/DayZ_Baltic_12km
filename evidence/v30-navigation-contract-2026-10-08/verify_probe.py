from pathlib import Path
import hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools/playtest'))
from read_water_temporal_v30 import read_series,read_order
ref=json.loads((OUT/'probe-reference.json').read_text())
assert {p['id'] for p in ref['points']}=={4001,4002,4003}

def judge(text):
    got=read_series(ref,text);points={p['id']:p for p in got['results']}
    rows=[s.split(';') for s in text.splitlines()[2:-1]]
    phases=[]
    for name,first,count in [('calm',0,31),('storm',31,31)]:
        selected=[r for r in rows if first<=int(r[1])<first+count]
        winds=[float(r[15]) for r in selected];cloud=[float(r[16]) for r in selected]
        ok=max(winds)<=1 and max(cloud)<=.15 if name=='calm' else min(winds)>=15 and min(cloud)>=.95
        phases.append(dict(name=name,reached=ok,wind=[min(winds),max(winds)],overcast=[min(cloud),max(cloud)]))
    checks=dict(complete=got['point_count']==3 and got['samples_per_point']==62,
                actual_floor_1m=all(abs(points[i]['ranges']['ground'][k]-1)<.002 for i in (4001,4002) for k in ('min','max')),
                repaired_beds_pond=all(points[i]['pond_true']==62 for i in (4001,4002)),
                repaired_beds_depth=all(points[i]['ranges']['depth_bed']['min']>=.95 for i in (4001,4002)),
                unchanged_control=points[4003]['pond_true']==62 and points[4003]['positive_depth_samples']==62,
                both_weather_settings=all(p['reached'] for p in phases))
    return dict(status='PASS_TWO_HIGH_BEDS_IN_ENGINE' if all(checks.values()) else 'FAIL',checks=checks,series=got,weather=phases)
for filename,target in [('baltic_bug_recheck_high_bed_probe_v1.log','runtime.log'),('baltic_bug_recheck_high_bed_order_v1.log','order.log')]:
    dest=OUT/target;assert not dest.exists();shutil.copyfile(Path('P:/DayZ_MCP_dev/_server/profiles')/filename,dest)
text=(OUT/'runtime.log').read_text(encoding='utf-8-sig');result=judge(text)
result['order']=read_order(ref,text,(OUT/'order.log').read_text(encoding='utf-8-sig'))
negative={}
for name,field,value,ident in [('pond_lost',6,'false','4001'),('depth_below_contract',9,'0.94','4002'),('old_terrain',4,'-1.603338','4001'),('control_lost',6,'false','4003')]:
    lines=text.splitlines()
    for k,line in enumerate(lines):
        f=line.split(';')
        if len(f)==17 and f[0]=='T' and f[1]=='31' and f[2]==ident:
            f[field]=value;lines[k]=';'.join(f);break
    else:raise AssertionError(name)
    try:negative[name]=judge('\n'.join(lines)+'\n')['status']=='FAIL'
    except AssertionError:negative[name]=True
assert all(negative.values())
result.update(negative=negative,files={p:hashlib.sha256((OUT/p).read_bytes()).hexdigest() for p in ['probe-reference.json','runtime.log','order.log']},
              limits=['Two repaired vertices and one unchanged control, 62 samples each in two weather settings.',
                      'No global minimum under a maximum wave, visual or final navmesh acceptance.'])
(OUT/'runtime-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(status=result['status'],checks=result['checks'],negative=negative,
                     points=[dict(id=p['id'],ground=p['ranges']['ground'],min_depth=p['ranges']['depth_bed']['min']) for p in result['series']['results']]),indent=1))
assert result['status']=='PASS_TWO_HIGH_BEDS_IN_ENGINE'
