"""Judge the frozen 28-point readback, with runtime-data negative controls."""
from pathlib import Path
import hashlib,json,shutil,sys
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-global-water-risk-2026-10-09'
sys.path.insert(0,str(W/'tools/playtest'))
from read_water_temporal_v30 import read_series,read_order
ref=json.loads((E/'scalar-temporal-reference.json').read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def judge(text):
    series=read_series(ref,text);got={p['id']:p for p in series['results']}
    checks=dict(complete=series['point_count']==len(ref['points']) and series['samples_per_point']==62,
                controls=series['control_gate']['status']=='PASS_REFERENCE_CONTROLS',
                old_gap_keeps_water=series['gate']['status']=='PASS_SHALLOW_DEPTH_BOTH_PHASES',
                r1_selected_depth=all(got[p['id']]['ranges']['depth_bed']['min']>=.95 for p in ref['points'] if p['reach']=='R1' and p['role']=='high_pond_control'))
    return dict(status='PASS_SCALAR_TEMPORAL_CONTROLS' if all(checks.values()) else 'FAIL',checks=checks,series=series)

for source,target in [('baltic_bug_recheck_scalar_temporal_v1.log','scalar-temporal-runtime.log'),('baltic_bug_recheck_scalar_temporal_order_v1.log','scalar-temporal-order.log')]:
    text=(Path('P:/DayZ_MCP_dev/_server/profiles')/source).read_text(encoding='utf-8-sig')
    assert text.splitlines()[-1]==f"END;62;{len(ref['points'])}", 'Run incomplete'
    assert not (E/target).exists();shutil.copyfile(Path('P:/DayZ_MCP_dev/_server/profiles')/source,E/target)
text=(E/'scalar-temporal-runtime.log').read_text(encoding='utf-8-sig');result=judge(text)
result['order']=read_order(ref,text,(E/'scalar-temporal-order.log').read_text(encoding='utf-8-sig'))
negative={}
for name,ident,field,value in [('pond_lost',5001,6,'false'),('terrain_wrong',5002,4,'99'),('dry_flood',5028,9,'0.2')]:
    lines=text.splitlines()
    for k,line in enumerate(lines):
        f=line.split(';')
        if len(f)==17 and f[:3]==['T','31',str(ident)]:f[field]=value;lines[k]=';'.join(f);break
    else:raise AssertionError(name)
    try:negative[name]=judge('\n'.join(lines)+'\n')['status']=='FAIL'
    except AssertionError:negative[name]=True
try:judge('\n'.join(text.splitlines()[:-1]))
except AssertionError:negative['missing_terminal']=True
else:negative['missing_terminal']=False
assert all(negative.values())
result.update(negative=negative,files={p:sha(E/p) for p in ('scalar-temporal-reference.json','scalar-temporal-runtime.log','scalar-temporal-order.log')},
              limits=['120 R2 controls plus 231 diagnostic scalar disagreements. A control PASS does not accept the diagnostic dry points or maximum-wave envelope.',
                      'R1 powered boat and visual shore/surface acceptance are separate gates.'])
(E/'scalar-temporal-runtime-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(status=result['status'],checks=result['checks'],negative=negative,
                     failed_controls=result['series']['control_gate']['failures'],shallow_gate=result['series']['gate']),indent=2))
assert result['status']=='PASS_SCALAR_TEMPORAL_CONTROLS'
