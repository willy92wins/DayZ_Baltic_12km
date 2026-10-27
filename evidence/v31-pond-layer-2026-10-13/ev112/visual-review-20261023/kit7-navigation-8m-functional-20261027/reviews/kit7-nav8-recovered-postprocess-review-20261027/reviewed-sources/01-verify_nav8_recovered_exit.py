"""One documented unexecuted cancel intent; original exit contract stays intact."""
from pathlib import Path
import json,re
from verify_c_orderly_close import validate_generation_exit as original_exit,utc
RUN='0db37e43-0bd0-4ac6-8b03-bc85daf9d5b2'
INTENT='2026-10-27T02:34:29.4373005+00:00'
GENERATOR=71040
SERVER=46288
FIELDS=('run_id','pid','created_utc','executable','executable_sha256','command_line_sha256','parent_pid','parent_created_utc','parent_command_line_sha256','parent_has_run_and_output')

def verify_recovery(observer,events,run_id,proof):
 assert __debug__ and run_id==RUN
 assert all(e['run_id']==RUN for e in events)
 cancelled=[e for e in events if e['event']=='GENERATOR_CANCEL_INTENT']
 assert len(cancelled)==1 and cancelled[0]['utc']==INTENT
 assert proof['cancel_file_exists'] is False and proof['wrapper_cancel_file_exists'] is False
 old=proof['original_completion'];oldclean=proof['original_cleanup']
 assert old['status']=='OWNED_RECOVERY_REQUIRED' and old['run_id']==RUN
 assert 'lease_expired' in old['error'] and 'lease_expired' in old['cleanup_error']
 assert oldclean['preserve_for_recovery'] is True and oldclean['own_run_present'] is True and oldclean['close'] is None
 before=proof['generator_before'];after=proof['generator_after']
 assert {k:before[k] for k in FIELDS}=={k:after[k] for k in FIELDS}
 assert before['run_id']==RUN and before['pid']==GENERATOR and before['parent_pid']==59940
 assert before['parent_has_run_and_output'] is True
 assert before['executable_sha256']=='66935ce864436892247cd520ea2205c179d661e6390478ec35a2c304aa2ecbb7'
 assert utc(before['observed_utc'])<utc(INTENT)<utc(after['observed_utc'])
 gen=proof['generation'];done=proof['completion']
 assert gen['run_id']==done['run_id']==RUN
 assert gen['status']=='GENERATED_FILE_PENDING_STRUCTURAL_AND_ENGINE_VALIDATION' and type(gen['returncode']) is int and gen['returncode']==0
 assert gen['inputs_unchanged'] is True and not gen['failure_reasons']
 assert utc(gen['started_utc'])<=utc(before['observed_utc'])<utc(after['observed_utc'])<=utc(gen['finished_utc'])
 assert done['status']=='GENERATION_STAGE_COMPLETE_PENDING_VALIDATION' and done['error'] is None and done['cleanup_error'] is None
 prior=[];later=[]
 for row in proof['progress']:
  stamp=utc(row['utc']);values=[int(m.group(1)) for line in row['progress'] if (m:=re.search(r'Generating:.*?(\d+)%',line))]
  assert all(0<=x<=100 for x in values)
  if stamp<utc(INTENT):prior.extend(values)
  elif utc(INTENT)<stamp<=utc(gen['finished_utc']):later.extend(values)
 assert prior and later and max(later)>max(prior)
 recovered=proof['mcp_recovered'];baseline=proof['mcp_before']
 assert recovered['run_id']==recovered['server_run_id']==baseline['run_id']==RUN
 assert recovered['server_binding']=='BOUND' and recovered['version_state']=='ok'
 assert len(recovered['processes'])==len(baseline['processes'])==1
 keys=('pid','creation_time_utc','executable_sha256','command_line_sha256','role','identity_scheme')
 assert {k:recovered['processes'][0][k] for k in keys}=={k:baseline['processes'][0][k] for k in keys}
 assert recovered['processes'][0]['pid']==SERVER and recovered['processes'][0]['role']=='server'
 assert all(c['state']=='not_started' for c in recovered['client_diagnostics'])
 # Exact classified event is excluded only in this derived view, never on disk.
 # All other original close, error, run and timing checks remain authoritative.
 return original_exit(observer,[e for e in events if e is not cancelled[0]],run_id)

def validate_generation_exit(observer,events,run_id):
 r=Path(__file__).parent;d=r/'nav-kit7-8m-preparation-20261027';g=r/'navmesh-kit7-8m-v9-20261027'
 read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
 proof=dict(cancel_file_exists=(d/'generator-cancel.json').exists(),wrapper_cancel_file_exists=(d/'generator-wrapper-after-cancel.json').exists(),
  original_completion=read(d/'completion-before-lease-recovery.json'),original_cleanup=read(d/'cleanup-before-lease-recovery.json'),
  generator_before=read(d/'generator-identity.json'),generator_after=read(d/'generator-after-unexecuted-cancel.json'),
  generation=read(g/'generation.json'),completion=read(d/'completion.json'),
  progress=[json.loads(x) for x in (d/'progress.jsonl').read_text(encoding='utf-8-sig').splitlines()],
  mcp_recovered=read(d/'mcp-recovered.json'),mcp_before=read(d/'mcp-before.json'))
 return verify_recovery(observer,events,run_id,proof)
