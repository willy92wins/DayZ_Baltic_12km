"""Narrow C retry close contract; unknown native exit codes remain inconclusive."""
from pathlib import Path
import datetime,hashlib
if not __debug__:raise RuntimeError('Assertions required')
def utc(x):return datetime.datetime.fromisoformat(x.replace('Z','+00:00'))
def validate_close(c):
 assert c['run_retired'] is True and c['graceful'] is True and c['exit_metrics_valid'] is True
 assert c['stop_method']=='orderly_close' and c['stop_required'] is False and c['reason'] is None
 assert c['roles']==[dict(role='server',termination_line=True,rpt_rotated=False)]
def validate_rpt(binding,host,path):
 data=Path(path).read_bytes()
 assert hashlib.sha256(data).hexdigest()==binding['sha256']
 assert binding['mission_match_in_header'] is True
 assert Path(binding['mission'])==Path(host['mission_path'])
 assert abs((utc(binding['process_creation_utc'])-utc(host['created_utc'])).total_seconds())<=.002
 assert utc(binding['source_creation_utc'])>=utc(host['created_utc'])-datetime.timedelta(seconds=1)
 head='\n'.join(data.decode('utf-8',errors='replace').splitlines()[:80]).casefold().replace('/','\\')
 assert str(Path(host['mission_path'])).casefold().replace('/','\\') in head
 assert data.count(b'--- Termination successfully completed ---')==1
def validate_generation_exit(observer,events,run_id):
 assert observer['status']=='EXIT_OBSERVED' and observer['error'] is None
 # 0 is conventional; -1 is measured with native orderly termination on this engine.
 # No open-ended crash-code blacklist: every other value is rejected.
 assert type(observer['exit_code']) is int and observer['exit_code'] in (0,-1)
 assert all(e['run_id']==run_id for e in events)
 intents=[e for e in events if e['event']=='CLOSE_INTENT'];assert len(intents)==1
 assert not any(e['event'] in ('SERVER_EXIT_OBSERVED','GENERATOR_CANCEL_INTENT') for e in events)
 assert 0<(utc(observer['observed_utc'])-utc(intents[0]['utc'])).total_seconds()<=30
 return observer['exit_code']
