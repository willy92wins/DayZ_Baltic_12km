"""Retarget only mission/log labels from frozen F-terrain queries to collision stack C."""
from pathlib import Path
import copy,hashlib,json
R=Path(__file__).parent;O=R/'patch-nav-c45'
M=Path('C:/temp/DayZ_MCP_130_dev/mpmissions/BalticPatchNavC45.BalticTrial')
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
h=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
frozen=read(R/'patch-nav-frozen.json')['F']
for p,d in frozen['inputs'].items():assert h(p)==d,p
before=read(frozen['reference']);old=Path(frozen['mission'])
assert before['side']=='F' and before['terrain_sha256']=='caa5398021399b6e435faf407005f053d58758091371b5b8fbd2e60e53f69cfc'
assert len(before['queries'])==45
code=(old/'init.c').read_bytes();csv=(old/'queries.csv').read_bytes()
a=b'baltic_patch_nav_f45.log';b=b'BALTIC_PATCH_NAV_F45;'
assert code.count(a)==code.count(b)==1
updated=code.replace(a,b'baltic_patch_nav_c45.log').replace(b,b'BALTIC_PATCH_NAV_C45;')
assert updated.replace(b'baltic_patch_nav_c45.log',a).replace(b'BALTIC_PATCH_NAV_C45;',b)==code
assert not O.exists() and not M.exists()
O.mkdir();M.mkdir()
(M/'init.c').write_bytes(updated);(M/'queries.csv').write_bytes(csv)
ref=copy.deepcopy(before)
ref.update(header='BALTIC_PATCH_NAV_C45;BalticTrial',mission=str(M),log_name='baltic_patch_nav_c45.log',code_sha256=h(M/'init.c'),collision_stack='C',source_f_reference_sha256=h(frozen['reference']))
# Full-record parity after undoing only the permitted metadata.
restored=copy.deepcopy(ref)
for k in ('header','mission','log_name','code_sha256'):restored[k]=before[k]
for k in ('collision_stack','source_f_reference_sha256'):del restored[k]
assert restored==before and h(M/'queries.csv')==ref['queries_sha256']
(O/'reference.json').write_text(json.dumps(ref,indent=2)+'\n',encoding='utf-8')
inputs=dict(frozen['inputs'])
for p in [M/'init.c',M/'queries.csv',O/'reference.json',Path(__file__),W/'tools/navigation/verify_continuity_nav_v30.py',W/'tools/navigation/verify_patch_nav_coverage_ev112.py']:
 inputs[str(p)]=h(p)
out=dict(status='FROZEN_C_STACK_F_TERRAIN_QUERIES',mission=str(M),reference=str(O/'reference.json'),inputs=inputs,queries_exact=True,csv_byte_exact=True,mission_only_two_label_replacements=True,terrain_side='F',collision_stack='C',limits=['Same45query records and expectations; zero claimed coverage of25Cpieces.'])
(O/'frozen.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k!='inputs'}))

