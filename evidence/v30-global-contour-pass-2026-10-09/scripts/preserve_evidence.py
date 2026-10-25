"""Preserve this functional unit without copying generated multi-gigabyte build trees."""
from pathlib import Path
import ast,gzip,json,shutil,zipfile
import numpy as np
import sys
B=Path(__file__).parent;B13=Path('E:/DayZ-Baltic-Build/v30-native-turn-optimizer-20261009')
sys.path.insert(0,str(B13));from discover_native_turns import W,sha
E=W/'evidence/v30-global-contour-pass-2026-10-09';scripts=E/'scripts';scripts.mkdir(exist_ok=True)
files=[]
for path in sorted(B.glob('*.py'))+sorted(B.glob('*.ps1')):
    if path.suffix=='.py':ast.parse(path.read_text())
    target=scripts/path.name;shutil.copyfile(path,target);assert sha(path)==sha(target);files.append(str(target.relative_to(E)))
for path in sorted(B.glob('*.json'))+sorted(B.glob('*.png')):
    target=E/path.name;shutil.copyfile(path,target);assert sha(path)==sha(target);files.append(path.name)
for name in ('tiles.jsonl',):
    raw=(B/name).read_bytes();target=E/(name+'.gz');target.write_bytes(gzip.compress(raw,mtime=0));assert gzip.decompress(target.read_bytes())==raw;files.append(target.name)
for name in ('package/world-addonbuilder.log','package/water/filebank.log','water-seams-addonbuilder.log'):
    path=B/name;target=E/path.name;shutil.copyfile(path,target);assert sha(path)==sha(target);files.append(target.name)
h=np.load(B13/'candidate-feasible/terrain.npz')['heights'];v=np.load(B/'candidate-repaired/terrain.npz')['heights'];rr,cc=np.nonzero(h!=v)
np.savez_compressed(E/'terrain-delta.npz',row=rr,col=cc,before=h[rr,cc],after=v[rr,cc]);files.append('terrain-delta.npz')
with zipfile.ZipFile(E/'new-seam-source.zip','w',compression=zipfile.ZIP_DEFLATED) as archive:
    for path in sorted((B/'compile-seams/source/baltic_water_v30').iterdir()):
        assert path.is_file();archive.write(path,'baltic_water_v30/'+path.name)
files.append('new-seam-source.zip')
result=dict(status='PRESERVED_PARTIAL_BASE_WORK',external_build=str(B),sparse_vertices=len(rr),
            source_sha256=sha(B13/'candidate-feasible/terrain.npz'),terrain_sha256=sha(B/'candidate-repaired/terrain.npz'),
            files={name:sha(E/name) for name in files},
            limits=['Native results and references are saved directly in this folder.','No TB/navmesh or global visual acceptance is inferred.'])
(E/'preservation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(files=len(files),vertices=len(rr))))
