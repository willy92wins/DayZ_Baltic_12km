from pathlib import Path
import ast,gzip,hashlib,json,shutil
import numpy as np
B=Path(__file__).parent
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-native-terminal-finish-2026-10-09';(E/'scripts').mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[]
for p in sorted(B.glob('*.py'))+sorted(B.glob('*.ps1')):
 if p.suffix=='.py':ast.parse(p.read_text())
 target=E/'scripts'/p.name;shutil.copyfile(p,target);assert sha(p)==sha(target);files.append(str(target.relative_to(E)))
for p in sorted(B.glob('*.json'))+sorted(B.glob('*.png')):
 target=E/p.name;shutil.copyfile(p,target);assert sha(p)==sha(target);files.append(p.name)
raw=(B/'tiles.jsonl').read_bytes();target=E/'tiles.jsonl.gz';target.write_bytes(gzip.compress(raw,mtime=0));assert gzip.decompress(target.read_bytes())==raw;files.append(target.name)
source=Path('E:/DayZ-Baltic-Build/v30-global-contour-pass-20261009/candidate-repaired/terrain.npz')
h=np.load(source)['heights'];v=np.load(B/'candidate/terrain.npz')['heights'];rr,cc=np.nonzero(h!=v)
np.savez_compressed(E/'terrain-delta.npz',row=rr,col=cc,before=h[rr,cc],after=v[rr,cc]);files.append('terrain-delta.npz')
for name in ('river074-final','stream0131-final'):
 paths=list((B/'views'/name).glob('*.jpg'));assert len(paths)==1
 dest=E/'frames'/paths[0].name;dest.parent.mkdir(exist_ok=True);shutil.copyfile(paths[0],dest);assert sha(paths[0])==sha(dest);files.append(str(dest.relative_to(E)))
p=B/'package/world-addonbuilder.log';dest=E/p.name;shutil.copyfile(p,dest);files.append(dest.name)
result=dict(status='PRESERVED_EV16_PARTIAL_BASE',external_build=str(B),sparse_vertices=len(rr),source_sha256=sha(source),terrain_sha256=sha(B/'candidate/terrain.npz'),files={name:sha(E/name) for name in files},limits=['Msta and four other boxes unchanged.','No fresh temporal run; no final TB/navmesh/road/boat acceptance.'])
(E/'preservation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(files=len(files),vertices=len(rr))))
