import hashlib, json
from pathlib import Path
import numpy as np
ROOT=Path(r'E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\G\wet-bank-pilot')
BASE=ROOT.parent.parent/'global-operator-prototype'/'real-sector-preflight'/'ev94-rebase'/'slope-bound'/'composition-run-01'/'terrain.npz'
PREP=ROOT/'prepared-runs'/'attempt-08'/'prepared.npz'
RECEIPT=ROOT/'prepared-runs'/'attempt-08'/'preparation.json'
RUNNER=ROOT/'run_once.py'
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def matches_context(prepared, base_context):
    # Exact predicate used by run_once.py's pre-solve guard.
    return not (prepared.dtype != np.float32 or base_context.shape != prepared.shape or
                not np.array_equal(prepared.view(np.uint32), base_context.view(np.uint32)))
receipt=json.loads(RECEIPT.read_text(encoding='utf-8'))
window=np.asarray(receipt['geometry']['window_rc_half_open'],dtype=np.int64)
assert window.shape==(4,) and np.all(window>=0)
r0,r1,c0,c1=map(int,window)
with np.load(PREP,allow_pickle=False) as z: B=z['base_heights_context'].copy()
with np.load(BASE,allow_pickle=False) as z: base=z['heights'][r0:r1,c0:c1].copy()
assert matches_context(B,base), 'positive exact baseline window should match'
mutated=base.copy(); mutated[0,0]=np.nextafter(mutated[0,0],np.float32(np.inf),dtype=np.float32)
assert not matches_context(B,mutated), 'one-ULP corner mutation must be rejected'
assert not matches_context(B,base[:-1,:]), 'wrong shape must be rejected'
assert not matches_context(B.astype(np.float64),base), 'wrong dtype must be rejected'
src=RUNNER.read_text(encoding='utf-8')
assert "base_context=z['heights'][r0:r1,c0:c1]" in src
assert 'not np.array_equal(B.view(np.uint32),base_context.view(np.uint32))' in src
assert src.index("base_context=z['heights'][r0:r1,c0:c1]") < src.index("if B.dtype!=np.float32") < src.index("a.out.mkdir(parents=True,exist_ok=False)")
report={
 'status':'PASS_STANDALONE_CONTEXT_GUARD_FIXTURES',
 'runner_sha256':sha(RUNNER),'prepared_sha256':sha(PREP),'base_sha256':sha(BASE),'preparation_sha256':sha(RECEIPT),
 'window_rc_half_open':[r0,r1,c0,c1], 'shape':list(B.shape),'dtype':str(B.dtype),
 'checks':{'real_pinned_window_exact_bits':True,'single_corner_one_ulp_mutation_rejected':True,'wrong_shape_rejected':True,'wrong_dtype_rejected':True,'guard_precedes_output_marker':True},
 'scope':'Fixture only; run_once.py and solver were not invoked.'}
(Path(__file__).with_name('fixture-report.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
