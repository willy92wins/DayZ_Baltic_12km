"""B3G2 consumer: reclassifies exact captured bytes and binds shared snapshots."""
from pathlib import Path
import contact_pair_b3g_binding_ev112 as old
import contact_pair_b3g1_receipts_ev112 as delta
from contact_b3g1_native_ev112 import continuity
import shared_log_b3g2_ev112 as s
from observe_contact_b3g2_ev112 import native_health

def snapshots(root,host,window,golden):
    root=Path(root);before=(root/'script-before.log').read_bytes();post=(root/'script-at-capture.log').read_bytes()
    bm=old.read(root/'script-before.json');pm=old.read(root/'script-at-capture.json')
    old.require(host['profile_filesystem']=='NTFS','profile_filesystem')
    known=[]
    for raw,meta,name in ((before,bm,'before'),(post,pm,'at-capture')):
        d=s.health(raw,meta,host,golden);old.require(d==old.read(root/('script-'+name+'-diagnostic.json')),'diagnostic_binding');known.append(d)
    old.require(bm['file_id']==pm['file_id'] and bm['source']==pm['source'] and post.startswith(before),'script_continuity')
    for key,mk in (('script_log_sha256','sha256'),('script_source','source'),('script_created_utc','created_utc'),('script_last_write_utc','last_write_utc'),('script_log_checked_utc','checked_utc')):
        old.require(window[key]==bm[mk],'script_window_binding')
    old.require(delta.utc(window['capture_started_utc'])<=delta.utc(pm['checked_utc'])<=delta.utc(window['capture_ended_utc']),'post_script_window')
    raw=(root/'native.log').read_bytes();second=(root/'native-second.log').read_bytes();m=old.read(root/'native-snapshots.json')
    for data,meta in ((raw,m['first']),(second,m['second'])):old.require(native_health(data,meta,host)==270,'native_complete')
    s.stable_pair((raw,m['first']),(second,m['second']))
    old.require(old.read(root/'native-first.json')['file_id']==m['first']['file_id'],'native_poll_continuity')
    old.require(delta.utc(window['capture_started_utc'])<=delta.utc(m['first']['checked_utc'])<=delta.utc(m['second']['checked_utc'])<=delta.utc(pm['checked_utc']),'snapshot_sequence')
    c=old.read(root/'log-capture.json')
    old.require(all(c[k]==m['first'][k] for k in ('source','sha256','last_write_utc')),'native_capture_binding')
    return known

def consume_bound(root,seal):
    root=Path(root);old.require(not(root/'result.json').exists(),'result_consumed');d=old.files(root,seal)
    old.require(not (root/'script-failure.json').exists(),'script_failure_present')
    golden=s.load_golden(d['golden']);old.require(str(d['golden']) in d['inputs'],'unbound_golden')
    launch=old.read(root/'launch.json');old.require(launch['accepted_sha256']==seal,'launch_seal')
    names=('host-identity.json','host-after.json','mcp-identity.json','log-capture.json','cleanup.json')
    host,after,mcp,capture,cleanup=[old.read(root/n) for n in names]
    old.require(after['profile_filesystem']==host['profile_filesystem']=='NTFS','filesystem_changed')
    window=old.read(root/'capture-window.json');preflight=old.read(root/'preflight.json');adoption=old.read(root/'adoption.json')
    old.require(preflight['status']=='succeeded' and preflight['preflight'] is True and not preflight['error_code'],'preflight_result')
    old.require(preflight['request']=={**launch['request'],'preflight':True} and delta.utc(preflight['at'])<=delta.utc(adoption['at']),'preflight_binding')
    continuity(launch,window,old.read(root/'readiness.json'),adoption,old.read(root/'heartbeats.json'),cleanup,old.read(root/'outcome.json'))
    diagnostics=snapshots(root,host,window,golden)
    delta.identity(d,launch,host,after,mcp,capture,cleanup,old.sha(root/'native.log'),window)
    result=old.consume((root/'native.log').read_text(encoding='utf-8-sig'),Path(d['csv']).read_text(encoding='ascii'),old.read(d['frozen']),old.read(d['original']))
    result['adapter']['raw_file_sha256']=old.sha(root/'native.log')
    inputs=(*names,'capture-window.json','script-at-capture.json','script-before.json','script-before.log','script-at-capture.log','script-before-diagnostic.json','script-at-capture-diagnostic.json','native-first.json','native-snapshots.json','native-second.log','launch.json','native.log','accepted.json','deployment.json','readiness.json','adoption.json','heartbeats.json','outcome.json','preflight.json')
    result.update(identity_bound=True,run_id=launch['run_id'],arm=d['arm'],deployment_sha256=old.sha(root/'deployment.json'),inputs={str(root/n):old.sha(root/n) for n in inputs},script_diagnostics=diagnostics,
                  limitations=['Known optional debug-profile DumpStack retained when present; no global causal or visual acceptance.'])
    return result
