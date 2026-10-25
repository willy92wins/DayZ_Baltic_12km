from pathlib import Path
import json
import numpy as np
from shapely.geometry import LineString,Point
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
R=Path(r'E:/DayZ-Baltic-Build/v30-bank-relief-review-20261010/luna-geometry')
roads=np.load(W/'tests/regional_foundation_roads_v6/reference.npz')['xy']
chains=json.loads((W/'evidence/regional-foundation-v1/road-grade-chains-v6.json').read_text())['chains']
lines=[LineString(roads[idx]) for idx in chains if len(idx)>=2]
N=(2417.1428225906,6889.8850822322)
p=json.loads((R/'report.json').read_text())
out=[]
for a in p['representative_maxima'][:4]:
 pt=Point(a['x_m'],a['z_m']);nearest=min((l.distance(pt),i) for i,l in enumerate(lines))
 out.append(dict(rank=a['rank'],x_m=a['x_m'],z_m=a['z_m'],narva_center_distance_m=pt.distance(Point(*N)),nearest_reference_road_line_m=float(nearest[0]),road_chain_index=int(nearest[1]),inside_existing_470m_narva_road_gate_exclusion=pt.distance(Point(*N))<=470))
(R/'road-proximity-anchors.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
