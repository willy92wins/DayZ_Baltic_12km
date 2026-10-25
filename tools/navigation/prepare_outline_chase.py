"""Derive the proven bounded AI fixture at the new summit; no world edits."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
source = ROOT/'missions/BalticNativeChaseV2.BalticTrial/init.c'
target = ROOT/'missions/BalticOutlineChaseV1.BalticTrial/init.c'
if target.exists():
    raise ValueError('Fresh fixture required')
text = source.read_text(encoding='utf-8')
for old, new in [('BalticNativeChaseV2', 'BalticOutlineChaseV1'),
                 ('baltic_native_chase_v2', 'baltic_outline_chase_v1'),
                 ('BALTIC_NATIVE_CHASE_V2', 'BALTIC_OUTLINE_CHASE_V1'),
                 ('2417.143', '5184.0'), ('6889.885', '7644.0'),
                 ('0.988364361', '1.0'), ('0.152104866', '0.0'),
                 ('98.748926', '90'), ('-81.251074', '-90'),
                 ('2300 0 6750', '5100 0 7644')]:
    if old not in text:
        raise ValueError('Source anchor absent: '+old)
    text = text.replace(old, new)
target.parent.mkdir(parents=True)
target.write_text(text, encoding='utf-8', newline='\n')
ref = json.loads((ROOT/'evidence/navigation/native-chase-reference-v2.json').read_text())
ref.update(status='FROZEN_BEFORE_RUNTIME', center_xz=[5184,7644], axis_xz=[1,0],
           parent_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
           mission_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
           height_sha256='3e2f6a9643ba4a8c58a86534c75de6033b7dbdf7a3de5d09a5ea46ff66680ac6',
           requirements=['Local stimulus control, then both summit traversals; no movement override.',
                         'Server health positive; actor within -0.2/+0.5m of native triangular terrain.',
                         'Same 4m lateral, 2m target drift, 1s sampling gap and 90s stage timeout.'],
           limits=['One summit, one infected and one client; not regional or multiplayer capacity.',
                   'Prior 26 geometric Y discrepancies remain a separate FAIL.'])
(ROOT/'evidence/regional-outline-v3/chase-reference.json').write_text(json.dumps(ref,indent=2)+'\n')
# Freeze a separate verifier rather than change the accepted Narva fixture.
v = (ROOT/'tools/navigation/verify_native_chase.py').read_text()
v = v.replace("[f'BALTIC_NATIVE_CHASE_V{v}', 'world=BalticTrial', 'event;t;stage;x;y;z;d;cross;health;mind;target_entity'] for v in (1, 2)",
              "['BALTIC_OUTLINE_CHASE_V1', 'world=BalticTrial', 'event;t;stage;x;y;z;d;cross;health;mind;target_entity']")
v = v.replace('2417.143','5184.0').replace('6889.885','7644.0').replace('.988364361','1.0').replace('.152104866','0.0')
v = v.replace('        road[np.abs(d) <= 37.5] = 9\n','')
v = v.replace("asc=ROOT/'tests/narva_navigation_v3/narva_navigation_v1.asc'\n    design=json.loads((asc.parent/'design.json').read_text())\n    if sha(asc) != design['candidate_sha256']:",
              "asc=ROOT/'tests/regional_outline_v3/baltic_regional_outline_v3.asc'\n    if sha(asc) != '3e2f6a9643ba4a8c58a86534c75de6033b7dbdf7a3de5d09a5ea46ff66680ac6':")
v = v.replace('PASS_NATIVE_AI_LOCAL_AND_BOTH_CROSSINGS','PASS_NATIVE_AI_LOCAL_AND_BOTH_SUMMIT_TRAVERSES')
v = v.replace('Only the tested Narva corridor; no regional route acceptance.','Only the tested summit corridor; no regional route acceptance.')
v = v.replace('Graph sample-height mismatch remains a separate failed geometric gate.','The 26 graph sample-height discrepancies remain a separate failed geometric gate.')
(ROOT/'tools/navigation/verify_outline_chase.py').write_text(v,encoding='utf-8',newline='\n')
print(json.dumps(dict(mission=str(target),reference=ref),indent=2))
