from pathlib import Path
import hashlib,json,subprocess,sys
if not __debug__:raise RuntimeError('Assertions required')
R=Path(__file__).parent;B=R/'river-131-midpoint-b';O=R/'package-midpoint-b'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path.insert(0,str(W/'tools/playtest'));from attach_navmesh import read_pbo
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text())
baseline=Path('P:/Mods/@DayZ_Baltic_EV112_RectangleF/Addons/baltic_stream_pilot.pbo');candidate=B/'packed/baltic_stream_pilot.pbo'
assert sha(baseline)=='c0be9abc9d36ee19c636325b825dbf09880a9dc31b5dfb8432e0f91d0e1cfa87'
assert sha(candidate)=='46390aff4704c9bb1a075cb4e4cf2224143dd30713a4bccf49cf0103226a28c8'
proofs={B/'compiled-contact-review.json':'PACKED_COLLISION_AT_F_POSES_PASS',B/'existing-pose-parity.json':'COMPILED_POSES_EXACT',B/'f-pose-binding.json':'F_WRP_62_POSES_BOUND_B27_EXACT'}
for path,status in proofs.items():assert read(path)['status']==status
for path,h in read(B/'compiled-contact-review.json')['sources'].items():assert sha(path)==h,path
_,props,before=read_pbo(baseline);_,p2,replacements=read_pbo(candidate)
assert props['prefix']==p2['prefix']=='baltic_stream_pilot'
names={n for n in replacements if n.lower().endswith('.p3d')};assert len(names)==27 and all(n.startswith('cs_131p0_0_') for n in names)
assert len([n for n in before if n.lower().endswith('.p3d')])==62 and names<=set(before)
assert before['config.bin'].startswith(b'\0raP')
expected={**before,**{n:replacements[n] for n in names}}
assert all(before[n]!=expected[n] for n in names)
stage=O/'compiled/baltic_stream_pilot';dest=O/'Addons'
assert not (O/'verification.json').exists() and not (dest/'baltic_stream_pilot.pbo').exists()
if O.exists():
    # Previous attempt failed before FileBank launch (wrong executable path).
    # Resume only the exact already-written inputs, no unknown files.
    assert {str(p.relative_to(stage)).replace('\\','/') for p in stage.rglob('*') if p.is_file()}==set(expected)
    assert all((stage/n).read_bytes()==v for n,v in expected.items()) and not list(dest.iterdir())
else:stage.mkdir(parents=True);dest.mkdir()
for n,data in expected.items():
    path=stage/n;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
fb=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe');assert fb.is_file()
args=[str(fb),'-property','prefix='+props['prefix'],'-property','product=dayz ugc','-dst',str(dest),str(stage)]
p=subprocess.run(args,capture_output=True);(O/'filebank.log').write_bytes(p.stdout+p.stderr);assert p.returncode==0
packed=dest/'baltic_stream_pilot.pbo';_,p3,after=read_pbo(packed)
assert after==expected and p3==props,(props,p3)
receipt=dict(status='PASS_27_MODELS_REPLACED_ALL_OTHER_ENTRIES_EXACT',baseline_sha256=sha(baseline),replacement_pbo_sha256=sha(candidate),pbo_sha256=sha(packed),models=62,replaced_models=27,unchanged_models=35,unchanged_entries=len(before)-27,config_byte_exact=True,properties_exact=True,entries={n:hashlib.sha256(v).hexdigest() for n,v in after.items()},sources={str(p):sha(p) for p in [baseline,candidate,*proofs,Path(__file__)]},limits=['Offline isolated package; no deployment or native acceptance. New collision requires its own nav generation before AI acceptance.'])
(O/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k not in ('entries','sources')},indent=2))
