from pathlib import Path
import hashlib,json,difflib
R=Path(__file__).parent;O=R/'kit7-overlap-native-20261026';old=R/'kit7-water-native-20261026'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
dep=read(O/'deployment.json');a=read(R/'kit7-contact-only-review-20261026/accepted.json')
inputs=dict(a['inputs'])
for mapping in [dep['inputs'],dep['deployed']]:
 for p,h in mapping.items():assert sha(Path(p))==h,p;inputs[p]=h
for p,h in inputs.items():assert sha(Path(p))==h,p
for p in [O/'deployment.json',O/'prelaunch.json',R/'kit7-contact-only-review-20261026/accepted.json',R/'consume_kit7_overlap_native.py',R/'finish_kit7_overlap_survey.js',old/'accepted.json',old/'consumer-clock-fix.json',old/'full/result.json',old/'full/native.log']:
 inputs[str(p)]=sha(p)
assert (O/'points.json').read_bytes()==(old/'points.json').read_bytes()
# Prove judge and producer are unchanged; only folder plus historical manifest binding differ.
before=(R/'consume_kit7_water_native_v2.py').read_text()
after=(R/'consume_kit7_overlap_native.py').read_text()
start=before.index("fix=read(O/'consumer-clock-fix.json')");end=before.index('host=read',start)
expected=before[:start]+"for mapping in (dep['inputs'],accept['inputs']):\n for p,h in mapping.items():assert sha(Path(p))==h,p\n"+before[end:]
expected=expected.replace("O=R/'kit7-water-native-20261026'","O=R/'kit7-overlap-native-20261026'")
assert after==expected
doc=dict(status='ACCEPTED_FOR_NATIVE_RUNS',inputs=inputs,consumer_delta='Only output folder and historical consumer-fix manifest binding; judge, clock binding and physical tolerances unchanged.',counts=dep['counts'],points_exact_parent=sha(old/'points.json'),calibration='Fresh run required with exact new deployed package set.',limits=['Runtime still pending. No navigation or client acceptance.'])
out=O/'accepted.json';assert not out.exists();out.write_text(json.dumps(doc,indent=2)+'\n')
print(json.dumps(dict(status=doc['status'],inputs=len(inputs),counts=doc['counts'])))

