from pathlib import Path
import csv,json,sys
import numpy as np
from scipy import ndimage
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290');E=W/'evidence/v30-global-water-risk-2026-10-09'
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
sys.path.insert(0,str(W/'tools/terrain'))
from v30_common import cell_planes,vertex_plane_bounds
paths=[Path('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008/r3-transition-proposal/terrain_flat.npz'),Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008/candidate-c1r3p/terrain_valley.npz')]
a,t=[dict(np.load(p)) for p in paths];h=t['heights'];planes=cell_planes(a['cls'],a['level']);pmin,pmax=vertex_plane_bounds(planes)
rows=[]
for p in csv.DictReader((E/'native-physical-anomalies.csv').open()):
 r,c=int(p['row']),int(p['col']);kind=int(p['cls']);nominal=float(p['plane'])-float(p['ground']);depth=float(p['depth'])
 if kind>0:
  if nominal>.03 or depth>.02:reason='presence_flag_disagrees_with_positive_depth'
  elif np.isfinite(pmax[r,c]) and h[r,c]>pmax[r,c]:reason='source_water_class_above_frozen_plane'
  elif not np.isfinite(pmax[r,c]):reason='no_frozen_pond_plane_at_vertex'
  else:reason='runtime_water_missing_below_frozen_plane'
 else:
  if np.isfinite(pmax[r,c]) and h[r,c]<pmax[r,c]-.03:reason='source_dry_below_neighbor_pond_plane'
  elif float(p['ground'])<.85:reason='sea_shore_classification'
  else:reason='runtime_water_above_source_domain'
 rows.append(dict(p,reason=reason,source_level=float(t['level'][r,c]) if np.isfinite(t['level'][r,c]) else None,
   frozen_plane_min=float(pmin[r,c]) if np.isfinite(pmin[r,c]) else None,frozen_plane_max=float(pmax[r,c]) if np.isfinite(pmax[r,c]) else None,
   original_ground=float(a['heights'][r,c]),current_ground=float(h[r,c]),height_changed_since_flat=bool(h[r,c]!=a['heights'][r,c]),
   platform_neighbor=bool(t['platform'][max(0,r-1):r+2,max(0,c-1):c+2].any())))
counts={reason:sum(p['reason']==reason for p in rows) for reason in sorted(set(p['reason'] for p in rows))}
(E/'native-anomaly-classification.json').write_text(json.dumps(dict(status='CLASSIFIED_NOT_CLOSED',counts=counts,points=rows),indent=2)+'\n')
print(json.dumps(dict(counts=counts,wet_without_positive_depth=[p for p in rows if int(p['cls'])>0 and p['reason']!='presence_flag_disagrees_with_positive_depth']),indent=2))
