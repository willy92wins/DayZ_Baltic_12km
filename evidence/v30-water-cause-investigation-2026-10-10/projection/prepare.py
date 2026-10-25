from pathlib import Path
import sys,json,hashlib
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path(__file__).parent
sys.path.insert(0,str(W/'tools/playtest'))
from attach_navmesh import read_pbo
probes=list(Path('P:/Mods/@BalticProjectionProbeV1/Addons').glob('*.pbo'))
assert len(probes)==1
probe=probes[0]
_,_,entries=read_pbo(probe)
scripts={k:v for k,v in entries.items() if k.endswith('.c')}
for k,v in scripts.items():
    (B/Path(k).name).write_bytes(v)
    print(k);print(v.decode('utf-8'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
files=[probe,*Path('P:/Mods/@DayZ_Baltic_BaseSurfacePreviewV1/Addons').glob('*.pbo')]
(B/'inputs.json').write_text(json.dumps({str(p):sha(p) for p in files},indent=2)+'\n')
