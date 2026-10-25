from pathlib import Path
import hashlib,json,shutil
G=Path('E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010')
P=G/'global-operator-prototype/face-slope-cone-pilot'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
D=W/'evidence/v30-global-bank-extension-2026-10-10/cone-pilot-checkpoint'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
review=P/'consumer-independent/solution-review-03.json'
assert sha(review)=='4b0fd2a4b495b9f60ea8f279f63e5e13c048528fd01170e11b0a54528f61cdba'
j=json.loads(review.read_text());assert all(v is True for v in j['checks'].values())
assert j['status']=='PASS_FACE_SLOPE_CONE_SYNTHETIC_ONLY'
names=['pilot.py','PLAN.md','run_reviewed_once.py','preflight-recheck-01/preflight.json',
       'preflight-recheck-01/PLAN.md','preflight-recheck-01/pilot.py',
       'preflight-recheck-01/solve-run.log','preflight-recheck-01/solve-run-02.log',
       'preflight-recheck-01/solve-once/solve-result.json','preflight-recheck-01/solve-once/progress.jsonl']
names += [p.relative_to(P).as_posix() for p in sorted((P/'consumer-independent').rglob('*'))
          if p.is_file() and p.suffix in ('.py','.json') and '__pycache__' not in p.parts]
src=[(P/n,n) for n in names]+[(Path(__file__),Path(__file__).name)]
before={n:sha(p) for p,n in src};D.mkdir(parents=True,exist_ok=False);records=[]
for p,n in src:
    q=D/'source'/n;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
    assert sha(q)==before[n]==sha(p)
    records.append({'source':str(p),'relative_path':n,'sha256':before[n]})
refs=[]
for n in ['preflight-recheck-01/prepared.npz','preflight-recheck-01/solve-once/solution.npz']:
    p=P/n;refs.append({'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size})
out={'status':j['status'],'copied_files':records,'external_artifacts':refs,'checks':j['checks'],
     'solution':j['solution'],'metrics':j['metrics'],'map_acceptance':False,
     'chronology':'Copied CLI failed before creating run; original-module runner made exactly one numerical solve. Consumer schema fixes preserved; no numeric gate or candidate changed.',
     'limits':['Synthetic coupled-sector feasibility only. Does not authorize map solve or prove whole-map performance.']}
(D/'manifest.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'status':out['status'],'copied':len(records),'external':len(refs)}))
