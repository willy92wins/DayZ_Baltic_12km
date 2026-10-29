from pathlib import Path
import hashlib, importlib.util, json, os

R = Path('E:/DayZ-Baltic-Build/shape-repair-20261025')
W = Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
S = R / 'road-b4b0-capture-20261029'
D = R / 'road-b4b0-saved-consumption-20261029'
I = R / 'road-b4b0-saved-inputs-20261029'
PY = 'C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe'

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def put(p, obj):
    with Path(p).open('xb') as f:
        f.write((json.dumps(obj, indent=2) + '\n').encode())
        f.flush()
        os.fsync(f.fileno())

def process_binding(report, running, completion, expected_script, expected_sha):
    tool = report['tool']
    pid = tool['pid']
    if type(pid) is not int or pid <= 0:
        raise ValueError('invalid report pid')
    identities = {str(k): v for k, v in completion['identities'].items()}
    if str(pid) not in identities:
        raise ValueError('report process was not observed in owned tree')
    if identities.get(str(running['pid'])) != running['birth']:
        raise ValueError('launcher birth mismatch')
    birth = identities[str(pid)]
    if not (running['started'] <= birth <= completion['finished']):
        raise ValueError('report process birth outside observation window')
    if completion['started'] != running['started'] or completion['reason'] is not None:
        raise ValueError('incomplete execution receipt')
    if tool['path'] != str(expected_script) or tool['sha256'] != expected_sha:
        raise ValueError('script identity mismatch')
    return {'pid': pid, 'birth': birth, 'launcher_pid': running['pid'], 'launcher_birth': running['birth'], 'binding': 'OBSERVED_OWNED_DESCENDANT_AND_SCRIPT_PIN', 'child_executable_independently_recorded': False}

def main():
    approval = json.loads((I / 'approval.json').read_bytes())
    assert approval['status'] == 'REVIEWED_SINGLE_SAVED_CONSUMPTION'
    for p, h in approval['pins'].items():
        assert sha(p) == h, p
    assert not D.exists(), 'saved consumption already consumed'
    D.mkdir()
    spec = importlib.util.spec_from_file_location('bounded_runner', R / 'council29_runner.py')
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    source_report = json.loads((S / 'report.json').read_bytes())
    sr = json.loads((S / 'producer/running.json').read_bytes())
    sc = json.loads((S / 'producer/completion.json').read_bytes())
    producer = W / 'tools/quality/road_scene_reference_index_ev112.py'
    consumer = W / 'tools/quality/verify_road_scene_reference_index_ev112.py'
    bound = process_binding(source_report, sr, sc, producer, approval['pins'][str(producer)])
    assert sc['rc'] == 2 and source_report['status'] == 'INCONCLUSIVE_REFERENCE_MISMATCH'
    put(D / 'source-binding.json', bound)
    c = W / 'tests/fixtures/road_b4b0/contract.json'
    job = {'id': 'road-b4b0-saved-consumer', 'command': [PY, '-I', '-X', 'utf8', str(consumer), '--contract', str(c), '--contract-sha', approval['contract_sha256'], '--report', str(S / 'report.json'), '--output', str(D / 'consumer.json')], 'cwd': str(W), 'out': str(D / 'consumer'), 'seconds': 60, 'max_bytes': 268435456, 'input_file': str(S / 'report.json')}
    put(D / 'job.json', job)
    completion = runner.run(job)
    result = {'status': 'INCONCLUSIVE_SAVED_CONSUMPTION', 'completion': completion, 'producer_rerun': False, 'build_ready': False, 'map_repaired': False}
    if completion['reason'] is None and (D / 'consumer.json').exists():
        report = json.loads((D / 'consumer.json').read_bytes())
        cr = json.loads((D / 'consumer/running.json').read_bytes())
        result['consumer_binding'] = process_binding(report, cr, completion, consumer, approval['pins'][str(consumer)])
        if completion['rc'] == 2 and report['status'] == 'VERIFIED_MISMATCH_DIAGNOSTIC':
            result['status'] = 'VERIFIED_MISMATCH_DIAGNOSTIC'
        result['consumer_sha256'] = sha(D / 'consumer.json')
    for p, h in approval['pins'].items():
        assert sha(p) == h, p
    result['source_report_sha256'] = sha(S / 'report.json')
    put(D / 'result.json', result)
    print(json.dumps(result))

if __name__ == '__main__':
    main()
