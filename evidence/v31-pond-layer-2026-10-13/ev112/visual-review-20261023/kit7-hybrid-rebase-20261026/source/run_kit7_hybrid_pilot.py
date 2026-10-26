from pathlib import Path
import hashlib,json,subprocess,sys,time
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
base=R/'river-kit7-merged-byteexact-20261026';discovery=R/'kit7-guarded-rebase-1171-190-20261026/selected-discovery'
O=R/'kit7-hybrid-pilot-20261026';O.mkdir(exist_ok=False)
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
paths=[Path(__file__),base/'terrain-buried.npz',base/'envelope.npy',base/'bury-work/fp0/footprint.npz',discovery/'report.json',discovery/'domains.npz',W/'plans/ev112-rebased-hybrid-relief-20261026.md']
paths += [W/'tools/terrain'/n for n in ['repair_guarded_shapes_ev112.py','repair_free_shapes_ev112.py','despike_v31.py','census_pyramids_v31.py','census_creases_v31.py','shape_repair_constraints_ev112.py','native_crease_constraints_ev112.py']]
paths += [W/'tools/water/continuous_stream_pilot_v31.py']
inputs={str(p):sha(p) for p in paths}
assert sha(base/'terrain-buried.npz')=='815ef8b772bfa10e9d6886d953878c24ef6819c5667ce4700c91faab992aec40'
(O/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
args=[sys.executable,'-I',str(W/'tools/terrain/repair_guarded_shapes_ev112.py'),str(base),str(discovery),str(O/'candidate'),'--expected-terrain-sha256',sha(base/'terrain-buried.npz'),'--expected-domains-sha256',sha(discovery/'domains.npz'),'--hybrid-witnesses']
start=time.monotonic()
with (O/'stdout.log').open('wb') as stdout,(O/'stderr.log').open('wb') as stderr:
    try:p=subprocess.run(args,stdout=stdout,stderr=stderr,timeout=300);rc=p.returncode
    except subprocess.TimeoutExpired:rc=124
assert all(sha(Path(k))==v for k,v in inputs.items())
(O/'receipt.json').write_text(json.dumps(dict(returncode=rc,seconds=time.monotonic()-start,inputs=inputs,inputs_unchanged=True,scope='ISOLATED_PILOT_PENDING_INDEPENDENT_VALIDATION'),indent=2)+'\n')
if (O/'candidate/report.json').exists():print((O/'candidate/report.json').read_text())
else:print((O/'stderr.log').read_text(errors='replace'))
raise SystemExit(rc)
