import copy,importlib.util,json
from pathlib import Path
R=Path(__file__).parent
spec=importlib.util.spec_from_file_location('budget',R/'verify_nav12_generation_budget.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
gen={'run_id':'fixture-owned','started_utc':'2026-10-27T10:00:00.123456+00:00','finished_utc':'2026-10-27T14:59:59.999999+00:00'}
base={'run_id':'fixture-owned','started_utc':gen['started_utc'],'generation_seconds':18000,'generation_deadline_utc':'2026-10-27T15:00:00.123Z','coordinator_seconds':18300,'deadline_utc':'2026-10-27T15:05:00.123Z'}
assert mod.validate_budget(base,gen)['status']=='PASS_PERSISTED_GENERATION_BUDGET'
cases=[]
for name in ('wrong_run','wrong_start','new_deadline','new_native_deadline','long_native','long_coordinator','extra_key','missing_key','bool_duration','late_finish','early_finish','naive_time'):
    b=copy.deepcopy(base);g=copy.deepcopy(gen)
    if name=='wrong_run':b['run_id']='foreign'
    elif name=='wrong_start':b['started_utc']='2026-10-27T10:00:01+00:00'
    elif name=='new_deadline':b['deadline_utc']='2026-10-27T15:05:01.123Z'
    elif name=='new_native_deadline':b['generation_deadline_utc']='2026-10-27T15:00:01.123Z'
    elif name=='long_native':b['generation_seconds']=18001
    elif name=='long_coordinator':b['coordinator_seconds']=18301
    elif name=='extra_key':b['reset']=True
    elif name=='missing_key':del b['deadline_utc']
    elif name=='bool_duration':b['generation_seconds']=True
    elif name=='late_finish':g['finished_utc']='2026-10-27T15:05:00.124Z'
    elif name=='early_finish':g['finished_utc']='2026-10-27T09:59:59Z'
    elif name=='naive_time':g['finished_utc']='2026-10-27T11:00:00'
    try:mod.validate_budget(b,g)
    except (ValueError,KeyError):cases.append({'name':name,'rejected':True})
    else:raise AssertionError(name+' accepted')
out=R/'kit7-nav12-consumer-20261027/generation-budget-controls.json'
out.write_text(json.dumps({'status':'PASS_BUDGET_POSITIVE_AND_NEGATIVE_CONTROLS','positive':1,'negative':cases},indent=2)+'\n')
print('Budget fixture: 1 positive and 12 negative controls PASS')
