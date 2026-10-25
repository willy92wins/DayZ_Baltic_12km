"""Classify native readback deltas without treating wave-phase differences as fixes."""
from pathlib import Path
import json,hashlib,shutil,re
import numpy as np
R=Path(__file__).parent;B=R.parents[1]/'v30-mixed-bank-incremental-fixed-20261010'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(R/'native-snapshot.log')=='f69470851e82ce01f144a5530f1e28edf6541a3ef82cdf270bb20778103281c8'
assert sha(B/'native-snapshot.log')=='c0effbbcf0200bd916a691e94d44546bc573dc30a7c275b8049a8ad64b2863a2'
H=np.load(R/'candidate/terrain.npz')['heights'];HB=np.load(B/'candidate/terrain.npz')['heights']
def records(path,prefix):
 return {(int(v[1]),int(v[2])):v for s in path.read_text().splitlines() if s.startswith(prefix+';') for v in [s.split(';')]}
out={'status':'NATIVE_READBACK_REVIEW','run_id':'20c41dc7-ac5b-411b-9f9c-04fe28af199d','records':{}}
for kind in ('A','Q'):
 before=records(B/'native-snapshot.log',kind);after=records(R/'native-snapshot.log',kind)
 added=sorted(after.keys()-before.keys());removed=sorted(before.keys()-after.keys())
 out['records'][kind]={'B':len(before),'candidate':len(after),'added':added,'removed':removed,
  'new_on_changed_height':[list(rc) for rc in added if H[rc]!=HB[rc]],
  'all_added_heights_unchanged':all(H[rc]==HB[rc] for rc in added)}
ref=json.loads((R/'native-reference-v2.json').read_text())
pts=[s.split(';') for s in (R/'native-snapshot.log').read_text().splitlines() if s.startswith('P;')]
out['max_calibrated_height_error_m']=max(abs(float(v[2])-q['expected_ground']) for v,q in zip(pts,ref['points']))
rpt=Path('P:/DayZ_MCP_dev/_server/profiles/DayZDiag_x64_2026-10-10_08-58-31.RPT')
text=rpt.read_text(encoding='utf-8',errors='replace')
assert 'BalticStrictBankFullWaterV1.BalticTrial' in text and '@DayZ_Baltic_StrictBankPreviewV1' in text
assert 'Termination successfully completed' in text
shutil.copyfile(rpt,R/'runtime.RPT')
out['rpt']={'source':str(rpt),'sha256':sha(rpt),'mission_and_mod_confirmed':True,'orderly_termination':True,
 'error_lines':sum('(E)' in s for s in text.splitlines()),'unknown_pond_warnings':text.count("Unknown object class 'pond'"),
 'leaked_mcp_callback':"Leaked 'MCPPollCallback'" in text}
out['limits']=['The RPT is not clean; resource errors, pond warnings and MCP callback cleanup diagnostics are preserved.',
 'Water-presence differences compare different wave phases. Do not interpret disappearance as repaired water.',
 'No client, visual shader proof, boat test or maximum-wave envelope in this run.']
(R/'runtime-review.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':out['status'],'deltas':{k:{q:v[q] for q in ('B','candidate','all_added_heights_unchanged','new_on_changed_height')} for k,v in out['records'].items()},'max_calibrated_height_error_m':out['max_calibrated_height_error_m'],'rpt':out['rpt']},indent=2))
