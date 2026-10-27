"""Validate persisted generation deadlines independently of the JS coordinator."""
from datetime import datetime,timedelta,timezone

def utc(value):
    result=datetime.fromisoformat(value.replace('Z','+00:00'))
    if result.tzinfo is None:
        raise ValueError('Timezone required')
    return result.astimezone(timezone.utc)

def validate_budget(budget,generation):
    keys={'run_id','started_utc','generation_seconds','generation_deadline_utc','coordinator_seconds','deadline_utc'}
    if set(budget)!=keys or budget['run_id']!=generation['run_id'] or budget['started_utc']!=generation['started_utc']:
        raise ValueError('Budget identity/start/schema mismatch')
    if type(budget['generation_seconds']) is not int or type(budget['coordinator_seconds']) is not int or budget['generation_seconds']!=18000 or budget['coordinator_seconds']!=18300:
        raise ValueError('Budget duration changed')
    start=utc(generation['started_utc'])
    # JavaScript Date preserves milliseconds, while Python records microseconds.
    js_start=start.replace(microsecond=(start.microsecond//1000)*1000)
    if utc(budget['generation_deadline_utc'])!=js_start+timedelta(seconds=18000) or utc(budget['deadline_utc'])!=js_start+timedelta(seconds=18300):
        raise ValueError('Persisted deadline changed')
    finish=utc(generation['finished_utc'])
    if finish<start or finish>utc(budget['deadline_utc']):
        raise ValueError('Generation receipt outside coordinator budget')
    return {'status':'PASS_PERSISTED_GENERATION_BUDGET','run_id':generation['run_id'],'started_utc':generation['started_utc'],'generation_seconds':18000,'coordinator_seconds':18300}
