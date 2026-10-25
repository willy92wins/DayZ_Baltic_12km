from pathlib import Path
import sys,json,csv
import numpy as np
E=Path(__file__).parent;R=E.parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path[:0]=[str(W/'tools/terrain'),str(W/'tools/water')]
from wrp0wzd import read
from engine_water_model import ODOL
world=read(R/'v30-remaining-exact-dry-support-20261009/package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp')
clean=lambda o:{k:o[k] for k in ('id','name','matrix')}
bridges=[clean(o) for o in world['objects'] if 'bridge' in o['name'].lower()]
print('BRIDGES',json.dumps(bridges))
models=R/'v30-native-terminal-finish-20261009/package/water/temp/baltic_water_v30'
near=[clean(o) for o in world['objects'] if 'baltic_water' in o['name'] and abs(o['matrix'][9]-2417)<400 and abs(o['matrix'][11]-6890)<400]
for name in sorted(set(o['name'] for o in near))[:3]:
    od=ODOL.from_file(str(models/name.replace('\\','/').split('/')[-1]))
    print('MODEL',name,[(l.resolution,len(l.vertices),len(l.faces),getattr(l,'named_properties',None),getattr(l,'textures',None)) for l in od.lods])
    print('ATTR',list(vars(od)))
    print('LODATTR',list(vars(od.lods[0])))
(E/'bridge-water-inventory.json').write_text(json.dumps(dict(bridges=bridges,nearby_water=near),indent=2)+'\n')
a=list(csv.DictReader((R/'v30-strict-dry-composition-20261009/dryfloor-physical-anomalies.csv').open()))
b=list(csv.DictReader((E/'base-surface-physical-anomalies.csv').open()))
key=lambda x:(x['row'],x['col'])
added=[x for x in b if key(x) not in set(map(key,a))]
removed=[x for x in a if key(x) not in set(map(key,b))]
(E/'native-anomaly-delta.json').write_text(json.dumps(dict(before=len(a),after=len(b),added=added,removed=removed,limits=['EV61 server-only and EV72 server plus client; wave phase not identical']),indent=2)+'\n')
print('ANOMALY_DELTA',json.dumps(dict(added=added,removed=removed)))
