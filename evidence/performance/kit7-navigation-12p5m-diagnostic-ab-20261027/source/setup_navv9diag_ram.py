"""Prepare isolated diagnostic-only RAM controls; never launch DayZ."""
from pathlib import Path
import ast,hashlib,json,shutil,subprocess,sys
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ren(s):return s.replace('nav12','navv9diag').replace('Nav12','NavV9Diag').replace('NAV12','NAVV9DIAG')
source=(R/'prepare_nav12_ram_files.py').read_text()
mission_code=source[:source.index("for name in ('prepare_nav8_ram_pass.py'")]+source[source.index("validator=Path("):]
mission_code=ren(mission_code).replace('Requires own kit7 NavV9Diag native607 PASS before each launch; no borrowed measurements.','DIAGNOSTIC_ONLY: four original height failures preserved; never eligible for acceptance.')
target=R/'prepare_navv9diag_ram_files.py';assert not target.exists();target.write_text(mission_code)
subprocess.run([sys.executable,'-I',str(target)],check=True)
D=R/'kit7-navv9diag-ram-ab-20261027'
for name in ('prepare_nav12_ram_pass.py','finish_nav12_ram_pass.py','finalize_nav12_ram_ab.py','orchestrate_nav12_ram.js','test_nav12_ram_conditions.py','test_nav12_ram_flow.cjs','test_nav12_ram_command.cjs'):
    s=ren((R/name).read_text())
    if name=='prepare_nav12_ram_pass.py':
        start=s.index("native=R/'kit7-navv9diag-consumer-20261027'")
        end=s.index("manifest=read(D/'missions.json')",start)
        s=s[:start]+"native=R/'kit7-nav-consumer-20261026'\nsys.path.insert(0,str(R))\nfrom navv9diag_gate import validate_diagnostic\nvalidate_diagnostic(native/'result.json',D/'deployment.json')\ndep=read(D/'deployment.json')\n"+s[end:]
        s=s.replace("proofs=[native/'result.json',native/'identity-verification.json',native/'deployment.json'","proofs=[native/'result.json',D/'deployment.json',R/'navv9diag_gate.py'")
    if name in ('prepare_nav12_ram_pass.py','finish_nav12_ram_pass.py'):
        s=s.replace('BOUND_AFTER_NATIVE607','BOUND_DIAGNOSTIC_ONLY_HEIGHT_FAIL')
    if name in ('orchestrate_nav12_ram.js','test_nav12_ram_flow.cjs'):
        s=s.replace('@DayZ_Baltic_EV112_Kit7NavV9Diag','@DayZ_Baltic_EV112_Kit7NavV9')
    if name=='finalize_nav12_ram_ab.py':
        s=s.replace("result['measurement_repeats']=0", "result['measurement_repeats']=0\nresult['acceptance_eligible']=False\nresult['scope']='DIAGNOSTIC_ONLY_ORIGINAL_FOUR_HEIGHT_FAILURES_PRESERVED'\nresult['height_result_sha256']='e086af218bc393476256cbfc17a540964d2daf53735dd9587585ae15eb9f7041'")
    path=R/ren(name);assert not path.exists()
    if path.suffix=='.py':ast.parse(s)
    path.write_text(s)
archive=json.loads((R/'archived-mods-nav12-space-20261027/archive-plan.json').read_text(encoding='utf-8-sig'))
restore=[r for r in archive if '@DayZ_Baltic_EV112_Kit7NavV9/' in r['destination'].replace('\\','/')];assert len(restore)==3
assert shutil.disk_usage('C:/').free>sum(x['bytes'] for x in restore)+2*1024**3
for row in restore:
    src=Path(row['destination']);dst=Path(row['source'])
    assert src.is_file() and src.stat().st_size==row['bytes'] and sha(src)==row['sha256']
    assert dst.parent.resolve()==Path('P:/Mods/@DayZ_Baltic_EV112_Kit7NavV9/Addons').resolve()
    if dst.exists():assert dst.is_file() and dst.stat().st_size==row['bytes'] and sha(dst)==row['sha256']
    else:
        dst.parent.mkdir(parents=True,exist_ok=True)
        with src.open('rb') as a,dst.open('xb') as b:shutil.copyfileobj(a,b,8*1024*1024)
        assert sha(dst)==row['sha256'] and dst.stat().st_size==row['bytes']
original=json.loads((R/'kit7-nav-consumer-20261026/deployment.json').read_text())
assert all(sha(p)==h for p,h in original['packages'].items())
deployment=dict(status='RESTORED_EXACT_ORIGINAL_PACKAGES_DIAGNOSTIC_ONLY',packages=original['packages'],inputs={str(R/'kit7-nav-consumer-20261026/deployment.json'):sha(R/'kit7-nav-consumer-20261026/deployment.json')},height_result_sha256=sha(R/'kit7-nav-consumer-20261026/result.json'),acceptance_eligible=False)
(D/'deployment.json').write_text(json.dumps(deployment,indent=2)+'\n')
(D/'restore.json').write_text(json.dumps(dict(status='COPIED_AND_VERIFIED_ARCHIVE_RETAINED',files=restore),indent=2)+'\n')
print('Prepared isolated diagnostic runners and restored three exact own PBOs; no launch')
