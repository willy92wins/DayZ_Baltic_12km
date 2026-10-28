"""B2 identity binder, with static census packages tied to native receipts."""
from pathlib import Path
import sys
import ntpath
import math
from water_query_native_b1_ev112 import sha, read, verify, norm, instant, package_set
from collision_native_b2_ev112 import require, source_points, csv_for, consume, match_pose, VECTOR_ERROR

VANILLA = {'plants.pbo','plants_bliss.pbo','structures_industrial.pbo','structures_roads.pbo','water.pbo'}
OWN = {'baltic_stream_pilot.pbo','narva_trial.pbo','baltic_water_v30.pbo'}


def static_binding(d, report):
    ref = {ntpath.basename(p['path']).lower():p['sha256'] for p in report['packages']}
    require(len(report['packages']) == len(ref) == 8 and set(ref) == VANILLA|OWN, 'census_packages')
    require(len(d['static_packages']) == 8, 'static_package_count')
    actual = {ntpath.basename(p).lower():h for p,h in d['static_packages'].items()}
    require(actual == ref, 'PACKAGE_DRIFT:census')
    mods = package_set(d['packages'])
    require({ntpath.basename(p).lower() for p in mods} == OWN|{'dayz_mcp.pbo'}, 'mod_names')
    vanilla = {}
    for name in VANILLA:
        path = norm(ntpath.join(ntpath.dirname(d['engine']),'Addons',name))
        require({norm(p):h for p,h in d['static_packages'].items()}.get(path) == ref[name], 'vanilla_install_path')
        vanilla[path] = ref[name]
    for path,digest in d['static_packages'].items():
        if ntpath.basename(path).lower() in OWN:
            require(mods.get(norm(path)) == digest, 'own_static_mod_binding')
    require(len(set(vanilla)|set(mods)) == 9, 'package_union')
    return vanilla


def files(root, accepted_sha):
    root = Path(root)
    require(sha(root/'accepted.json') == accepted_sha, 'seal_drift')
    a = read(root/'accepted.json')
    require(a['status'] == 'B2_NATIVE_READY', 'not_accepted')
    require(str(root/'deployment.json') in a['inputs'], 'unsealed_deployment')
    verify(a['inputs']);d = read(root/'deployment.json')
    required = [d[k] for k in ('original','frozen','hits','poses','report','wrp','config','csv','producer','engine')]
    required += list(d['packages']) + list(d['static_packages'])
    require(all(p in d['inputs'] for p in required), 'incomplete_manifest')
    verify(d['inputs'])
    require(all(d['inputs'][p] == h for p,h in {**d['packages'],**d['static_packages']}.items()), 'unbound_package')
    static_binding(d,read(d['report']))
    require(norm(Path(d['producer']).parent) == norm(d['mission']) and norm(Path(d['csv']).parent) == norm(d['mission']), 'mission_files')
    points = source_points(read(d['frozen']),read(d['original']))
    require(Path(d['csv']).read_text(encoding='ascii') == csv_for(points), 'csv_source_binding')
    return d


def gate(root, accepted_sha):
    d = files(root,accepted_sha)
    require(not any((Path(root)/n).exists() for n in ('launch.json','result.json','native.log')), 'unit_consumed')
    return dict(status='PRE_FIFO_GATE_PASS',mission=d['mission'],mod=d['mod'],accepted_sha256=accepted_sha)


