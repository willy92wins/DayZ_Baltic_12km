"""Bind a fresh, orderly-closed EV93 snapshot to its recorded server run."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil

HERE = Path(__file__).resolve().parent
RUN_ID = '1ed16d48-1352-4216-b5fe-31c77358b9fc'
NAME = 'baltic_ev93_selected_bank_v1.log'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def utc(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()


def require_fresh(stat, server_created):
    if stat.st_ctime < server_created or stat.st_mtime < server_created:
        raise ValueError('stale snapshot')


def main():
    provenance_path = HERE / 'native-run-provenance.json'
    provenance = json.loads(provenance_path.read_text(encoding='utf-8'))
    ref_path = HERE / 'native-reference.json'
    ref = json.loads(ref_path.read_text(encoding='utf-8'))
    run = provenance['run_identity']
    assert run['run_id'] == RUN_ID == provenance['launch']['run_id']
    assert provenance['launch']['status'] == 'succeeded'
    assert provenance['request']['mode'] == 'server'
    assert provenance['snapshot_source_was_absent_before_launch'] is True
    assert provenance['close']['run_id'] == RUN_ID
    assert provenance['close']['graceful'] and provenance['close']['run_retired']
    assert provenance['close']['exit_metrics_valid']
    coord = provenance['final_coordination']
    assert coord['owner'] is None and coord['self']['state'] == 'none'
    assert coord['pending_commands'] == 0 and not coord['occupied']
    assert len(run['processes']) == 1 and run['processes'][0]['role'] == 'server'
    created = utc(run['processes'][0]['creation_time_utc'])
    profile = Path(run['profiles'])
    source = profile / NAME
    assert source.resolve() == Path(provenance['snapshot_source_precheck']).resolve()
    stat = source.stat()
    require_fresh(stat, created)
    stale_rejected = False
    try:
        require_fresh(stat, max(stat.st_ctime, stat.st_mtime) + 1)
    except ValueError:
        stale_rejected = True
    assert stale_rejected, 'freshness gate accepted a snapshot from before the run'
    content = source.read_text(encoding='utf-8-sig')
    lines = content.splitlines()
    assert lines[0] == 'BALTIC_EV93_SELECTED_BANK_V1;BalticTrial;' + ref['terrain_sha256']
    assert not any(x.startswith('FAIL;') for x in lines)
    for prefix in ('GRID_END;', 'QUERY_END;', 'END;'):
        assert sum(x.startswith(prefix) for x in lines) == 1, prefix
    assert len([x for x in lines if x.startswith('G;')]) == 2048
    assert len([x for x in lines if x.startswith('P;')]) == 1212
    assert source.stat().st_mtime_ns == stat.st_mtime_ns, 'source still changing'
    rpts = [p for p in profile.glob('*.RPT') if p.stat().st_mtime >= created]
    matching = []
    for rpt in rpts:
        text = rpt.read_text(encoding='utf-8-sig', errors='replace')
        if str(Path(ref['mission'])) in text and '@DayZ_Baltic_EV93_SelectedBankPreviewV1' in text:
            matching.append((rpt, text))
    assert len(matching) == 1, 'ambiguous current run RPT'
    rpt, rpt_text = matching[0]
    assert 'Termination successfully completed' in rpt_text, 'orderly termination missing'
    destination = HERE / 'native-snapshot.log'
    assert not destination.exists(), 'refuse replacing prior runtime evidence'
    source_hash = sha(source)
    shutil.copyfile(source, destination)
    assert sha(destination) == source_hash == sha(source)
    excerpt = rpt_text.splitlines()[:42] + rpt_text.splitlines()[-20:]
    (HERE / 'runtime-rpt-excerpt.log').write_text('\n'.join(excerpt) + '\n', encoding='utf-8')
    receipt = {
        'status': 'CAPTURED_FRESH_CLOSED_SNAPSHOT_NOT_YET_VERIFIED',
        'run_id': RUN_ID, 'source': str(source), 'destination': str(destination),
        'source_sha256': source_hash, 'copied_sha256': sha(destination),
        'source_created_utc': datetime.fromtimestamp(stat.st_ctime, timezone.utc).isoformat(),
        'source_modified_utc': datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        'server_created_utc': run['processes'][0]['creation_time_utc'],
        'reference_sha256': sha(ref_path), 'provenance_sha256': sha(provenance_path),
        'collector_sha256': sha(__file__), 'rpt_path': str(rpt), 'rpt_sha256': sha(rpt),
        'rpt_excerpt_sha256': sha(HERE / 'runtime-rpt-excerpt.log'),
        'negative_stale_same_candidate_rejected': stale_rejected,
        'limits': ['Freshness and file provenance only; verify_native.py owns semantic readback checks.'],
    }
    (HERE / 'native-capture.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: receipt[k] for k in ('status', 'run_id', 'source_sha256')}))


if __name__ == '__main__':
    main()
