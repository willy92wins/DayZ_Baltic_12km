from pathlib import Path
import hashlib, importlib.util, json, os

R = Path('E:/DayZ-Baltic-Build/shape-repair-20261025')
W = Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
I = R / 'road-b4b0-capture-inputs-20261029'
D = R / 'road-b4b0-capture-20261029'
PY = 'C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe'

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def put(p, obj):
    with Path(p).open('xb') as f:
        f.write((json.dumps(obj, indent=2) + '\n').encode())
        f.flush()
        os.fsync(f.fileno())

approval = json.loads((I / 'approval.json').read_bytes())
assert approval['status'] == 'REVIEWED_FOR_SINGLE_CAPTURE'
for p, h in approval['pins'].items():
    assert sha(p) == h, p
assert not D.exists(), 'capture already consumed'
D.mkdir()
put(D / 'started.json', {'approval_sha256': sha(I / 'approval.json'), 'single_attempt': True})
spec = importlib.util.spec_from_file_location('bounded_runner', R / 'council29_runner.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
c = W / 'tests/fixtures/road_b4b0/contract.json'
base = [PY, '-I', '-X', 'utf8']
common = ['--contract', str(c), '--contract-sha', approval['contract_sha256']]
producer = W / 'tools/quality/road_scene_reference_index_ev112.py'
consumer = W / 'tools/quality/verify_road_scene_reference_index_ev112.py'
p = runner.run({'id': 'road-b4b0-producer', 'command': base + [str(producer)] + common + ['--output', str(D / 'report.json')], 'cwd': str(W), 'out': str(D / 'producer'), 'seconds': 120, 'max_bytes': 1073741824, 'input_file': str(c)})
result = {'producer': p, 'consumer': None, 'status': 'INCONCLUSIVE_CAPTURE', 'build_ready': False, 'map_repaired': False}
if p['reason'] is None and (D / 'report.json').exists():
    report = json.loads((D / 'report.json').read_bytes())
    running = json.loads((D / 'producer/running.json').read_bytes())
    assert report['tool']['pid'] == running['pid']
    assert report['tool']['sha256'] == approval['pins'][str(producer)]
    assert p['identities'][running['pid']] == running['birth']
    if report['source'] is not None and report['candidate'] is not None:
        v = runner.run({'id': 'road-b4b0-consumer', 'command': base + [str(consumer)] + common + ['--report', str(D / 'report.json'), '--output', str(D / 'consumer.json')], 'cwd': str(W), 'out': str(D / 'consumer'), 'seconds': 60, 'max_bytes': 268435456, 'input_file': str(D / 'report.json')})
        result['consumer'] = v
        if v['reason'] is None and (D / 'consumer.json').exists():
            verdict = json.loads((D / 'consumer.json').read_bytes())
            cr = json.loads((D / 'consumer/running.json').read_bytes())
            assert verdict['tool']['pid'] == cr['pid']
            assert verdict['tool']['sha256'] == approval['pins'][str(consumer)]
            assert v['identities'][cr['pid']] == cr['birth']
            if p['rc'] == 0 and v['rc'] == 0 and verdict['status'] == report['status'] == 'SAVED_SCENE_REFERENCE_INDEX_ONLY':
                result['status'] = 'VERIFIED_SAVED_SCENE_REFERENCE_INDEX_ONLY'
            elif p['rc'] == 2 and v['rc'] == 2 and verdict['status'] == 'VERIFIED_MISMATCH_DIAGNOSTIC':
                result['status'] = 'VERIFIED_MISMATCH_DIAGNOSTIC'
    result['report_sha256'] = sha(D / 'report.json')
for pth, h in approval['pins'].items():
    assert sha(pth) == h, pth
put(D / 'result.json', result)
print(json.dumps(result))
