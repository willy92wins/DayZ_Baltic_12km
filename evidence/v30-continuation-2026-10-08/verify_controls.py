from pathlib import Path
import copy,hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools/playtest'))
from read_water_temporal_v30 import read_series,read_order,controls
for name,target in [('baltic_bug_recheck_water_v3.log','controls-runtime.log'),('baltic_bug_recheck_water_order_v3.log','controls-order.log')]:
    dest=OUT/target;assert not dest.exists();shutil.copyfile(Path('P:/DayZ_MCP_dev/_server/profiles')/name,dest)
ref=json.loads((OUT/'controls-reference.json').read_text());text=(OUT/'controls-runtime.log').read_text(encoding='utf-8-sig')
got=read_series(ref,text);order=read_order(ref,text,(OUT/'controls-order.log').read_text(encoding='utf-8-sig'))
checks=dict(shallow_both_phases=got['gate']['status']=='PASS_SHALLOW_DEPTH_BOTH_PHASES',
            positive_and_dry_controls=got['control_gate']['status']=='PASS_REFERENCE_CONTROLS',
            coverage=got['point_count']==18 and got['samples_per_point']==302)
negative={}
for name,ident,field,value in [('high_pond_lost',2001,6,'false'),('high_pond_dry',2001,9,'-0.01'),('dry_control_wet',693,6,'true')]:
    lines=text.splitlines()
    for k,line in enumerate(lines):
        f=line.split(';')
        if len(f)==17 and f[0]=='T' and int(f[1])==151 and int(f[2])==ident:
            f[field]=value;lines[k]=';'.join(f);break
    else:raise AssertionError(name)
    negative[name]=read_series(ref,'\n'.join(lines)+'\n')['control_gate']['status']=='FAIL_REFERENCE_CONTROLS'
missing=copy.deepcopy(ref);next(p for p in missing['points'] if p['id']==2001)['role']='unclassified_observer'
negative['positive_role_removed']=read_series(missing,text)['control_gate']['status']=='INCONCLUSIVE_REFERENCE_CONTROLS'
checks['negative_controls_rejected']=all(negative.values())
report=dict(status='PASS_CURRENT_SHORE_AND_REFERENCE_CONTROLS' if all(checks.values()) else 'FAIL',
            checks=checks,current=got,order=order,negative=negative,reader_controls=controls(),
            files={p:hashlib.sha256((OUT/p).read_bytes()).hexdigest() for p in ['controls-reference.json','controls-runtime.log','controls-order.log']},
            limits=['Seven shallow sites, two positive ponds, sea and eight dry controls.',
                    'Only the 302-sample calm/storm experiment; not maximum waves, global visuals or navigation.'])
(OUT/'controls-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(status=report['status'],checks=checks,negative=negative,
                     depths=[dict(id=p['id'],pond=p['pond_true'],min=p['ranges']['depth_bed']['min']) for p in got['results'] if p['id'] in (765,1176,2001)]),indent=1))
raise SystemExit(0 if all(checks.values()) else 1)
