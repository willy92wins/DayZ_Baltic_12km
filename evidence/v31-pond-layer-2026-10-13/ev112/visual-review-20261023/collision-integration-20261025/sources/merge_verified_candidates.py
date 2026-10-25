"""Compose disjoint height deltas and byte-exact previously compiled models."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys
import numpy as np
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
Q=Path('E:/DayZ-Baltic-Build/qc-council-20261024')
B=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018')
sys.path.insert(0,str(W/'tools/playtest'))
from attach_navmesh import read_pbo
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=B/'visual-pilot-20261024-p';new=R/'river-131-compact-a';out=R/'combined-pilot';out.mkdir(exist_ok=True);assert not any(out.iterdir())
base=Q/'road-merged-s3';free=R/'terrain-free-final-merged/terrain-buried.npz'
assert sha(base/'terrain-buried.npz')=='6a081028120778d3821574878d4b3845f419c411e661a97d1dc17f3440a4c8a1'
assert sha(free)=='82e0f1ca5fb102ec4109adac8095819f9b060730e5750c9593eb6e1a86461761'
assert sha(new/'packed/baltic_stream_pilot.pbo')=='b03dd92b0a1fc7845a06bca52c742dbb06ca00272fc86f2a9ff42e824599dc35'
assert sha(old/'packed/baltic_stream_pilot.pbo')=='b2c1799d7edb7adf2deb55f3f3b76e0c0c82f608bcf1673f47074da93c6eeea1'
assert json.loads((new/'contact-review-union.json').read_text())['status']=='SAVED_COLLISION_PASS'
A=np.load(base/'terrain-buried.npz');F=np.load(free);C=np.load(new/'terrain.npz')
df=F['heights']!=A['heights'];dc=C['heights']!=A['heights'];assert not (df&dc).any()
arrays={k:C[k].copy() for k in C.files}
assert set(F.files)==set(A.files)|{'v31_shape_repair'} and A.files==C.files
assert np.array_equal(F['v31_shape_repair'],df)
arrays['v31_shape_repair']=F['v31_shape_repair'].copy()
for k in A.files:
    if k!='heights':assert np.array_equal(F[k],A[k],equal_nan=True),k
    if k not in ('heights','v31_continuous_pilot'):assert np.array_equal(C[k],A[k],equal_nan=True),k
arrays['heights'][df]=F['heights'][df]
np.savez_compressed(out/'terrain.npz',**arrays)
for name in ('cover.npy','envelope.npy'):shutil.copy2(new/name,out/name)
merged_entries={};instances=[];sites=[];removed=[];parents=[]
source=out/'source/baltic_stream_pilot';source.mkdir(parents=True)
compiled=out/'temp/baltic_stream_pilot';compiled.mkdir(parents=True)
for parent in (old,new):
    rep=json.loads((parent/'author-report.json').read_text());review=json.loads((parent/'binary-review.json').read_text())
    pbo=parent/'packed/baltic_stream_pilot.pbo';assert review['status']=='BINARY_PASS' and sha(pbo)==review['pbo_sha256']
    _,props,entries=read_pbo(pbo);assert props['prefix']=='baltic_stream_pilot'
    for name,data in entries.items():
        assert Path(name).name==name and '/' not in name and '\\' not in name,name
        if name in merged_entries and name!='config.bin':assert merged_entries[name]==data,name
        merged_entries[name]=data
    for instance in rep['instances']:
        name=instance['model'].split('\\')[-1];path=parent/'source/baltic_stream_pilot'/name
        assert sha(path)==instance['sha256'] and not (source/name).exists()
        shutil.copy2(path,source/name)
    for site in rep['sites']:shutil.copy2(parent/(site['site']+'-surfaces.npz'),out/(site['site']+'-surfaces.npz'))
    instances+=rep['instances'];sites+=rep['sites'];removed+=rep['removed_sites']
    parents.append(dict(path=str(parent),author_sha256=sha(parent/'author-report.json'),pbo_sha256=sha(pbo)))
assert len(instances)==len({i['model'] for i in instances})==62
for name,data in merged_entries.items():(compiled/name).write_bytes(data)
# New config only adds the 27 declared classes; existing 35 models never had classes.
old_config=(old/'source/baltic_stream_pilot/config.cpp').read_text().strip()
new_config=(new/'source/baltic_stream_pilot/config.cpp').read_text().strip()
assert new_config.startswith(old_config+'\nclass CfgVehicles {')
for name in ('config.cpp','$PBOPREFIX$'):shutil.copy2(new/'source/baltic_stream_pilot'/name,source/name)
author=json.loads((new/'author-report.json').read_text());author.update(instances=instances,sites=sites,removed_sites=removed,terrain_sha256=sha(out/'terrain.npz'),composition=dict(parents=parents,free_terrain_sha256=sha(free),free_vertices=int(df.sum()),river_vertices=int(dc.sum()),overlap_vertices=0))
(out/'author-report.json').write_text(json.dumps(author,indent=2),encoding='utf-8')
packed=out/'packed';packed.mkdir()
bank='C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe'
cmd=[bank]
for k,v in props.items():cmd+=['-property',k+'='+v]
cmd+=['-dst',str(packed),str(compiled)]
with (out/'filebank.log').open('wb') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
_,finalprops,final=read_pbo(packed/'baltic_stream_pilot.pbo');assert final==merged_entries and all(finalprops.get(k)==v for k,v in props.items())
(out/'merge-report.json').write_text(json.dumps(dict(status='COMPOSED_BYTE_EXACT',parents=parents,models=62,old_models_preserved=35,new_models=27,terrain_sha256=sha(out/'terrain.npz'),pbo_sha256=sha(packed/'baltic_stream_pilot.pbo'),free_vertices=int(df.sum()),river_vertices=int(dc.sum()),overlap_vertices=0,limits=['Full merged terrain and binary consumers still required.']),indent=2))
merged=R/'combined-merged';merged.mkdir(exist_ok=False)
for name in ('cover.npy','envelope.npy'):shutil.copy2(out/name,merged/name)
cmd=[sys.executable,'-I',str(W/'tools/water/bury_edges_v31.py'),str(out/'terrain.npz'),str(base/'terrain-buried.npz'),str(merged/'cover.npy'),str(merged/'envelope.npy'),str(base/'bury-work/fp0/footprint-report.json'),str(merged/'terrain-buried.npz'),str(merged/'bury-work'),str(merged/'bury-report.json')]
with (merged/'bury.log').open('w',encoding='utf-8') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
bury=json.loads((merged/'bury-report.json').read_text());assert bury['changed_vs_input']==0 and not bury['final_new_exposed']
baseline=np.load(base/'bury-work/fp0/footprint.npz');final=np.load(merged/'bury-work/fp0/footprint.npz')
assert baseline.files==final.files and all(np.array_equal(baseline[k],final[k],equal_nan=True) for k in baseline.files)
(merged/'merge-verification.json').write_text(json.dumps(dict(status='WATER_FOOTPRINT_EXACT',bury_changes=0,arrays=final.files,terrain_sha256=sha(merged/'terrain-buried.npz'),source_sha256=sha(out/'terrain.npz')),indent=2))
print('COMPOSED_BYTE_EXACT; WATER_FOOTPRINT_EXACT',flush=True)
