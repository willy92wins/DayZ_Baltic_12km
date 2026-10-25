from pathlib import Path
import json,numpy as np
R=Path(r'E:/DayZ-Baltic-Build/v30-bank-relief-review-20261010/luna-geometry'); base=Path(r'E:/DayZ-Baltic-Build/v30-remaining-exact-dry-support-20261009');
r=json.loads((R/'report.json').read_text()); m=dict(np.load(base/'constraints.npz')); scope=dict(np.load(Path(r'E:/DayZ-Baltic-Build/v30-low-dry-domain-classification-20261009/domain.npz'))); prior=dict(np.load(Path(r'E:/DayZ-Baltic-Build/v30-native-hinge-finish-20261009/constraints.npz')))
for a in r['representative_maxima']:
 v={'diagonal':[(a['row'],a['col']),(a['row'],a['col']+1),(a['row']+1,a['col']),(a['row']+1,a['col']+1)],'vertical':[(a['row'],a['col']),(a['row'],a['col']+1),(a['row']+1,a['col']+1),(a['row']+1,a['col']+2)],'horizontal':[(a['row'],a['col']),(a['row']+1,a['col']),(a['row']+1,a['col']+1),(a['row']+2,a['col']+1)]}[a['kind']]
 a['scope_fixed_vertices']=sum(bool(scope['fixed'][y,x]) for y,x in v)
 a['old_water_support_vertices']=sum(bool(prior['water_support'][y,x]) for y,x in v)
 a['old_large_lake_vertices']=sum(bool(prior['large_lake_banks'][y,x]) for y,x in v)
 a['at_ev71_border11_vertices']=sum(y<11 or y>=2037 or x<11 or x>=2037 for y,x in v)
print([(a['rank'],a['x_m'],a['z_m'],a['scope_fixed_vertices'],a['old_water_support_vertices'],a['old_large_lake_vertices'],a['at_ev71_border11_vertices']) for a in r['representative_maxima']])
(R/'report.json').write_text(json.dumps(r,indent=2)+'\n')
