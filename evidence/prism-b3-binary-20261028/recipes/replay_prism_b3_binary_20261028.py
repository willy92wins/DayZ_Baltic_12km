from pathlib import Path
import copy,hashlib,json,subprocess,time
R=Path(__file__).resolve().parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'prism-b3-binary-replay-20261028'
PY='C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
oldpath=R/'prism-b3-binary-pair-20261028/contract.json'
assert sha(oldpath)=='45d6bd48e4a03a12cb3adb1c62f6c35ff8fbe81e515281c3f498cc6410d84e56'
assert oldpath.read_bytes()==(O/'contract-before.json').read_bytes()
c=json.loads(oldpath.read_bytes());new=copy.deepcopy(c)
changed=[W/'tools/quality'/n for n in ('prism_b3_binary_ev112.py','test_prism_b3_binary_ev112.py')]
assert (O/'failed-prism_b3_binary_ev112.py').read_bytes().replace(b"read_pbo(c['baseline_pbo'])",b"read_pbo(Path(c['baseline_pbo']))")==changed[0].read_bytes()
for p in changed:
    assert sha(O/('failed-'+p.name))==c['pins'][str(p)]
    new['pins'][str(p)]=sha(p)
assert {p for p in c['pins'] if c['pins'][p]!=new['pins'][p]}=={str(p) for p in changed}
assert {k:v for k,v in c.items() if k!='pins'}=={k:v for k,v in new.items() if k!='pins'}
expected={
 'control/saved-odol.p3d':'0fccfce81ebcdd6b69b32989744ffe7b838b855c67c7dd3e71a0c266606a5525',
 'candidate/saved-odol.p3d':'b2c8bd4b45b56d139e0f97e14220aef6ed31e965eddc6fdbc040990f05eb5d62',
 'control/packed/baltic_stream_pilot.pbo':'cf2f7a48174a213938531d42cee43d100ab1fc53306f4ea9069a57184475bb47',
 'candidate/packed/baltic_stream_pilot.pbo':'b8cfdd52c16a82a77136468030a89de3290fd6197d1b9f25c0d1f2b364c14913'}
for rel,h in expected.items():
    p=R/'prism-b3-binary-pair-20261028'/rel;assert sha(p)==h;new['pins'][str(p)]=h
for p in (oldpath,O/'contract-before.json',O/'failure-before.json',O/'failed-prism_b3_binary_ev112.py',O/'failed-test_prism_b3_binary_ev112.py',Path(__file__),W/'plans/ev112-prism-b3-binary-replay-20261028.md',R/'prism-b3-binary-replay-review-20261028/review.md',R/'prism-b3-binary-replay-review-20261028/completion.json'):
    new['pins'][str(p)]=sha(p)
contract=O/'contract-r1.json';assert not contract.exists();dump(contract,new)
for p,h in new['pins'].items():assert sha(p)==h,p
t=time.monotonic();cp=subprocess.run([PY,'-I',str(changed[1]),'-v'],capture_output=True,timeout=120,cwd=W)
(O/'tests.stdout.log').write_bytes(cp.stdout);(O/'tests.stderr.log').write_bytes(cp.stderr)
assert cp.returncode==0 and b'Ran 34 tests' in cp.stderr and b'OK' in cp.stderr
dump(O/'tests.json',dict(tests=34,returncode=cp.returncode,seconds=time.monotonic()-t))
t=time.monotonic();out=R/'prism-b3-binary-consumer-r1-20261028'
cp=subprocess.run([PY,'-I',str(changed[0]),str(R),str(contract),str(R/'prism-b3-binary-pair-20261028'),'C:/temp/moto_lanes/review_g3/tools',str(out)],capture_output=True,timeout=195,cwd=W,creationflags=0x08000000)
(O/'consumer.stdout.log').write_bytes(cp.stdout);(O/'consumer.stderr.log').write_bytes(cp.stderr)
result=dict(returncode=cp.returncode,seconds=time.monotonic()-t,inputs_unchanged=all(sha(p)==h for p,h in new['pins'].items()),contract_sha256=sha(contract),no_recompile=True,no_package=True,no_dayz=True)
dump(O/'completion.json',result);print(json.dumps(result))
