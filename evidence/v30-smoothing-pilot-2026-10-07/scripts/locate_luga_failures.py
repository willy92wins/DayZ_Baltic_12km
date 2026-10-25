from pathlib import Path
import json,sys,numpy as np
W=Path.cwd();sys.path[:0]=[str(W/'tools/water'),str(W/'tools/terrain')]
from audit_waterline_v30 import measure
B=Path('E:/DayZ-Baltic-Build/v30-smoothing-pilot-20261007')
z=np.load(B/'luga-waterline-stations.npz');p=z['points'];n=z['normal'];old=z['offset_12'];new=z['offset_18-vector'];keep=z['keep']
bad=np.flatnonzero(keep&np.isfinite(old)&~np.isfinite(new))
_,extended=measure(str(B/'luga-18-vector/terrain_inland.npz'),p[bad],n[bad],np.full(len(bad),'river'),np.arange(len(bad)),np.ones(len(bad),bool),search=16)
rows=[{'station_index':int(i),'x':float(p[i,0]),'z':float(p[i,1]),'baseline_offset_m':float(old[i]),'candidate_offset_with_16m_search':float(extended[j]) if np.isfinite(extended[j]) else None} for j,i in enumerate(bad)]
(B/'luga-new-missing.json').write_text(json.dumps({'gate_search_stays_m':8,'diagnostic_only_search_m':16,'new_missing':rows},indent=2)+'\n',encoding='utf-8')
print(json.dumps(rows))
