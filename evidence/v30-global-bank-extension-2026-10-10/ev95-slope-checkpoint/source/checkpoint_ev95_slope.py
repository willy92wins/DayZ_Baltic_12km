"""Archive the accepted offline sector; preserve rejected lineage and open map status."""
from pathlib import Path
import hashlib, json, shutil

G=Path('E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010')
R=G/'global-operator-prototype/real-sector-preflight/ev94-rebase'
S=R/'slope-bound'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
D=W/'evidence/v30-global-bank-extension-2026-10-10/ev95-slope-checkpoint'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def main():
    rp=S/'consumer/full-run-01.json'
    if sha(rp)!='b0b7c872746002d11a6fc44228d7d6901bf936efc42e5156b5e77293ba84fe47':raise ValueError('Report changed')
    report=json.loads(rp.read_text())
    if len(report['gates'])!=17 or not all(v is True for v in report['gates'].values()):raise ValueError('Gates failed')
    composition=json.loads((S/'composition-run-01/composition.json').read_text())
    if sha(Path(composition['candidate']['path']))!=composition['candidate']['sha256']:raise ValueError('Candidate changed')
    names=['PLAN_SLOPE_BOUND.md','prepare_slope_bound.py','test_slope_bound.py',
           'prepared-identity-review.json','verify_slope_bound.py','compose_verified_sector.py','plot_candidate.py',
           'preflight-run-01/preflight.json','solve-run-01/solve-result.json','solve-run-01/progress.jsonl',
           'solve-run-01/native-sector-comparison.png','composition-run-01/composition.json',
           'preserved-361ad514/verify_slope_bound.py','consumer/review-01.json','consumer/review-02.json',
           'consumer/smoke-preflight-run-01.json','consumer/smoke-preflight-run-02.json',
           'consumer/smoke-preflight-run-03.json','consumer/smoke-preflight-run-04.json','consumer/full-run-01.json']
    sources=[(S/n,'slope-bound/'+n) for n in names]
    sources += [(R/n,'diagnostic/'+n) for n in ('slope-diagnostic.json','slope-diagnostic-coordinate-erratum.json')]
    sources.append((Path(__file__),Path(__file__).name))
    before={n:sha(p) for p,n in sources}
    refs=[S/n for n in ('preflight-run-01/prepared.npz','solve-run-01/candidate-local.npz',
                         'solve-run-01/solver-state.npz','composition-run-01/terrain.npz')]
    external=[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in refs]
    D.mkdir(parents=True,exist_ok=False)
    records=[]
    for p,n in sources:
        if p.stat().st_size>8*1024**2:raise ValueError('Unexpected large source')
        dest=D/'source'/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
        if sha(dest)!=before[n] or sha(p)!=before[n]:raise ValueError('Copy/source drift')
        records.append({'source':str(p),'relative_path':n,'sha256':before[n],'bytes':p.stat().st_size})
    manifest={'status':'PASS_EV95_SECTOR_OFFLINE_CHECKPOINT','copied_files':records,'external_artifacts':external,
              'gates':report['gates'],'changed_vertices_vs_focal':report['information']['changed_vertices'],
              'composition':composition,'native_acceptance':False,'visual_acceptance':False,
              'map_status':'BASE_1_0_NOT_ACCEPTED',
              'chronology':'One fresh solve started after preparation and root checks, before reviewer closed the new independent baseline check. Consumer fix was independently reviewed before acceptance; final full consumer PASS uses d111772e. No second solve or post-repair.',
              'limits':['Dry-relief sector only; wet shoreline and remaining map are open.',
                        'Compiled preview and native readback are separate subsequent steps.']}
    (D/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':manifest['status'],'copied':len(records),'external':len(external)}))

if __name__=='__main__':main()
