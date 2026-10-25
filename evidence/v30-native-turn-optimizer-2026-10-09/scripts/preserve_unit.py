"""Preserve the completed contour unit, identities and consumer evidence."""
from pathlib import Path
import ast,csv,gzip,hashlib,json,shutil,zipfile
import numpy as np
from discover_native_turns import B,B10,B12,W,sha

E=W/'evidence/v30-native-turn-optimizer-2026-10-09';scripts=E/'scripts';scripts.mkdir(exist_ok=True)
copied=[]
for path in sorted(B.glob('*.py'))+sorted(B.glob('*.ps1')):
    if path.suffix=='.py':ast.parse(path.read_text())
    target=scripts/path.name;shutil.copyfile(path,target);assert sha(path)==sha(target);copied.append(str(target.relative_to(E)))
names=['discovery.json','R1-graph.json','R2-graph.json','optimization.json','feasibility-repair.json',
       'candidate-native-verification.json','candidate-feasible-verification.json',
       'coverage-consumer.json','candidate-feasible-coverage.json','candidate-feasible-final-coverage.json',
       'seam-reuse.json','seam-authoring.json','seam-verification.json','stage.json','package-seams.json','deploy.json',
       'native-fullwater-lint.json','native-temporal-lint.json','native-anomaly-regression.json',
       'whole-map-contour-survey.json','candidate-feasible-contours.png','whole-map-contour-survey.png']
for name in names:
    source=B/name;assert source.is_file(),source;target=E/name;shutil.copyfile(source,target);assert sha(source)==sha(target);copied.append(name)
for name in ('whole-map-contour-chains.csv','whole-map-contour-angles.csv'):
    raw=(B/name).read_bytes();target=E/(name+'.gz');target.write_bytes(gzip.compress(raw,mtime=0));assert gzip.decompress(target.read_bytes())==raw;copied.append(target.name)
for name in ('package/world-addonbuilder.log','water-seams-addonbuilder.log','package/water/filebank.log'):
    source=B/name;target=E/Path(name).name;shutil.copyfile(source,target);assert sha(source)==sha(target);copied.append(target.name)
h=np.load(B10/'measured-bank-bed-r2/terrain.npz')['heights'];v=np.load(B/'candidate-feasible/terrain.npz')['heights'];rr,cc=np.nonzero(h!=v)
delta=E/'terrain-delta.npz';np.savez_compressed(delta,row=rr,col=cc,before=h[rr,cc],after=v[rr,cc]);copied.append(delta.name)
with (E/'terrain-delta.csv').open('w',newline='') as stream:
    writer=csv.writer(stream);writer.writerow(['row','col','x','z','before_m','after_m'])
    writer.writerows((int(r),int(c),int(c)*6,12282-int(r)*6,float(h[r,c]),float(v[r,c])) for r,c in zip(rr,cc))
copied.append('terrain-delta.csv')
with zipfile.ZipFile(E/'new-seam-source.zip','w',compression=zipfile.ZIP_DEFLATED) as archive:
    for path in sorted((B/'compile-seams/source/baltic_water_v30').iterdir()):
        assert path.is_file();archive.write(path,'baltic_water_v30/'+path.name)
copied.append('new-seam-source.zip')
report=dict(status='EVIDENCE_PRESERVED_NOT_GLOBAL_ACCEPTANCE',terrain_sha256=sha(B/'candidate-feasible/terrain.npz'),
            parent_terrain_sha256=sha(B10/'measured-bank-bed-r2/terrain.npz'),sparse_vertices=len(rr),
            external_build=str(B),files={name:sha(E/name) for name in copied},
            limits=['Runtime files and references are produced directly into this evidence folder.','Full terrain, compiled models, mission grids and WRP remain in E: with identities; no shared memory modified.'])
(E/'preservation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(status=report['status'],files=len(copied),sparse_vertices=len(rr)),indent=2))
