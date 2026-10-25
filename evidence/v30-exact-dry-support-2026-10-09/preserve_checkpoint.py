from pathlib import Path
import json,shutil,hashlib,csv
import numpy as np
B=Path(__file__).parent;R=B.parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=R/'v30-strict-dry-composition-20261009/candidate/terrain.npz';a=dict(np.load(source));d=np.load(B/'terrain-delta.npz')
assert np.array_equal(a['heights'][d['row'],d['col']],d['before'])
a['heights'][d['row'],d['col']]=d['after'];out=B/'layer-replay';out.mkdir(exist_ok=False);np.savez_compressed(out/'terrain.npz',**a)
assert sha(out/'terrain.npz')==sha(B/'candidate/terrain.npz')
(B/'layer-replay.json').write_text(json.dumps(dict(status='PASS_BYTE_EXACT_TERRAIN_REPLAY',source_sha256=sha(source),candidate_sha256=sha(out/'terrain.npz'),layer_sha256=sha(B/'terrain-delta.npz'),changed_vertices=len(d['row'])),indent=2)+'\n')
scope=np.load(R/'v30-low-dry-domain-classification-20261009/domain.npz');prior=np.load(R/'v30-native-hinge-finish-20261009/constraints.npz');mask=scope['editable']&(a['heights']<1.79999)
with (B/'remaining-strict-dry.csv').open('w',newline='') as f:
    writer=csv.writer(f);writer.writerow(['row','col','x','z','height','legacy_water_box','earlier_fixed','actual_wet_face'])
    for rr,cc in zip(*np.nonzero(mask)):writer.writerow([int(rr),int(cc),int(cc*6),int(12282-rr*6),float(a['heights'][rr,cc]),bool(prior['water_support'][rr,cc]),bool(scope['fixed'][rr,cc]),bool(scope['wet_face_support'][rr,cc])])
(B/'remaining-strict-dry.json').write_text(json.dumps(dict(status='REMAINING_PREVIOUS_EV59_EDITABLE_SCOPE',vertices=int(mask.sum()),candidate_sha256=sha(B/'candidate/terrain.npz'),limits=['This is the remaining EV59 strictly dry eligible set, not all low shoreline/protected terrain.','EV70 has no in-game validation yet.']),indent=2)+'\n')
manifest_path=W/'evidence/v30-volkhov-float-consistent-2026-10-09/evidence-manifest.json';manifest=json.loads(manifest_path.read_text())
dest=W/'evidence/v30-exact-dry-support-2026-10-09';dest.mkdir(exist_ok=False)
sources=[p for p in B.iterdir() if p.is_file() and p.suffix in ['.py','.json','.md','.npz','.log','.ps1','.csv']]
sources += list((B/'risk-census').iterdir())
for src in sources:
    if not src.is_file():continue
    target=dest/src.relative_to(B);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,target);assert sha(src)==sha(target)
    manifest.append(dict(evidence=70,path=target.relative_to(W).as_posix(),sha256=sha(target),bytes=target.stat().st_size))
init=B/'missions/BalticExactDrySupportFullWaterV1.BalticTrial/init.c';target=dest/'probe-init.c';shutil.copyfile(init,target);manifest.append(dict(evidence=70,path=target.relative_to(W).as_posix(),sha256=sha(target),bytes=target.stat().st_size))
for name in ['README.md','check_exact_support.py','exact-support-discriminator.json']:
    src=R/'v30-dry-floor-boundary-feasibility-20261009'/name;target=W/'evidence/v30-dry-floor-boundary-feasibility-2026-10-09'/name;shutil.copyfile(src,target);rel=target.relative_to(W).as_posix();manifest=[v for v in manifest if v['path']!=rel];manifest.append(dict(evidence=69,path=rel,sha256=sha(target),bytes=target.stat().st_size))
manifest_path.write_text(json.dumps(manifest,indent=2)+'\n');assert all(sha(W/v['path'])==v['sha256'] for v in manifest)
print(json.dumps(dict(status='PRESERVED_EV70_NOT_RUNTIME_ACCEPTED',remaining_ev59_strict_dry_vertices=int(mask.sum()),manifest_files=len(manifest),manifest_bytes=sum(v['bytes'] for v in manifest)),indent=2))
