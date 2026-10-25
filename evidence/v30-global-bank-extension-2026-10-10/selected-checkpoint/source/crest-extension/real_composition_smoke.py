"""Exercise actual selected artifacts through the production composition consumer."""
import hashlib, importlib.util, json, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'verify_selected_composite_v2.py'
PIN = '6e661b073e5f27b2475e6b82d75d6a7722d0503a082dcfd51d8f00bd6de9722b'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(SOURCE) == PIN
spec = importlib.util.spec_from_file_location('real_composition_consumer', SOURCE)
consumer = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = consumer
spec.loader.exec_module(consumer)
selection_path = ROOT.parent / 'compound-selection/run-02/selection.json'
selection = consumer.jload(selection_path)
assert sha(selection_path) == '3b22dcc381b34b8d7c3e6641d3c919658f0fe7377594a859e3d5c064cf92ba0b'
assert sha(selection['base_path']) == selection['base_sha256']
with np.load(selection['base_path'], allow_pickle=False) as z:
    base_npz = {k: z[k] for k in z.files}
base = base_npz['heights']
patches = []
for unit in selection['units']:
    if unit['selection_status'] != 'retained': continue
    path = Path(unit['source_artifact_path'])
    assert sha(path) == unit['source_artifact_sha256']
    row = consumer.jload(path)
    if unit['origin'] == 'legacy':
        assert sha(row['delta_path']) == row['delta_sha256']
        with np.load(row['delta_path'], allow_pickle=False) as z:
            nodes = z['variables_rc'].copy()
            final = z['final_float32'].copy()
    else:
        nodes = np.asarray(row['variables_rc'], np.int32)
        final = np.asarray(row['final_float32'], np.float32)
    patches.append((unit, {'nodes': nodes, 'final': final}))
candidate, owner, changed = consumer.compose_retained(base, patches)
ref = selection['candidate']
assert sha(ref['path']) == ref['sha256']
with np.load(ref['path'], allow_pickle=False) as z:
    assert set(z.files) == set(base_npz)
    assert np.array_equal(z['heights'], candidate)
    for key in z.files:
        if key != 'heights': assert np.array_equal(z[key], base_npz[key], equal_nan=True), key
assert len(patches) == 499
assert sha(SOURCE) == PIN
report = {'status': 'PASS_REAL_499_COMPOSITION_ONLY', 'consumer_sha256': PIN,
          'selection_sha256': sha(selection_path), 'candidate_sha256': ref['sha256'],
          'retained_units': len(patches), 'owned_nodes': len(owner),
          'changed_vertices': int(np.count_nonzero(candidate != base)),
          'changed_node_inventory_exact': True, 'metadata_exact': True}
output = ROOT / 'real-composition-smoke.json'
with output.open('x', encoding='utf-8') as f: json.dump(report, f, indent=2)
print(json.dumps(report))
