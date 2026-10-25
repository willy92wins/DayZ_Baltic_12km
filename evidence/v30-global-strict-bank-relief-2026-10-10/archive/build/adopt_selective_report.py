"""Explicitly adopt verified incremental terrain; never re-label the rejected global trial."""
import argparse,ast,hashlib,json,shutil
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
OLD='a7146c27a634d3ee59bc4c2763d71050da3172724c4f2620a17fce0775fcf020'
NEW='8e239f8e2815b61a920421af1dfbb1b64f353ab4978d633eb39fe74f04946d1b'

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--review-sha',required=True);a=ap.parse_args()
 report_path=R/'selective/selective-review.json'
 assert sha(report_path)==a.review_sha
 report=json.loads(report_path.read_text(encoding='utf-8'))
 assert report['status']=='PASS_INCREMENTAL_NONREGRESSION'
 assert report['gates'] and all(v is True for v in report['gates'].values())
 assert report['global_representation_status']=='FAIL_WITH_INHERITED_OPEN'
 assert report['information']['global_contract_status']=='FAIL_WITH_INHERITED_OPEN' and report['information']['inherited_open']
 assert report['information']['changed_vertices']==4987
 candidate=R/'selective/candidate-terrain.npz'
 assert sha(candidate)==NEW and report['inputs'][str(candidate)]==NEW
 for path,digest in report['inputs'].items():assert sha(path)==digest,('accepted input drift',path)
 original=R/'candidate-terrain.npz';raw=R/'review-independent/coverage-contract-review.json'
 assert sha(original)==OLD
 assert sha(raw)=='079557bc0419bad0ed35c1472e34fad7e4e27089229c26403d95a7dd498fb2b9'
 assert json.loads(raw.read_text())['status']=='FAIL_EV87_REPRESENTATION_CONSUMER'
 for name in ('build-inputs.json','surface','package','missions','deploy.json','selective-adoption-receipt.json'):
  assert not (D/name).exists(),('Build already begun',name)
 targets=[D/n for n in ('lock_build_inputs.py','build_surface.py','stage.py','package.py','prepare_probe.py','prepare_native_adapters.py')]
 prepared={}
 for path in targets:
  old=path.read_text(encoding='utf-8')
  assert 'ev87-review.json' in old and 'PASS_EV87_GLOBAL_CONSUMER' in old
  new=old.replace('review-independent/ev87-review.json','selective/selective-review.json')
  new=new.replace("'review-independent' / 'ev87-review.json'","'selective' / 'selective-review.json'")
  new=new.replace('PASS_EV87_GLOBAL_CONSUMER','PASS_INCREMENTAL_NONREGRESSION')
  new=new.replace("'candidate-terrain.npz'","'selective/candidate-terrain.npz'").replace(OLD,NEW)
  assert 'ev87-review.json' not in new and OLD not in new
  if path.name!='prepare_native_adapters.py':
   var='report' if path.name=='prepare_probe.py' else 'review'
   lines=new.splitlines();hits=[i for i,line in enumerate(lines) if line.lstrip().startswith('assert '+var) and 'PASS_INCREMENTAL_NONREGRESSION' in line]
   assert len(hits)==1,(path,hits)
   index=hits[0];indent=lines[index][:len(lines[index])-len(lines[index].lstrip())]
   lines[index+1:index+1]=[indent+f"assert {var}['global_representation_status']=='FAIL_WITH_INHERITED_OPEN'",
     indent+f"assert {var}['information']['global_contract_status']=='FAIL_WITH_INHERITED_OPEN' and {var}['information']['inherited_open']"]
   new='\n'.join(lines)+'\n'
  if path.name=='lock_build_inputs.py':
   marker="D/'reference-inputs.json',D/'native-adapter-receipt.json',"
   assert marker in new
   new=new.replace(marker,marker+"\n        D/'selective-adoption-receipt.json',R/'selective-integration-plan.md',\n        R/'selective/integration-receipt.json',R/'selective/verify_selective.py',")
  ast.parse(new);prepared[path]=(old,new)
 archive=D/'before-selective-adoption';archive.mkdir(exist_ok=False);changes={}
 for path,(old,new) in prepared.items():
  before=sha(path);backup=archive/path.name;shutil.copyfile(path,backup)
  path.write_text(new,encoding='utf-8',newline='\n')
  changes[str(path)]={'before_sha256':before,'after_sha256':sha(path),'backup':str(backup)}
 native_path=D/'native-adapter-receipt.json';backup=archive/native_path.name
 shutil.copyfile(native_path,backup);native=json.loads(native_path.read_text())
 native['supersedes']={'path':str(backup),'sha256':sha(backup)}
 native['output']={p:sha(p) for p in native['output']}
 native['incremental_contract']={'report':str(report_path),'sha256':a.review_sha,
  'candidate_sha256':NEW,'absolute_global_representation':'FAIL_WITH_INHERITED_OPEN'}
 native_path.write_text(json.dumps(native,indent=2)+'\n',encoding='utf-8')
 out={'status':'BUILD_GUARDS_ADOPT_INCREMENTAL_NONREGRESSION','accepted_report':str(report_path),
  'accepted_report_sha256':a.review_sha,'candidate_sha256':NEW,'changes':changes,
  'native_adapter_receipt_sha256':sha(native_path),'original_candidate_sha256':sha(original),
  'preserved_absolute_fail_sha256':sha(raw),'limits':'No build executed; inherited water and visual defects remain open.'}
 (D/'selective-adoption-receipt.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'status':out['status'],'scripts':len(changes)}))
if __name__=='__main__':main()
