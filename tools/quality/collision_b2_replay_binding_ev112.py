"""Versioned replay of one rejected B2 capture. Original artifacts stay immutable."""
from pathlib import Path
import ntpath
from collision_native_b2_binding_ev112 import (read,sha,verify,require,identity,
                                             SceneIndex,source_points,csv_for)
from collision_native_b2_ev112 import consume

SUPERSEDED = {'collision_native_b2_ev112.py','test_collision_native_b2_ev112.py'}


def verify_superseded(inputs, archives, new_sources):
    require(len(archives) == 2 and set(archives) == set(new_sources) and
            {ntpath.basename(p) for p in archives} == SUPERSEDED, 'supersession_scope')
    require(set(archives) <= set(inputs), 'supersession_input_missing')
    for path,digest in inputs.items():
        if path in archives:
            a=archives[path]
            require(a['sha256'] == digest and sha(a['path']) == digest, 'historical_source_drift')
            require(sha(path) == new_sources[path], 'replay_source_drift')
        else:require(sha(path) == digest, 'historical_input_drift:'+path)


def replay(root, accepted_sha):
    root=Path(root)
    require(not (root/'result.json').exists(), 'replay_consumed')
    require(sha(root/'accepted.json') == accepted_sha, 'replay_seal_drift')
    a=read(root/'accepted.json');require(a['status'] == 'B2_REPLAY_READY','replay_unreviewed')
    require(a['receipt'] in a['inputs'] and str(Path(__file__)) in a['inputs'] and
            all(p in a['inputs'] for p in a['new_sources']), 'replay_manifest_unsealed')
    verify(a['inputs'])
    receipt=read(a['receipt']);require(receipt['status'] == 'IDENTITY_VERIFIED_CONSUMER_REJECTED_ENUM','original_rejection_missing')
    verify(receipt['inputs'])
    old=Path(a['original_root'])
    require(sha(old/'accepted.json') == receipt['original_accepted_sha256'], 'original_seal_drift')
    old_a=read(old/'accepted.json');require(old_a['status']=='B2_NATIVE_READY','original_not_ready')
    verify(old_a['inputs']);d=read(old/'deployment.json')
    require(str(old/'deployment.json') in old_a['inputs'],'original_deployment_unbound')
    expected_sources={str(Path(__file__).with_name(n)) for n in SUPERSEDED}
    require(set(a['new_sources']) == expected_sources,'replay_source_scope')
    verify_superseded(d['inputs'],receipt['archives'],a['new_sources'])
    names=('host-identity.json','host-after.json','mcp-identity.json','log-capture.json','cleanup.json')
    launch=read(old/'launch.json')
    require(launch['accepted_sha256']==receipt['original_accepted_sha256'] and launch['run_id']==receipt['run_id'],'original_launch_binding')
    identity(d,launch,*[read(old/n) for n in names],sha(old/'native.log'))
    require(Path(d['csv']).read_text(encoding='ascii')==csv_for(source_points(read(d['frozen']),read(d['original']))),'original_csv_binding')
    result=consume((old/'native.log').read_text(encoding='utf-8-sig'),Path(d['csv']).read_text(encoding='ascii'),
                   read(d['frozen']),read(d['original']),read(d['hits']),[p['id'] for p in read(d['poses'])],SceneIndex(d))
    result.update(identity_bound=True,run_id=launch['run_id'],replay=True,original_rejection=receipt['original_rejection'],
                  original_accepted_sha256=receipt['original_accepted_sha256'],replay_accepted_sha256=accepted_sha,
                  native_log_sha256=sha(old/'native.log'),limits_binding=[
                      'Original identity rechecked with only two explicitly archived source supersessions.',
                      'No additional native run. No scripts.pbo historical identity assertion.',
                      'The script representation does not certify the engine integer or layer semantics.'])
    return result
