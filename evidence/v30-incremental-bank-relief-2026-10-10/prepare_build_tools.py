"""Adapt the verified EV80 build steps; no step runs without EV82 consumer PASS."""
from pathlib import Path
import re,json,hashlib
B=Path(__file__).parent; OLD=B.parent/'v30-mixed-bank-constrained-20261010'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((B/'review-luna/report.json').read_text())
assert r['status']=='PASS_EV82_CONSUMER' and all(r['gates'].values())
assert r['candidate_sha256']==sha(B/'candidate/terrain.npz')=='f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0'
changes={
 'v30-narva-dry-bank-relief-20261010':'v30-mixed-bank-constrained-20261010',
 'dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c':'0a18c5623885eed274cfe7d296e02aba290ed491b835d317213fc7876b2fc45b',
 '0a18c5623885eed274cfe7d296e02aba290ed491b835d317213fc7876b2fc45b':'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
 '7d49ba1916ed838f98f2436d04398f59ec490656adbb5e5063fb4101f25063ac':'6b43b82a274bf9d80767f2df4db033a084c1206cc0b0cdab8abde9df0397c064',
 'df00806c598181e9ddca160781790cd0edc9314095262f6f106a87ed4d464213':'ec3785d1eab89eb18503e358a9f7d786dca35f9eef829301bae45a1ec28d7038',
 'fee7cad702d5d2278697976654fd62e2ba0f2afbd4ab7c7d9f26369c15099f76':'3ae8f82cfc7279cec5c58dd8f253b9da79bfbfe52004695ebe02cb5587383680',
 '@DayZ_Baltic_NarvaDryBankPreviewV1':'@DayZ_Baltic_MixedBankPreviewV1',
 '@DayZ_Baltic_MixedBankPreviewV1':'@DayZ_Baltic_IncrementalBankPreviewV1',
 'PASS_EV80_CONSUMER':'PASS_EV82_CONSUMER','PASS_EV80_AFFECTED_SURFACE':'PASS_EV82_AFFECTED_SURFACE',
 'PASS_EV79_COMPOSITE_REFERENCE':'PASS_EV80_COMPOSITE_REFERENCE',
 'STAGED_EV80_HEIGHTS_ONLY':'STAGED_EV82_HEIGHTS_ONLY',
 'DEPLOYED_EV80_PREVIEW_NATIVE_READBACK_PENDING':'DEPLOYED_EV82_PREVIEW_NATIVE_READBACK_PENDING',
}
pattern=re.compile('|'.join(map(re.escape,sorted(changes,key=len,reverse=True))))
out=[]
for name in ['audit_exposure.py','audit_surface_inputs.py','stage.py','package.py','check_changed_mips.py']:
    target=B/name;assert not target.exists()
    source=OLD/name;text=pattern.sub(lambda m:changes[m[0]],source.read_text())
    compile(text,str(target),'exec');target.write_text(text,encoding='utf-8',newline='\n')
    out.append(dict(name=name,source_sha256=sha(source),target_sha256=sha(target)))
(B/'build-tools-provenance.json').write_text(json.dumps(dict(status='PREPARED_NOT_EXECUTED',tools=out),indent=2)+'\n')
print(json.dumps(out,indent=2))