def identity(d, launch, host, after, mcp, capture, cleanup, native_sha):
    require(launch['status'] == 'succeeded', 'launch_failed')
    require(isinstance(cleanup.get('close'),dict), 'lifecycle_not_closed')
    run = launch['run_id']
    require(run and all(x == run for x in (host['run_id'],after['run_id'],mcp['run_id'],mcp['server_run_id'],cleanup['close']['run_id'])), 'run_binding')
    require(mcp['server_binding'] == 'BOUND' and mcp['version_state'] == 'ok' and math.isfinite(mcp['poll_age_s']) and 0 <= mcp['poll_age_s'] < 10, 'bridge_binding')
    procs = mcp['processes']
    require(len(procs) == 1 and procs[0]['role'] == 'server', 'process_count')
    require(procs[0]['pid'] == host['pid'] == after['pid'] == capture['pid'], 'process_binding')
    created = instant(procs[0]['creation_time_utc'])
    require(all(abs((instant(v)-created).total_seconds()) <= .001 for v in (host['created_utc'],after['created_utc'],capture['created_utc'])), 'creation_binding')
    require(instant(capture['last_write_utc']) >= created, 'stale_log')
    require(bool(mcp['client_diagnostics']) and all(x['state'] == 'not_started' for x in mcp['client_diagnostics']) and host['navmesh_data_server'] and after['navmesh_data_server'], 'runtime_mode')
    expected = package_set(d['packages'])
    vanilla = static_binding(d,read(d['report']))
    for h in (host,after):
        require(h.get('file_patching') is False and h.get('server_mods') == [], 'external_source_mode')
        require(norm(h['mission_path']) == norm(d['mission']) and h['mission_sha256'] == d['inputs'][d['producer']], 'mission_binding')
        require(norm(h['executable']) == norm(d['engine']) and h['executable_file_sha256'] == d['inputs'][d['engine']], 'engine_binding')
        require(package_set(h['package_hashes']) == expected, 'package_binding')
        actual = {norm(p):v for p,v in h['vanilla_hashes'].items()}
        require(len(h['vanilla_hashes']) == len(actual) == 5 and actual == vanilla, 'PACKAGE_DRIFT:vanilla')
    for key in ('profiles','host_raw_command_line_sha256','server_config','server_config_sha256'):
        require(host[key] == after[key], 'runtime_changed:'+key)
    require(norm(capture['source']) == norm(ntpath.join(host['profiles'],'baltic_collision_b2.log')), 'profile_log_binding')
    require(capture['count'] == 270 and capture['sha256'] == native_sha, 'log_binding')
    stopped = cleanup.get('stop')
    retired = cleanup['close']['run_retired'] or (stopped and stopped['run_id'] == run and stopped['status'] == 'succeeded')
    require(retired and cleanup['self']['state'] == 'none' and not cleanup['own_run_present'] and cleanup['pending_commands'] == 0 and not cleanup['cleanup_degraded'] and not cleanup['error'] and not cleanup['cleanup_error'], 'lifecycle_not_closed')


class SceneIndex:
    """Full WRP population by model, with formatting-only position matching."""
    def __init__(self, d):
        import numpy as np
        sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'terrain'))
        from package_visual_forest_ev112 import compiled_arrays
        from collision_native_b2_ev112 import norm as modelnorm
        config = read(d['config'])
        self.scene,reader = compiled_arrays(Path(d['wrp']).read_bytes(),config['anchor'])
        s = self.scene
        require(len(s['ids']) == 2578398 and len(s['names']) == 5509, 'scene_coverage')
        self.names = {modelnorm(n):i for i,n in enumerate(s['names'])}
        self.order = np.argsort(s['mi'],kind='stable')
        self.starts = np.r_[0,np.cumsum(np.bincount(s['mi'],minlength=len(s['names'])))]
        self.cache = {}
        self.np = np
        # Candidate poses are bound against the independent full scene, not trusted copies.
        for p in read(d['poses']):
            index = np.flatnonzero(s['ids'] == p['id'])
            require(len(index) == 1 and modelnorm(s['names'][s['mi'][index[0]]]) == p['model'] and np.array_equal(s['mat'][index[0]],p['matrix']), 'candidate_pose_binding')

    def __call__(self, obj):
        from collision_native_b2_ev112 import norm as modelnorm
        key = (obj['valid'],modelnorm(obj['shape']),tuple(obj['pos']),tuple(obj.get('matrix',[])))
        if key not in self.cache:
            mi = self.names.get(key[1]); candidates = []
            if mi is not None and obj['valid']:
                indices = self.order[self.starts[mi]:self.starts[mi+1]]
                delta = self.np.abs(self.scene['mat'][indices,9:].astype(float)-obj['pos'])
                rows = indices[(delta <= VECTOR_ERROR).all(1)]
                candidates = [dict(id=int(self.scene['ids'][i]),matrix=self.scene['mat'][i].astype(float).tolist()) for i in rows]
            self.cache[key] = match_pose(obj,candidates)
        return self.cache[key]


def consume_bound(root, accepted_sha):
    root = Path(root)
    require(not (root/'result.json').exists(), 'result_exists')
    d = files(root,accepted_sha);launch = read(root/'launch.json')
    require(launch['accepted_sha256'] == accepted_sha, 'launch_seal_binding')
    names = ('host-identity.json','host-after.json','mcp-identity.json','log-capture.json','cleanup.json')
    identity(d,launch,*[read(root/n) for n in names],sha(root/'native.log'))
    result = consume((root/'native.log').read_text(encoding='utf-8-sig'),Path(d['csv']).read_text(encoding='ascii'),
                     read(d['frozen']),read(d['original']),read(d['hits']),[p['id'] for p in read(d['poses'])],SceneIndex(d))
    result.update(identity_bound=True,run_id=launch['run_id'],inputs={str(root/n):sha(root/n) for n in (*names,'launch.json','native.log','accepted.json','deployment.json')},
        limits_binding=['Pre/post on-disk package identities, not in-memory hashes.','No historical vanilla identity inferred for B1.'])
    return result
