"""B1 provenance checks. Physical decisions stay in the unchanged pure consumer."""
from pathlib import Path
from datetime import datetime
import hashlib
import json
import ntpath
import math
from water_query_diag_b1_ev112 import require, check_csv, source_points, consume

def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def verify(mapping):
    require(bool(mapping), 'empty_manifest')
    for path, digest in mapping.items():
        require(sha(path) == digest, 'input_drift:' + path)

def norm(path):
    return ntpath.normcase(ntpath.normpath(str(path)))

def instant(value):
    t = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(t.tzinfo is not None, 'naive_time')
    return t

def package_set(packages):
    normalized = {norm(p): h for p, h in packages.items()}
    require(len(normalized) == len(packages) == 4, 'package_cardinality')
    return normalized

def files(root, accepted_sha):
    root = Path(root)
    require(sha(root/'accepted.json') == accepted_sha, 'seal_drift')
    a = read(root/'accepted.json')
    require(a['status'] == 'B1_NATIVE_READY', 'not_accepted')
    require(str(root/'deployment.json') in a['inputs'], 'unsealed_deployment')
    verify(a['inputs'])
    d = read(root/'deployment.json')
    required = [d[k] for k in ('selected', 'original', 'csv', 'producer', 'engine')]
    required += list(d['packages'])
    require(all(p in d['inputs'] for p in required), 'incomplete_manifest')
    verify(d['inputs'])
    package_set(d['packages'])
    require(all(d['inputs'][p] == h for p, h in d['packages'].items()), 'unbound_package')
    require(norm(Path(d['producer']).parent) == norm(d['mission']) and
            norm(Path(d['csv']).parent) == norm(d['mission']), 'mission_files')
    check_csv(Path(d['csv']).read_text(encoding='ascii'), source_points(read(d['selected']), read(d['original'])))
    return d

def gate(root, accepted_sha):
    d = files(root, accepted_sha)
    require(not any((Path(root)/n).exists() for n in ('launch.json', 'result.json', 'native.log')), 'unit_consumed')
    return dict(status='PRE_FIFO_GATE_PASS', mission=d['mission'], mod=d['mod'], accepted_sha256=accepted_sha)

def identity(d, launch, host, after, mcp, capture, cleanup, native_sha):
    require(launch['status'] == 'succeeded', 'launch_failed')
    require(isinstance(cleanup.get('close'), dict), 'lifecycle_not_closed')
    run = launch['run_id']
    require(run and all(x == run for x in (host['run_id'], after['run_id'], mcp['run_id'],
            mcp['server_run_id'], cleanup['close']['run_id'])), 'run_binding')
    require(mcp['server_binding'] == 'BOUND' and mcp['version_state'] == 'ok' and
            math.isfinite(mcp['poll_age_s']) and 0 <= mcp['poll_age_s'] < 10, 'bridge_binding')
    procs = mcp['processes']
    require(len(procs) == 1 and procs[0]['role'] == 'server', 'process_count')
    require(procs[0]['pid'] == host['pid'] == after['pid'] == capture['pid'], 'process_binding')
    created = instant(procs[0]['creation_time_utc'])
    # Host emits 100 ns digits; psutil/MCP emits rounded microseconds. This is
    # process timestamp serialization (PS independently checks <=2 ms), never
    # a physical height/water/collision tolerance.
    require(all(abs((instant(v)-created).total_seconds()) <= .001 for v in
                (host['created_utc'], after['created_utc'], capture['created_utc'])), 'creation_binding')
    require(instant(capture['last_write_utc']) >= created, 'stale_log')
    require(all(x['state'] == 'not_started' for x in mcp['client_diagnostics']) and
            host['navmesh_data_server'] and after['navmesh_data_server'], 'runtime_mode')
    expected = package_set(d['packages'])
    for h in (host, after):
        require(h.get('file_patching') is False and h.get('server_mods') == [], 'external_source_mode')
        require(norm(h['mission_path']) == norm(d['mission']) and
                h['mission_sha256'] == d['inputs'][d['producer']], 'mission_binding')
        require(norm(h['executable']) == norm(d['engine']) and
                h['executable_file_sha256'] == d['inputs'][d['engine']], 'engine_binding')
        require(package_set(h['package_hashes']) == expected, 'package_binding')
    for key in ('profiles', 'host_raw_command_line_sha256', 'server_config', 'server_config_sha256'):
        require(host[key] == after[key], 'runtime_changed:' + key)
    require(norm(capture['source']) == norm(ntpath.join(host['profiles'], 'baltic_water_query_b1.log')), 'profile_log_binding')
    require(capture['count'] == 345 and capture['sha256'] == native_sha, 'log_binding')
    stopped = cleanup.get('stop')
    retired = cleanup['close']['run_retired'] or (stopped and stopped['run_id'] == run and stopped['status'] == 'succeeded')
    require(retired and cleanup['self']['state'] == 'none' and
            not cleanup['own_run_present'] and cleanup['pending_commands'] == 0 and
            not cleanup['cleanup_degraded'] and not cleanup['error'] and
            not cleanup['cleanup_error'], 'lifecycle_not_closed')

def consume_bound(root, accepted_sha):
    root = Path(root)
    require(not (root/'result.json').exists(), 'result_exists')
    d = files(root, accepted_sha)
    launch = read(root/'launch.json')
    require(launch['accepted_sha256'] == accepted_sha, 'launch_seal_binding')
    names = ('host-identity.json','host-after.json','mcp-identity.json','log-capture.json','cleanup.json')
    identity(d, launch, *[read(root/n) for n in names], sha(root/'native.log'))
    result = consume((root/'native.log').read_text(encoding='utf-8-sig'),
                     Path(d['csv']).read_text(encoding='ascii'), read(d['selected']), read(d['original']))
    paths = [root/n for n in (*names,'launch.json','native.log','accepted.json','deployment.json')]
    result.update(identity_bound=True, run_id=launch['run_id'],
                  inputs={str(p):sha(p) for p in paths},
                  limits_binding=['On-disk artifacts verified before/after own process; no in-memory PBO hash assertion.',
                                  'Original FAIL retained. No physical repair or visual acceptance.'])
    return result
