"""Preserve current diagnostics without overwriting accepted candidate or earlier evidence."""
from pathlib import Path
import hashlib,json,shutil
import numpy as np
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009');E=W/'evidence/v30-global-water-risk-2026-10-09'
B11=Path('E:/DayZ-Baltic-Build/v30-river-end-tapers-20261009');E11=W/'evidence/v30-river-end-tapers-2026-10-09'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]


def preserve(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists():assert src.read_bytes()==dst.read_bytes(),str(dst)
    else:shutil.copy2(src,dst)
    assert sha(src)==sha(dst)
    rows.append(dict(source=str(src),copy=str(dst.relative_to(W)),sha256=sha(src)))


ref=B/'shore-material-probe-r2/reference.json';r=json.loads(ref.read_text())
r['reason']='R1 used Terrain shaders in the shore slot and the client crashed. Contract mismatch is a hypothesis; R2 preserves native Shore/ShoreWet shaders and has not run.'
ref.write_text(json.dumps(r,indent=2)+'\n')
for name in ['water-connections.json','water-connection-edges.json','water-connection-fields.npz','connected-visual-field.json']:
    preserve(B/name,E/name)
for name in ['prepare_shore_marker_r2.py','audit_water_connections.py','derive_connected_visual_field.py','preserve_diagnostic_checkpoint.py']:
    preserve(B/name,E/'scripts'/name)
for directory in ['shore-material-baseline','shore-material-marker']:
    for file in (B/directory).glob('*'):
        if file.is_file():preserve(file,E/'frames'/directory/file.name)
for file in (B/'shore-material-probe-r2').rglob('*'):
    if file.is_file() and file.suffix not in ('.bin','.pbo'):
        preserve(file,E/'shore-material-probe-r2-source'/file.relative_to(B/'shore-material-probe-r2'))
for file in B11.glob('*.py'):preserve(file,E11/'scripts'/file.name)
for file in B11.glob('*.json'):preserve(file,E11/file.name)
for file in B11.glob('*.png'):preserve(file,E11/file.name)
base=np.load(B/'measured-bank-bed-r2/terrain.npz')['heights']
for label in ['candidate-msta','candidate-msta-r2']:
    for file in (B11/label).glob('*.json'):preserve(file,E11/label/file.name)
    q=np.load(B11/label/'terrain.npz')['heights'];rr,cc=np.nonzero(q!=base)
    delta=[dict(row=int(r),col=int(c),x=int(c*6),z=int(12282-r*6),before=float(base[r,c]),after=float(q[r,c])) for r,c in zip(rr,cc)]
    (E11/label/'exact-height-delta.json').write_text(json.dumps(dict(terrain_sha256=sha(B11/label/'terrain.npz'),changes=delta),indent=2)+'\n')
(E/'diagnostic-checkpoint-files.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(dict(preserved=len(rows),bytes=sum((W/r['copy']).stat().st_size for r in rows))))
