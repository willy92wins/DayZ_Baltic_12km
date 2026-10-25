from __future__ import annotations
import importlib.util, json, sys
from pathlib import Path
import numpy as np

SELECTOR = Path(__file__).with_name('selector.py')
EXPECTED_SELECTOR_SHA = '0d29d3979c1f8bc0d3b0b1833edb314a5807fe5b22ba63b43c44080732fe81bc'
spec = importlib.util.spec_from_file_location('ev93_selector_real_rows', SELECTOR)
sel = importlib.util.module_from_spec(spec); sys.modules[spec.name] = sel; spec.loader.exec_module(sel)
if sel.sha256_file(SELECTOR) != EXPECTED_SELECTOR_SHA:
    raise SystemExit('selector source SHA changed; update integration pin after review')
pool, pool_sha, crest_receipt = sel.validate_pool(sel.POOL_DEFAULT)
vl = sel.load_pinned_module('ev93_real_rows_consumer', sel.CONSUMER,
    '33050881caaf5e75f288d4122222c15eb326bf146c28a4c723760564457b3dc2')
ev, ev91, ev87, cv, shape, ev92, index_module = vl.load_helpers()
policy = sel.load_pinned_module('ev93_real_rows_policy', sel.POLICY, sel.POLICY_SHA256)
author = sel.load_pinned_module('ev93_real_rows_author', sel.COMPOUND_AUTHOR, sel.COMPOUND_AUTHOR_SHA256)
selected_local = sel.load_pinned_module('ev93_real_rows_selected_consumer', sel.SELECTED_LOCAL_CONSUMER, sel.SELECTED_LOCAL_CONSUMER_SHA256)
selected_context = selected_local.loadctx()
bundle = ev.checked_sources()
base_npz = bundle['B']; base = np.asarray(base_npz['heights'], dtype=np.float32)
prepared, legacy_receipt, entries, ledger, ledger_path = vl.verify_prepared(sel.PREPARED, sel.LEGACY_RECEIPT, base)
details = vl.validate_detail_hashes(prepared, entries)
readset = sel._source_readset(sel.POOL_DEFAULT, pool, crest_receipt, pool['rows'], vl, ev87,
    prepared, legacy_receipt, entries, ledger, ledger_path)
for path, expected in readset.items():
    if sel.sha256_file(path) != expected:
        raise AssertionError(f'Initial production readset differs: {path}')
source_candidate, _, legacy_patches, _ = vl.reconstruct_candidate(base_npz, legacy_receipt, entries, ledger, details, sel.LEGACY_RECEIPT.parent)
legacy_by_qid = {int(p['queue_id']): p for p in legacy_patches}
reuse = json.loads(sel.REUSE_INVENTORY.read_text(encoding='utf-8'))
inv_by_qid = {int(r['queue_id']): r for r in reuse['reusable_directions']}
prepared_by_qid = {int(r['queue_id']): r for r in entries}
crest_rows = [r for r in pool['rows'] if r['origin'] == 'crest']
legacy_rows = [r for r in pool['rows'] if r['origin'] == 'legacy']
row_legacy = min(legacy_rows, key=lambda r: int(r['queue_id']))
row_derived = next(r for r in sorted(crest_rows, key=lambda r: int(r['queue_id'])) if r['state'] == 'derived_quarantined')
row_rejected = next(r for r in sorted(crest_rows, key=lambda r: int(r['queue_id'])) if r['state'] == 'rejected_policy')

def check_legacy(row):
    qid = int(row['queue_id']); patch = legacy_by_qid[qid]
    one = sel._apply_one(base, patch['nodes'], patch['final'])
    result = vl.verify_local_windows(ev, ev87, shape, ev92, base, one, [patch], {qid: details[qid]})
    return {'unit_id': row['unit_id'], 'qid': qid, 'local_pass': bool(result['gates'][qid]),
            'metric_keys': sorted(result['metrics'][0]), 'patch_nodes': len(patch['nodes'])}

def check_crest(row):
    qid = int(row['queue_id']); target = json.loads(Path(row['artifact_path']).read_text(encoding='utf-8'))
    source = inv_by_qid[qid]; prep_row = prepared_by_qid[qid]
    source_result, nodes, stencils, direction = author.validate_source_row(vl, source, prep_row, base)
    local, patch = sel.crest_local_validation(selected_local, selected_context, base,
        target, row, details[qid], source, nodes, stencils, direction, sel.sha256_file(sel.PREPARED))
    return {'unit_id': row['unit_id'], 'qid': qid, 'local_status': local['local_status'],
            'local_gates': local['local_gates'], 'patch_present': patch is not None,
            'patch_nodes': 0 if patch is None else len(patch['nodes'])}

out = {'status': 'REAL_ROW_INTEGRATION_PASS', 'pool_sha256': pool_sha,
       'production_readset_count': len(readset),
       'pool_counts': {'legacy': len(legacy_rows), 'crest': len(crest_rows)},
       'rows': [check_legacy(row_legacy), check_crest(row_derived), check_crest(row_rejected)],
       'solver_calls': 0, 'candidate_written': False}
if (out['rows'][0]['local_pass'] is not True or out['rows'][1]['local_status'] != 'PASS' or
        out['rows'][2]['local_status'] != 'FAIL' or out['rows'][2]['patch_present']):
    raise SystemExit('row state contract failed')
# Exercise the actual support path against three cells already checked by direct ODOL reading.
diagnosis_path = sel.POOL_DEFAULT.parents[2] / 'support-hole-diagnosis/support-hole-report.json'
if sel.sha256_file(diagnosis_path) != '5098683bbd10c2835ba4c14ce655da614388dbb9f5493ba169bff77f5e53cb50':
    raise AssertionError('Direct ODOL reference changed')
diagnosis = json.loads(diagnosis_path.read_text(encoding='utf-8'))
references = diagnosis['top_three_direct_odol']
cells = {tuple(row['cell_rc']) for row in references}
if len(cells) != 3: raise AssertionError('Expected exactly three direct-ODOL cells')
index = index_module.FaceRangeIndex(sel.INDEX_RUN)
support, support_stats = sel.capture_support_once(vl, ev87, cv, index, bundle['P'], bundle['F'], cells)
holes = {layer: sel._holes_for_grid(cv, ev87, source_candidate, bundle['P'], bundle['F'], cells,
                                  layer, support[layer]) for layer in sel.LAYERS}
errors = [abs(holes[row['kind']][tuple(row['cell_rc'])] - row['candidate_hole_direct_odol_m2']) for row in references]
if max(errors) > 1e-12: raise AssertionError(f'Support differs from direct-ODOL reference: {max(errors)}')
out['production_support_smoke'] = {'cells':3,'layers':2,'max_error_vs_direct_odol_m2':max(errors),'index':support_stats}
if any(sel.sha256_file(path) != expected for path,expected in readset.items()):
    raise AssertionError('Production readset changed during smoke')
print(json.dumps(out, sort_keys=True, allow_nan=False))











