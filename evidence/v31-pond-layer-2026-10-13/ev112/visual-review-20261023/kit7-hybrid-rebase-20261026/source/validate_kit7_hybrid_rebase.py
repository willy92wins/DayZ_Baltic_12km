from pathlib import Path
import hashlib,json,subprocess,sys
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'kit7-hybrid-pilot-20261026'
assert json.loads((O/'candidate/report.json').read_text())['status']=='PARTIAL_LOCAL_OFFLINE_PASS_PENDING_FULL_VALIDATION'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sources={R/'audit_guarded_all_e.py':R/'audit_kit7_hybrid_all.py',R/'validate_guarded_relief_e.py':R/'merge_kit7_hybrid_relief.py'}
for source,target in sources.items():
    assert not target.exists()
    text=source.read_text()
    text=text.replace("R/'combined-merged'","R/'river-kit7-merged-byteexact-20261026'")
    text=text.replace('combined-merged/terrain-buried.npz','river-kit7-merged-byteexact-20261026/terrain-buried.npz')
    text=text.replace('combined-merged/envelope.npy','river-kit7-merged-byteexact-20261026/envelope.npy')
    text=text.replace('combined-merged/bury-work/fp0/footprint.npz','river-kit7-merged-byteexact-20261026/bury-work/fp0/footprint.npz')
    text=text.replace('guarded-relief-batch-e-merged','kit7-hybrid-pilot-merged-20261026')
    text=text.replace('guarded-relief-batch-e-roads','kit7-hybrid-pilot-roads-20261026')
    text=text.replace('guarded-relief-batch-e','kit7-hybrid-pilot-20261026/candidate')
    text=text.replace('guarded-relief-discovery/domains.npz','kit7-remaining-relief-discovery-20261026/domains.npz')
    assert 'combined-merged' not in text and 'guarded-relief-batch-e' not in text
    target.write_text(text)
    with (O/(target.stem+'.log')).open('wb') as log:
        p=subprocess.run([sys.executable,'-I',str(target)],cwd=W,stdout=log,stderr=subprocess.STDOUT,timeout=600)
    if p.returncode:raise RuntimeError(target.name+' failed; see retained log')
audit=json.loads((O/'candidate/all-protected-audit.json').read_text());assert audit['status']=='PASS'
sys.path[:0]=[str(W/'tools/quality'),str(W/'tools/terrain')]
from screen_shapes_ev112 import terrain_screen
screens={}
for label,base in [('baseline',R/'river-kit7-merged-byteexact-20261026'),('candidate',R/'kit7-hybrid-pilot-merged-20261026')]:
    tp=base/'terrain-buried.npz';fp=base/'bury-work/fp0/footprint.npz'
    screen,_=terrain_screen(tp,fp)
    screen['inputs']={str(p):sha(p) for p in (tp,fp)}
    (O/(label+'-shape-screen.json')).write_text(json.dumps(screen,indent=2)+'\n')
    screens[label]=screen['finding_counts']
result=dict(status='OFFLINE_GUARDS_PASS_PENDING_REVIEW_STAGE_NATIVE',finding_counts=screens,
            all_protected_audit='PASS',water_merge=json.loads((R/'kit7-hybrid-pilot-merged-20261026/merge-verification.json').read_text()),
            roads=json.loads((R/'kit7-hybrid-pilot-roads-20261026/review.json').read_text()),
            limits='One corrected guarded peak only. No forest staging, compiled artifact, runtime, visual or global acceptance.')
(O/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='roads'},indent=2))
