from pathlib import Path
import sys,json,datetime
p=Path('P:/DayZ_MCP_dev/_client/profiles/baltic_distance_probe_v1.phase')
value=sys.argv[1];assert value in ['0','1','2','3']
before=p.read_text() if p.exists() else None
assert before is None or before.startswith('EV31-20261009\n')
data='EV31-20261009\n'+value+'\n';p.write_text(data,encoding='ascii');assert p.read_text()==data
row=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),phase=int(value),before=before,after=data)
with (Path(__file__).parent/'phase-writes.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row)+'\n')
print(json.dumps(row))
