"""Read bound references to establish cross-block conditions, not RAM acceptance."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path.insert(0,str(W/'tools/performance'))
from compare_server_baseline_ev112 import conditions_identity
rows=[];inputs={}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for label,folder in [('8m','kit7-nav8-ram-ab-20261027'),('12.5m','kit7-navv9diag-ram-ab-20261027')]:
    for n in range(1,7):
        path=R/folder/f'pass-{n:02}'/'reference.json';ref=json.loads(path.read_text());inputs[str(path)]=sha(path)
        c=conditions_identity(ref)
        packages={Path(p).name.lower():h for p,h in ref['packages'].items()};assert len(packages)==len(ref['packages'])
        world_sha=packages.pop('narva_trial.pbo',None)
        rows.append(dict(block=label,order=n,world=ref['world'],conditions={k:c[k] for k in ['server_config','executable','canonical_mission']},non_world_packages=packages,world_pbo_sha256=world_sha))
assert len({json.dumps(x['conditions'],sort_keys=True) for x in rows})==1
for world in ('BalticTrial','ChernarusPlus'):
    assert len({json.dumps(x['non_world_packages'],sort_keys=True) for x in rows if x['world']==world})==1
summary=[{k:v for k,v in row.items() if k!='non_world_packages'}|dict(non_world_package_count=len(row['non_world_packages'])) for row in rows]
out=R/'kit7-ram-cross-block-conditions-20261027.json';assert not out.exists()
result=dict(status='BOUND_REFERENCE_CONDITIONS_MATCH',passes=summary,inputs=inputs,limits=['Reference comparison only; each block retains its own full rehash and validation evidence.','Does not prove identical host load or causality; no RAM acceptance or linear scaling inferred.','World PBO differs intentionally; models/terrain parity must be established by packaging receipts.'])
out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(status=result['status'],passes=len(rows),world_hashes={label:sorted({x['world_pbo_sha256'] for x in rows if x['block']==label and x['world']=='BalticTrial'}) for label in ['8m','12.5m']})))
