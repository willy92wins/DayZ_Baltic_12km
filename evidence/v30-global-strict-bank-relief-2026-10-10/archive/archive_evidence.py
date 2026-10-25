"""Archive compact EV87 evidence, pin large derived artifacts outside Git."""
from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).resolve().parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
D=W/'evidence/v30-global-strict-bank-relief-2026-10-10'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
report=R/'selective/selective-review.json'
assert sha(report)=='cc2b94b1a1b86e8e139edd532be9d77f95edc3526a5af1706c5dc29f2bfc41a0'
d=json.loads(report.read_text());assert d['status']=='PASS_INCREMENTAL_NONREGRESSION'
assert d['gates'] and all(x is True for x in d['gates'].values())
assert d['global_representation_status']=='FAIL_WITH_INHERITED_OPEN'
raw=json.loads((R/'selective/_consumer-scratch/ev87-global-report.json').read_text())['information']
summary={'status':d['status'],'global_representation_status':d['global_representation_status'],
 'full_report':str(report),'full_report_sha256':sha(report),'gates':d['gates'],
 'information':{k:v for k,v in d['information'].items() if isinstance(v,(int,float,str,bool))},
 'global_angular_statistics':{k:{s:v[s] for s in ('B','candidate')} for k,v in raw['p99'].items()},
 'crossing_max_shift_m':raw['crossing_max_shift_m'],
 'new_over30_count':raw['new_over30_count'],'new_weak_extrema_count':raw['new_weak_extrema_count'],
 'limits':['Incremental nonregression only. Absolute inherited representation conflicts remain open.',
           'Static compiled geometry is not renderer or wave-envelope acceptance.']}
D.mkdir(parents=True,exist_ok=True)
(D/'selective-review-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
paths=set()
for folder in (R,R/'selective',R/'review-independent',R/'residual-review',R/'build',R/'build/scalar-probe'):
 for p in folder.iterdir():
  if p.is_file() and p.suffix.lower() in {'.py','.json','.jsonl','.npz','.npy','.md','.ps1','.log','.rpt','.csv','.png'}:
   paths.add(p)
for folder in (R/'selective/_consumer-scratch',R/'build/candidate',R/'build/before-selective-adoption',R/'build/scalar-probe/BalticScalarMarginV1.BalticTrial'):
 if folder.exists():paths.update(p for p in folder.iterdir() if p.is_file())
manifest=[]
for p in sorted(paths):
 relative=p.relative_to(R);size=p.stat().st_size;dest=None
 # Keep code/compact evidence editable; large logs, meshes and arrays stay hash-pinned.
 if p.suffix.lower() not in {'.npz','.npy','.jsonl'} and size<=600000:
  q=D/'archive'/relative;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);dest=str(q.relative_to(D))
  assert sha(q)==sha(p)
 manifest.append({'external_path':str(p),'sha256':sha(p),'bytes':size,'archived':dest})
(D/'manifest.json').write_text(json.dumps({'status':'EVIDENCE_ARCHIVE','external_root':str(R),'artifacts':manifest},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'artifacts':len(manifest),'copied':sum(x['archived'] is not None for x in manifest),'destination':str(D)}))
