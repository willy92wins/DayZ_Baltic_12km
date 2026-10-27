from pathlib import Path
import hashlib,json,subprocess,sys
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
D=R/'kit7-onload-package-execution-20261027';D.mkdir(exist_ok=False)
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
review=json.loads((R/'kit7-onload-package-code-review-20261027/adjudication.json').read_text())
assert review['status']=='ACCEPTED_AFTER_REVIEW'
assert all(sha(p)==h for p,h in review['inputs'].items())
for name,count in [('test_nav8_onload_config_ev112.py',14),('test_nav8_onload_package_contract.py',12)]:
 p=subprocess.run([sys.executable,'-I',str(W/'tests'/name)],capture_output=True)
 (D/(name+'.stdout.log')).write_bytes(p.stdout);(D/(name+'.stderr.log')).write_bytes(p.stderr)
 assert p.returncode==0 and ('Ran '+str(count)+' tests').encode() in p.stderr and b'OK' in p.stderr
args=[sys.executable,'-I',str(W/'tools/navigation/package_nav8_onload_config_ev112.py'),'--baseline','P:/Mods/@DayZ_Baltic_EV112_Kit7Nav8/Addons/narva_trial.pbo','--expected-sha256','ac088ccbaff34ef7a5cbfe03b6e016fb6941895b9b253786f99b57578cf6d4ff','--wrp-sha256','0da63d3f258923e784a62bcb59bb1d7f2ab99866816f530bfe73cd4211b23254','--converter','C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/CfgConvert/CfgConvert.exe','--filebank','C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe','--output',str(R/'package-kit7-nav8-onload-20261027')]
inputs={**review['inputs'],str(Path(__file__)):sha(__file__)}
(D/'frozen.json').write_text(json.dumps(dict(status='REVIEWED_OFFLINE_BUILD',inputs=inputs,argv=args,review_sha256=sha(R/'kit7-onload-package-code-review-20261027/adjudication.json')),indent=2)+'\n')
with (D/'build.stdout.log').open('wb') as out,(D/'build.stderr.log').open('wb') as err:
 p=subprocess.run(args,cwd=W,stdout=out,stderr=err)
unchanged=all(sha(path)==h for path,h in inputs.items())
(D/'completion.json').write_text(json.dumps(dict(returncode=p.returncode,inputs_unchanged=unchanged,scope='OFFLINE_ONLY_NOT_DEPLOYED'),indent=2)+'\n')
print(json.dumps(dict(returncode=p.returncode,inputs_unchanged=unchanged)));assert unchanged;raise SystemExit(p.returncode)
