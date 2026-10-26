"""Keep the original NPZ container after proving bury wrote identical NPY payloads."""
from pathlib import Path
import json,hashlib,shutil,zipfile
import numpy as np
R=Path(__file__).parent;K=R/'river-kit7-midpoint-a-20261026';A=R/'river-kit7-merged-20261026';O=R/'river-kit7-merged-byteexact-20261026'
read=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
d=read(A/'container-diagnostic.json');v=read(A/'merge-verification.json');buried=read(A/'bury-report.json')
assert d['all_npy_byte_exact'] and d['all_arrays_exact'] and d['source_sha256']==sha(K/'terrain.npz')=='815ef8b772bfa10e9d6886d953878c24ef6819c5667ce4700c91faab992aec40'
assert d['saved_sha256']==sha(A/'terrain-buried.npz') and all(x for k,x in v['checks'].items() if k!='terrain_byte_exact')
assert buried['changed_vs_input']==0 and not buried['final_new_exposed']
assert all(sha(p)==h for p,h in read(A/'inputs.json').items())
with zipfile.ZipFile(K/'terrain.npz') as a,zipfile.ZipFile(A/'terrain-buried.npz') as b:
 assert a.namelist()==b.namelist() and all(a.read(n)==b.read(n) for n in a.namelist())
assert Path(v['last_footprint'])==A/'bury-work/fp0/footprint.npz' and sha(Path(v['last_footprint']))==v['footprint_sha256']
(O/'bury-work/fp0').mkdir(parents=True,exist_ok=False)
shutil.copyfile(K/'terrain.npz',O/'terrain-buried.npz')
for name in ['cover.npy','envelope.npy','bury-report.json']:shutil.copyfile(A/name,O/name)
for name in ['footprint.npz','footprint-report.json']:shutil.copyfile(A/'bury-work/fp0'/name,O/'bury-work/fp0'/name)
assert sha(O/'terrain-buried.npz')==sha(K/'terrain.npz')
assert sha(O/'bury-work/fp0/footprint.npz')==v['footprint_sha256']
checks={**v['checks'],'terrain_byte_exact':True}
result=dict(status='POND_GEOMETRY_EXACT_KIT7_PENDING_INTEGRATION',checks=checks,last_footprint=str(O/'bury-work/fp0/footprint.npz'),footprint_sha256=v['footprint_sha256'],terrain_sha256=sha(O/'terrain-buried.npz'),inputs={str(p):sha(p) for p in [Path(__file__),A/'container-diagnostic.json',A/'merge-verification.json',A/'inputs.json',K/'terrain.npz',O/'cover.npy',O/'envelope.npy',O/'bury-work/fp0/footprint-report.json']},correction='bury used np.savez (ZIP_STORED) while candidate used compressed NPZ. Every NPY payload was byteexact. Preserve original compressed bytes after proving no actual terrain mutation; original failed output/report retained.',limits=['Pond geometry fields exact toF; no new terrain edits. Kit7WRP,forest,native/navigation/visual acceptance remain separate.'])
(O/'merge-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
