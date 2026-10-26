from pathlib import Path
import hashlib,json
R=Path(__file__).parent;D=R/'nav-kit7-preparation-20261026'
s=(R/'orchestrate_nav_kit7_v2.js').read_text()
old="const prepared=await read(d+'/launch-inputs.json');"
new="""const prepared=JSON.parse((await cmd("Get-Content -LiteralPath '"+d+"/launch-inputs.json' -Raw | ConvertFrom-Json | Select-Object status,observer_sha256,packages | ConvertTo-Json -Depth 6",10000,3000)).output);"""
assert s.count(old)==1;s=s.replace(old,new)
p=R/'orchestrate_nav_kit7_v3.js';assert not p.exists();p.write_text(s)
for basename in ['coordinator','command','lease']:
 p=R/f'test_nav_kit7_{basename}_v2.cjs';t=p.read_text().replace('orchestrate_nav_kit7_v2.js','orchestrate_nav_kit7_v3.js').replace('-v2.json','-v3.json').replace('-v2.js','-v3.js')
 out=R/f'test_nav_kit7_{basename}_v3.cjs';assert not out.exists();out.write_text(t)
doc=dict(status='PRELAUNCH_OUTPUT_TRUNCATION_NO_RUN',failed_coordinator_sha256=hashlib.sha256((R/'orchestrate_nav_kit7_v2.js').read_bytes()).hexdigest(),replacement_sha256=hashlib.sha256(s.encode()).hexdigest(),mechanism='Full256inputmanifest exceeded9000token command-output budget. JSON parser rejected truncation warning before lifecycle call. Project only three consumed fields for JS; full on-disk manifest remains verified by PowerShell pre/post loops.',new_launch=False,generator_started=False,attempt_consumed=False,source_delta=[old,new])
(D/'manifest-read-fix.json').write_text(json.dumps(doc,indent=2)+'\n')
print('V3_BOUNDED_READ_PREPARED')

