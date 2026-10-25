"""Repair Windows Path string normalization before any new seam source was authored."""
from pathlib import Path
import json,hashlib
B=Path(__file__).parent;old='E:/DayZ-Baltic-Build/v30-native-turn-optimizer-20261009'
receipt=json.loads((B/'consumer-reuse.json').read_text())
for name in ('author_exact_seams.py','verify_exact_seams.py'):
    path=B/name;text=path.read_text();find="B=Path('"+old+"')"
    assert text.count(find)==1
    path.write_text(text.replace(find,"B=Path('"+B.as_posix()+"')"))
    for row in receipt['copies']:
        if row.get('copy')==str(path):row['copy_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
receipt['path_correction']='The initial inherited author stopped before edits because Windows Path str did not match its forward-slash B constant. Use as_posix for Python and str for PowerShell. Parent models unchanged.'
(B/'consumer-reuse.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('Corrected two copied B constants; no parent edits')
