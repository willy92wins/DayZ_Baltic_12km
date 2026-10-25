"""Regression on a real old consumer plus independent analytic separation cases."""
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path('P:/DayZ_Baltic_12km_dev');OUT=Path(__file__).resolve().parent/'path-controls.json'
assert not OUT.exists()
sys.path.insert(0,str(ROOT/'tools/terrain'))
from verify_v30_acceptance import verify
def accepted(ref,text):
    try:return verify(ref,text)['status']=='PASS_NATIVE_V30_PATHS'
    except (ValueError,IndexError):return False
legacy_ref=json.loads((ROOT/'evidence/v30-resume-2026-10-02/acceptance-reference.json').read_text())
old=(ROOT/'evidence/v30-runtime-2026-10-02/native-paths.log').read_text();rows=old.splitlines()
assert accepted(legacy_ref,old)
bad={
 'old_missing_end':'\n'.join(rows[:-1]),
 'old_wrong_world':old.replace(';BalticTrial',';ChernarusPlus',1),
 'old_missing_case':'\n'.join(r for r in rows if not r.startswith(('Q;delta;','P;delta;'))),
 'old_duplicate_query':'\n'.join([rows[0],rows[1]]+rows[1:]),
 'old_partial_endpoint':old.replace('P;delta;1;<8622.000000','P;delta;1;<8600.000000',1),
 'old_nonfinite_endpoint':old.replace('P;delta;1;<8622.000000','P;delta;1;<nan',1),
 'old_none_succeeds':old.replace('Q;negative;false;false;false;','Q;negative;true;true;true;',1)}
for name,log in bad.items():assert log!=old and not accepted(legacy_ref,log),name
ref=dict(queries=[dict(name='gap',start=[0,1,0],end=[60,1,0],expect='disconnected')],limits=['Synthetic only'])
head='BALTIC_V30_ACCEPTANCE_V1;BalticTrial\n';end='END;1\n'
q='Q;gap;true;true;false;0;<0,1,0>;<60,1,0>;<0,0.5,0>;<60,0.5,0>\n'
p0='P;gap;0;<0,0.5,0>;<0,0.5,0>;<0,0.5,0>\n'
p1='P;gap;1;<10,0.5,0>;<10,0.5,0>;<10,0.5,0>\n'
empty=head+q+end
partial=head+q.replace(';false;0;',';true;2;')+p0+p1+end
assert accepted(ref,empty) and accepted(ref,partial)
negative={
 'gap_full_path':partial.replace('<10,0.5,0>','<60,0.5,0>'),
 'gap_full_path_false_flag':partial.replace('<10,0.5,0>','<60,0.5,0>').replace(';true;2;',';false;2;'),
 'gap_bad_land_sample':empty.replace('Q;gap;true;true;','Q;gap;false;true;'),
 'gap_distant_sample':empty.replace(';<0,0.5,0>;',';<10,0.5,0>;'),
 'gap_found_empty':empty.replace(';false;0;',';true;0;'),
 'gap_wrong_partial_start':partial.replace('P;gap;0;<0,0.5,0>','P;gap;0;<10,0.5,0>'),
 'gap_wrong_requested_goal':empty.replace(';<60,1,0>;',';<65,1,0>;'),
 'gap_missing_end':empty.replace('END;1\n','')}
for name,log in negative.items():assert log!=empty and not accepted(ref,log),name
unknown=json.loads(json.dumps(ref));unknown['queries'][0]['expect']='unknown'
assert not accepted(unknown,empty)
result=dict(status='PASS_NAV_VERIFIER_REGRESSION_AND_SEPARATION_CONTROLS',
 positives=['Historical native ten-case log unchanged','Synthetic empty gap','Synthetic partial gap'],
 negatives=list(bad)+list(negative)+['unknown_expectation'],
 negative_count=len(bad)+len(negative)+1,
 verifier_sha256=hashlib.sha256((ROOT/'tools/terrain/verify_v30_acceptance.py').read_bytes()).hexdigest(),
 limits=['Offline consumer checks; synthetic gap cases do not prove new terrain navigation.'])
OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))
