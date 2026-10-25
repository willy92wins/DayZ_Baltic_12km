from pathlib import Path
from datetime import datetime,timezone
import json,sys
phase,index=map(int,sys.argv[1:])
assert phase in (1,2) and index==4
p=Path('P:/DayZ_MCP_dev/_client/profiles/baltic_detail_probe_v1.phase')
before=p.read_text() if p.exists() else None
after=f'EV32-20261009\n{phase}\n{index}\n'
p.write_text(after);assert p.read_text()==after
row=dict(utc=datetime.now(timezone.utc).isoformat(),phase=phase,index=index,before=before,after=after)
with (Path(__file__).parent/'phase-writes.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
print(json.dumps(row))
