from pathlib import Path
import hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools/playtest'))
from read_water_temporal_v30 import read_series,read_order
ref=json.loads((OUT/'gap-reference.json').read_text())
def judge(text):
    got=read_series(ref,text)
    points={p['id']:p for p in got['results']}
    rows=[s.split(';') for s in text.splitlines()[2:-1]]
    weather=[]
    for name,first,count in [('calm',0,31),('storm',31,31)]:
        selected=[r for r in rows if first<=int(r[1])<first+count]
        winds=[float(r[15]) for r in selected];cloud=[float(r[16]) for r in selected]
        ok=max(winds)<=1 and max(cloud)<=.15 if name=='calm' else min(winds)>=15 and min(cloud)>=.95
        weather.append(dict(name=name,reached=ok,wind=[min(winds),max(winds)],overcast=[min(cloud),max(cloud)]))
    checks=dict(complete=got['point_count']==3 and got['samples_per_point']==62,
                gap_presence=all(points[i]['pond_true']==62 for i in (3001,3002)),
                gap_positive_depth=all(points[i]['positive_depth_samples']==62 for i in (3001,3002)),
                adjacent_control=points[3003]['pond_true']==62 and points[3003]['positive_depth_samples']==62,
                both_weather_settings=all(p['reached'] for p in weather))
    return dict(status='PASS_LOCAL_JUNCTION_WATER' if all(checks.values()) else 'FAIL',checks=checks,series=got,weather=weather)
for name,target in [('baltic_bug_recheck_junction_probe_v1.log','gap-fixed-runtime-r2.log'),('baltic_bug_recheck_junction_order_v1.log','gap-fixed-order-r2.log')]:
    dest=OUT/target;assert not dest.exists();shutil.copyfile(Path('P:/DayZ_MCP_dev/_server/profiles')/name,dest)
text=(OUT/'gap-fixed-runtime-r2.log').read_text(encoding='utf-8-sig');result=judge(text)
result['order']=read_order(ref,text,(OUT/'gap-fixed-order-r2.log').read_text(encoding='utf-8-sig'))
negative={}
for name,file in [('actual_baseline','gap-baseline-runtime.log'),('actual_no_overlap_candidate','gap-fixed-runtime-r1.log')]:
    negative[name]=judge((OUT/file).read_text(encoding='utf-8-sig'))['status']=='FAIL'
for name,field,value in [('pond_lost',6,'false'),('bed_exposed',9,'-0.01')]:
    lines=text.splitlines()
    for k,line in enumerate(lines):
        f=line.split(';')
        if len(f)==17 and f[0]=='T' and f[1]=='31' and f[2]=='3002':
            f[field]=value;lines[k]=';'.join(f);break
    else:raise AssertionError(name)
    negative[name]=judge('\n'.join(lines)+'\n')['status']=='FAIL'
assert all(negative.values())
result.update(negative=negative,files={p:hashlib.sha256((OUT/p).read_bytes()).hexdigest() for p in ['gap-reference.json','gap-baseline-runtime.log','gap-fixed-runtime-r1.log','gap-fixed-runtime-r2.log']},
              limits=['Three fixed points, 62 samples each; not global seams, boats or a maximum-wave envelope.',
                      'Current terrain is unchanged; old navmesh still awaits the final accepted geometry.'])
(OUT/'gap-verification-r2.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(status=result['status'],checks=result['checks'],negative=negative,
                     points=[dict(id=p['id'],pond=p['pond_true'],min_depth=p['ranges']['depth_bed']['min']) for p in result['series']['results']]),indent=1))
assert result['status']=='PASS_LOCAL_JUNCTION_WATER'
