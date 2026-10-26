from pathlib import Path
from collections import deque,Counter
import json,hashlib,re,datetime
R=Path(__file__).parent;D=R/'nav-c-data-preparation-v2-20261026';O=R/'c-nav-exit-diagnostic-20261026';O.mkdir(exist_ok=False)
sha=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
pat=re.compile(r'error|exception|memory|terminat|destroy|exit|shutdown|restart|timeout|fatal',re.I)
tail=deque(maxlen=60);end=[];counts=Counter();lines=0;pond=0
with (D/'server.RPT').open(encoding='utf-8',errors='replace') as f:
 for n,line in enumerate(f,1):
  lines=n
  if "Unknown object class 'pond'" in line:pond+=1;continue
  if pat.search(line) and not any(s in line for s in ('Creating empty','Duplicate string')):
   row=dict(line=n,text=line.strip());tail.append(row)
   for key in ('exception','fatal','out of memory','Destroying game','Termination successfully','shutdown','restart','timeout'):
    if key.lower() in line.lower():counts[key]+=1
  if line.startswith('12:58:'):end.append(dict(line=n,text=line.strip()))
audit=Path('C:/Users/guill/AppData/Local/DayZ_MCP_130/audit/events.jsonl')
events=[]
for line in audit.read_text(encoding='utf-8-sig').splitlines():
 x=json.loads(line);stamp=x.get('timestamp_utc','')
 if '2026-10-26T11:57:00'<=stamp<'2026-10-26T11:59:00':
  events.append({k:x.get(k) for k in ('timestamp_utc','event','reason','decision','run_id')})
samples=[json.loads(x) for x in (D/'observer/samples.jsonl').read_text().splitlines()]
observer=json.loads((D/'observer/terminal.json').read_text())
inputs=json.loads((D/'launch-inputs.json').read_text())['inputs']
unchanged=all(sha(p)==h for p,h in inputs.items())
report=dict(status='GENERATION_FAILED_CAUSE_UNRESOLVED',run_id='a2619a56-4b44-49f1-bb6f-da2a16da3f86',rpt_sha256=sha(D/'server.RPT'),lines=lines,pond_warnings=pond,counts=dict(counts),last_matching_lines=list(tail),terminal_minute=end[-80:],observer=observer,samples=len(samples),max_working_set_bytes=max(x['working_set_bytes'] for x in samples),max_private_bytes=max(x['private_bytes'] for x in samples),final_sample=samples[-1],frozen_inputs_unchanged=unchanged,redacted_audit=events,limits=['Exit-1 and orderly RPT shutdown precede our close intent. They do not identify who requested exit.','No exception/fatal/OOM line is not proof of no engine fault.','Pond warnings also exist in prior successful E generation; not isolated as cause.','One C generation attempt exhausted. No automatic retry, no NM or C45 acceptance.'])
(O/'diagnostic.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('last_matching_lines','terminal_minute','final_sample')},indent=2))

