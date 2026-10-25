"""Archive the bounded A/B/A diagnostic and its explicit limits."""
from pathlib import Path
import hashlib, json, shutil
B=Path(__file__).parent
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-ocean-height-diagnostic-2026-10-09'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
lines=(E/'ocean-height-runtime.log').read_text().splitlines()
rows=[list(map(float,line.split(';')[1:])) for line in lines if line.startswith('SEA;')]
assert len(rows)==90 and lines[-1]=='END;90' and lines[1]=='CFG;0;0.1'
assert [int(row[0]) for row in rows]==list(range(90))
assert all(abs(row[2]-row[3])<1e-6 and abs(row[4]-.1)<1e-6 for row in rows)
frames={}
for path in sorted((B/'views').rglob('*.jpg')):
    target=E/'frames'/path.parent.name/path.name;target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(path,target);assert sha(path)==sha(target);frames[str(target.relative_to(E))]=sha(target)
for name in ('reference.json','lint.json','prepare_ocean_probe.py','preserve_comparison.py'):
    path=B/name;shutil.copyfile(path,E/name);assert sha(path)==sha(E/name)
source=E/'diagnostic-source';source.mkdir(exist_ok=True)
for path in (B/'baltic_ocean_height_probe_v1').rglob('*'):
    if path.is_file() and path.suffix!='.bin':
        target=source/path.relative_to(B/'baltic_ocean_height_probe_v1');target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
result=dict(status='SEA_LEVEL_DEPENDENCE_REPRODUCED_NOT_ROOT_CAUSE',native_config=dict(MaxTide=0,MaxWave=.1),native_samples=90,sea_range_m=[min(r[2] for r in rows),max(r[2] for r in rows)],
    comparison=dict(baseline='EV14/shore-baseline-wind20, normal map',diagnostic='bridge-wind20, MaxTide=0 only',restored='bridge-restored, normal map',positive_control='EDGE1 shoreline/foam changes and restores',terrain_and_ponds='Identical deployed PBO hashes in all runs'),frames=frames,
    observations=['Several distant glints/halos beside the bridge disappear with the lower sea and return in the restored normal map.', 'The visible ocean shoreline changes too, providing a positive response to the factor.', 'This repeats the earlier sea-separation dependence on the new GlobalContourV1 package; it does not identify the renderer mechanism.'],
    limits=['Wave phase is not synchronized. Per-frame pixel differences are not an extent/area audit.', 'No definitive shore material or terrain LOD causality.', 'No production sea-level/config change. All runs closed orderly and leases released.', 'Whole-map physical and compiled geometric checks remain EV14; these images cannot certify every dry surface.'])
(E/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='frames'},indent=2))
