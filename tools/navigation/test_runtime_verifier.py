from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile

root=Path('P:/DayZ_Baltic_12km_dev')
evidence=root/'evidence/navigation'
raw=(evidence/'runtime-launch/boat-v3-complete.log').read_text(encoding='utf-8-sig')
cases={
    'truncated_before_END':'\n'.join(raw.splitlines()[:-1])+'\n',
    'wrong_ASC_identity':raw.replace('ASC=c1f23f24808cb6f1ff858f47a378f6bdf8211387f63c110a12ff72fd3bd82d3c','ASC=wrong_identity'),
}
results=[]
with tempfile.TemporaryDirectory(prefix='navigation-verifier-', dir=Path(__file__).parent) as tmp:
    for name,content in cases.items():
        src=Path(tmp)/(name+'.log')
        out=Path(tmp)/(name+'.json')
        src.write_text(content,encoding='utf-8')
        p=subprocess.run([sys.executable,'-X','utf8',str(root/'tools/navigation/verify_boat_probe.py'),
                          '--log',str(src),'--out',str(out)],capture_output=True,text=True,encoding='utf-8')
        if p.returncode!=1 or not out.exists():
            raise RuntimeError(name+': expected controlled rejection; '+p.stderr[-500:])
        report=json.loads(out.read_text())
        failed=[k for k,v in report['checks'].items() if not v]
        expected='terminated_record' if name=='truncated_before_END' else 'correct_ASC_marker'
        if report['geometry_status']!='FAIL_OR_INCOMPLETE' or failed!=[expected]:
            raise AssertionError((name,failed))
        results.append({'case':name,'exit_code':p.returncode,'rejected_by':failed})

for name in ['boat-fixture.json','deployment-v3.json']:
    info=json.loads((evidence/name).read_text())
    key='init_sha256' if name.startswith('boat') else 'mission_init_sha256'
    actual=hashlib.sha256((root/'missions/BalticBoat.BalticTrial/init.c').read_bytes()).hexdigest()
    assert info[key]==actual
receipt={'status':'PASS_NEGATIVE_REJECTIONS_AND_MISSION_IDENTITY','negative_cases':results,
         'positive_evidence':'runtime-verification.json from unchanged complete engine log',
         'limits':'Only integrity/completeness gates tested; this does not validate boat motion.'}
(evidence/'verifier-negative-tests.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt,indent=2))
