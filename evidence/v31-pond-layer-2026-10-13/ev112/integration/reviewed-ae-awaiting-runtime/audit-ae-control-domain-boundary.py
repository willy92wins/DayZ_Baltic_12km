"""Measure the exact records outside the declared half-open world control domain.

Read-only audit; no source, gate, band, control result or production record changes.
The main final map gates still use the entire records file.
"""
from pathlib import Path
import hashlib,json
import numpy as np
O=Path(__file__).parent;R=O/'forest-map-51ae';out=O/'forest-ae-control-domain-boundary.json';assert not out.exists()
read=lambda p:json.loads(Path(p).read_text())
report=read(R/'report.json');binding=read(O/'forest-final-negatives-ae/domain-binding.json')
a=np.load(R/'instances.npy',mmap_mode='r');assert len(a)==report['n_records']
bad=np.flatnonzero((a['tx']<0)|(a['tx']>=12288)|(a['tz']<0)|(a['tz']>=12288))
assert len(a)-len(bad)==binding['pools']['distribution']['records']
want=set(map(int,bad));found=[];h=hashlib.sha256();index=0
with (R/'records.json').open('rb') as f:
 for line in f:
  h.update(line)
  if line.lstrip().startswith(b'{'):
   if index in want:
    rec=json.loads(line.rstrip().rstrip(b','));m=rec['matrix']
    assert m[9]==float(a['tx'][index]) and m[11]==float(a['tz'][index])
    found.append(dict(index=index,model=rec['model'],family=int(a['fam'][index]),placement_xz=[float(a['x'][index]),float(a['z'][index])],wrp_xz=[m[9],m[11]]))
   index+=1
assert index==len(a) and h.hexdigest()==report['records_sha256'] and len(found)==len(bad)
positions=np.array([v['wrp_xz'] for v in found]);placement=np.array([v['placement_xz'] for v in found])
result=dict(scope=__doc__,status='MEASURED_NOT_A_NEW_ACCEPTANCE_RULE',records_sha256=h.hexdigest(),
 total_records=len(a),inside_world_control_domain=binding['pools']['distribution']['records'],excluded_records=len(found),
 domain=[0,0,12288,12288],interval='lower-inclusive, upper-exclusive; WRP translation, as recio.load_records bbox',
 excluded_by_family={str(k):sum(v['family']==k for v in found) for k in sorted({v['family'] for v in found})},
 excluded_wrp_min_xz=positions.min(0).tolist(),excluded_wrp_max_xz=positions.max(0).tolist(),
 excluded_placement_inside_world=int(((placement>=0)&(placement<12288)).all(1).sum()),
 excluded=found,main_final_gate_coverage='The main map/painted gates receive the full2,561,015-record file and retain their original spatial filters. The independent compiled WRP readback verifies all forest objects. Only the paired distribution-control pool prefilters that file through the declared world bbox.',
 limits='The paired distribution controls do not cover mutations confined to these out-of-world translations; no claim of every isolated local defect detection. No change to acceptance bands or original failed regional evidence.',
 tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='excluded'}))
