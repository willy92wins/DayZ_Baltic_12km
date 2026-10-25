from pathlib import Path
import hashlib,json,sys
import numpy as np
import rasterio
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290');E=W/'evidence/v30-current-physical-consumers-2026-10-09'
sys.path.insert(0,str(W/'tools/navigation'));from verify_regional_boat_consumer import verify
ref=json.loads((E/'boat-reference.json').read_text());base=(E/'boat-runtime.log').read_text().splitlines()
with rasterio.open(ref['terrain']) as ds:h=ds.read(1)
assert verify(ref,base,h)['status'].startswith('PASS_')
index=next(i for i,line in enumerate(base) if line.startswith('B;0;') and float(line.split(';')[2])>30)
def one(field,change):
 out=base.copy();row=out[index].split(';');row[field]=str(change(row[field]));out[index]=';'.join(row);return out
def all_case(field,value):
 out=[]
 for line in base:
  if line.startswith('B;0;'):
   row=line.split(';');row[field]=str(value);line=';'.join(row)
  out.append(line)
 return out
mutations={'missing_end':base[:-1],'wrong_ground':one(19,lambda x:float(x)+1),'damage':one(8,lambda x:float(x)-2),'sample_gap':one(2,lambda x:float(x)+2),'engine_off':all_case(9,'false'),'no_rpm':all_case(12,700),'no_propeller':all_case(13,0),'no_callbacks':all_case(14,0),'neutral_gear':all_case(10,1),'nan_speed':one(7,lambda x:'nan')}
teleport=base.copy();row=teleport[index].split(';');xyz=[float(x) for x in row[22][1:-1].split(',')];xyz[0]+=20;row[3]=format(xyz[0],'.6g');row[22]='<'+', '.join(f'{x:.6f}' for x in xyz)+'>';teleport[index]=';'.join(row);mutations['consistent_teleport']=teleport
outcomes=[]
for name,lines in mutations.items():
 report=verify(ref,lines,h);assert not report['status'].startswith('PASS_'),name
 outcomes.append(dict(name=name,status='EXPECTED_REJECTION'))
result=dict(status='PASS_REAL_RUN_NEGATIVE_CONTROLS',positive='Fresh EV16 six-case actual engine boat run',negative_cases=outcomes,log_sha256=hashlib.sha256((E/'boat-runtime.log').read_bytes()).hexdigest())
(E/'boat-negative-controls.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
