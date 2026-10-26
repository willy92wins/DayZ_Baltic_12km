"""Fresh native terrain pattern census; candidates remain open diagnostics."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/quality'),str(W/'tools/terrain')]
import screen_shapes_ev112 as screen
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
tp=R/'river-kit7-merged-byteexact-20261026/terrain-buried.npz';fp=tp.parent/'bury-work/fp0/footprint.npz'
out=R/'kit7-integrated-terrain-shapes-20261026.json';assert not out.exists()
assert sha(tp)=='815ef8b772bfa10e9d6886d953878c24ef6819c5667ce4700c91faab992aec40'
assert sha(fp)=='084171b0e29df5c220f9d5aab42a3dc683a2f70a07579f08cd930dfd109e716b'
paths=[tp,fp,Path(__file__),Path(screen.__file__),W/'tools/quality/shape_patterns_ev112.py',W/'tools/terrain/despike_v31.py']
inputs={str(p):sha(p) for p in paths}
result,_=screen.terrain_screen(tp,fp)
assert all(sha(p)==h for p,h in inputs.items())
result.update(status='REVIEW_REQUIRED',visual_acceptance=False,inputs=inputs,inputs_unchanged=True)
out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'counts':result['finding_counts']}))
