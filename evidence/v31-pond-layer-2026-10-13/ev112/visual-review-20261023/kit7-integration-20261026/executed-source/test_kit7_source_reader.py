"""Damage actual new WRP copies; original reader must reject before acceptance."""
from pathlib import Path
import hashlib,json,struct,sys,traceback
R=Path(__file__).parent;sys.path.insert(0,str(R));import verify_kit7_fc_stage as reader
S=R/'stage-kit7-fc-20261026';O=R/'kit7-source-reader-controls-20261026';O.mkdir(exist_ok=False)
src=S/'root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
with src.open('rb') as f:reader.pre(f);offset=f.tell();ident,raw,_,_=reader.row(f)
blob=src.read_bytes();before=hashlib.sha256(blob).hexdigest()
assert json.loads((S/'independent-source-review.json').read_text())['wrp_sha256']==before
outcomes={}
for case in ['changed_height','moved_object','missing_object','extra_object']:
 target=O/case/'root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp';target.parent.mkdir(parents=True)
 if case=='changed_height':bad=blob[:24]+struct.pack('<f',struct.unpack_from('<f',blob,24)[0]+1)+blob[28:]
 elif case=='moved_object':bad=blob[:offset+36]+struct.pack('<f',struct.unpack_from('<f',blob,offset+36)[0]+.25)+blob[offset+40:]
 elif case=='missing_object':bad=blob[:offset]+blob[offset+len(raw):]
 else:bad=blob[:offset]+raw+blob[offset:]
 target.write_bytes(bad);del bad
 reader.O=O/case
 try:reader.main()
 except AssertionError as exc:
  frames=traceback.extract_tb(exc.__traceback__);last=frames[-1]
  assert Path(last.filename).resolve()==Path(reader.__file__).resolve(),'unexpected failure outside reader'
  expected='assert ya==' if case=='changed_height' else ('assert actual==expect' if case=='moved_object' else 'assert oi==ident')
  assert expected in last.line,(case,last.line)
  outcomes[case]=dict(rejected=True,reader_line=last.lineno,assertion=last.line,message=str(exc))
 else:raise AssertionError('mutant accepted: '+case)
 assert not (O/case/'independent-source-review.json').exists()
 print('REJECTED',case,flush=True)
assert hashlib.sha256(src.read_bytes()).hexdigest()==before
(O/'result.json').write_text(json.dumps(dict(status='PASS_REAL_WRP_MUTANT_CONTROLS',positive_review=str(S/'independent-source-review.json'),source_sha256=before,mutants=outcomes,original_unchanged=True),indent=2)+'\n')
