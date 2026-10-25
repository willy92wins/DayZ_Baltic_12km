from pathlib import Path
import json, numpy as np
P=Path(r'E:/DayZ-Baltic-Build/v30-remaining-exact-dry-support-20261009')
R=Path(r'E:/DayZ-Baltic-Build/v30-bank-relief-review-20261010/luna-geometry')
r=json.loads((R/'report.json').read_text())
m=dict(np.load(P/'constraints.npz'));prior=dict(np.load(Path(r'E:/DayZ-Baltic-Build/v30-native-hinge-finish-20261009/constraints.npz')))
t=dict(np.load(P/'candidate/terrain.npz'))
for a in r['representative_maxima']:
  coords={'diagonal':[(a['row'],a['col']),(a['row'],a['col']+1),(a['row']+1,a['col']),(a['row']+1,a['col']+1)],'vertical':[(a['row'],a['col']),(a['row'],a['col']+1),(a['row']+1,a['col']+1),(a['row']+1,a['col']+2)],'horizontal':[(a['row'],a['col']),(a['row']+1,a['col']),(a['row']+1,a['col']+1),(a['row']+2,a['col']+1)]}[a['kind']]
  flags=[]
  for y,x in coords:
    flags.append({k:bool(m[k][y,x]) for k in ['fixed','other_fixed','water_support','large_lake_banks','released_dry'] if k in m}|{'prior_fixed':bool(prior['fixed'][y,x]),'prior_lake':bool(prior['large_lake_banks'][y,x]),'cls':int(t['cls'][y,x]),'reserve':bool(t['reserve'][y,x]),'platform':bool(t['platform'][y,x])})
  a['protection_reasons_by_vertex']=flags
  a['fixed_reason_summary']={k:sum(int(f.get(k,False)) for f in flags) for k in ['other_fixed','water_support','large_lake_banks','prior_fixed','prior_lake','released_dry']}
  print(a['rank'],a['x_m'],a['z_m'],json.dumps(a['fixed_reason_summary']),json.dumps(flags))
(R/'report.json').write_text(json.dumps(r,indent=2)+'\n')
