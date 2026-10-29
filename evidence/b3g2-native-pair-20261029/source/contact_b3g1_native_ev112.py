"""Consume B3G1 captured bytes after official lifecycle retirement, never R0 CLI."""
from pathlib import Path
import re,ntpath
from datetime import datetime,timezone
import contact_pair_b3g_binding_ev112 as old
import contact_pair_b3g1_receipts_ev112 as delta


def script_health(raw, source, host, created, written, checked):
    old.require(isinstance(raw,bytes) and len(raw)<=20*1024**2,'script_size')
    old.require(old.norm(ntpath.dirname(source))==old.norm(host['profiles'])
                and re.fullmatch(r'script_\d{4}-\d\d-\d\d_\d\d-\d\d-\d\d\.log',ntpath.basename(source)), 'script_location')
    birth=delta.utc(host['created_utc']);c=delta.utc(created);m=delta.utc(written);t=delta.utc(checked)
    old.require(birth<=c<=m<=t,'script_freshness')
    text=raw.decode('utf-8-sig',errors='replace')
    match=re.search(r'started at .*\((\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) UTC\)',text)
    old.require(match is not None,'script_header')
    stamp=datetime.strptime(match[1],'%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    old.require(-1<=(stamp-birth).total_seconds() and stamp<=t,'script_header_time')
    old.require(not re.search(r'SCRIPT\s*\(E\)|Can.t compile mission init script',text),'native_script_error')
    return dict(status='FRESH_SCRIPT_WITHOUT_RECORDED_ERROR',bytes=len(raw))


def consume_bound(root,seal):
    root=Path(root);old.require(not(root/'result.json').exists(),'result_consumed')
    d=old.files(root,seal);launch=old.read(root/'launch.json')
    old.require(launch['accepted_sha256']==seal,'launch_seal')
    names=('host-identity.json','host-after.json','mcp-identity.json','log-capture.json','cleanup.json')
    host,after,mcp,capture,cleanup=[old.read(root/n) for n in names]
    window=old.read(root/'capture-window.json');post=old.read(root/'script-at-capture.json')
    readiness=old.read(root/'readiness.json');adoption=old.read(root/'adoption.json');heartbeats=old.read(root/'heartbeats.json')
    preflight=old.read(root/'preflight.json')
    old.require(preflight['status']=='succeeded' and preflight['preflight'] is True and not preflight['error_code'],'preflight_result')
    old.require(preflight['request']=={**launch['request'],'preflight':True} and delta.utc(preflight['at'])<=delta.utc(adoption['at']),'preflight_binding')
    continuity(launch,window,readiness,adoption,heartbeats,cleanup,old.read(root/'outcome.json'))
    old.require(old.sha(root/'script-before.log')==window['script_log_sha256'],'script_before_hash')
    old.require(old.sha(root/'script-at-capture.log')==post['sha256'],'script_post_hash')
    old.require(post['source']==window['script_source'],'script_file_changed')
    script_health((root/'script-before.log').read_bytes(),window['script_source'],host,
                  window['script_created_utc'],window['script_last_write_utc'],window['script_log_checked_utc'])
    script_health((root/'script-at-capture.log').read_bytes(),post['source'],host,
                  window['script_created_utc'],post['last_write_utc'],post['checked_utc'])
    old.require(delta.utc(window['capture_started_utc'])<=delta.utc(post['checked_utc'])<=delta.utc(window['capture_ended_utc']),'post_script_window')
    delta.identity(d,launch,host,after,mcp,capture,cleanup,old.sha(root/'native.log'),window)
    result=old.consume((root/'native.log').read_text(encoding='utf-8-sig'),Path(d['csv']).read_text(encoding='ascii'),old.read(d['frozen']),old.read(d['original']))
    result['adapter']['raw_file_sha256']=old.sha(root/'native.log')
    inputs=(*names,'capture-window.json','script-at-capture.json','script-before.log','script-at-capture.log','launch.json','native.log','accepted.json','deployment.json','readiness.json','adoption.json','heartbeats.json','outcome.json','preflight.json')
    result.update(identity_bound=True,run_id=launch['run_id'],arm=d['arm'],deployment_sha256=old.sha(root/'deployment.json'),inputs={str(root/n):old.sha(root/n) for n in inputs})
    return result


def continuity(launch,window,ready,adopt,hb,cleanup,outcome):
    run=launch['run_id']
    old.require(all(r.get('run_id')==run for r in (ready,adopt,outcome)),'continuity_run')
    old.require(ready['ready_utc']==window['ready_utc'] or delta.utc(ready['ready_utc'])==delta.utc(window['ready_utc']),'ready_binding')
    old.require(delta.utc(ready['capture_deadline_utc'])==delta.utc(window['capture_deadline_utc']),'deadline_binding')
    old.require(adopt['status']=='OWN_RUN_ADOPTED' and outcome['status']=='CAPTURED_PENDING_CONSUMER','continuity_status')
    old.require(hb['failure'] is None and hb['events'] and all(x['ok'] is True for x in hb['events']),'heartbeat_failure')
    stamps=[delta.utc(x['at']) for x in hb['events']]
    # The heartbeat task may complete its first call before adoption receipt write.
    a=delta.utc(adopt['at']);end=delta.utc(cleanup['heartbeat_ended_utc'])
    old.require(delta.utc(window['capture_ended_utc'])<=delta.utc(cleanup['closed_utc'])<=end,'retirement_clock')
    old.require(abs((stamps[0]-a).total_seconds())<=20 and a<=delta.utc(ready['ready_utc'])<=end,'heartbeat_adoption')
    old.require(stamps[0]<=delta.utc(window['capture_started_utc']) and stamps[-1]<=end,'heartbeat_bounds')
    old.require(all(0<=(y-x).total_seconds()<=20 for x,y in zip(stamps,stamps[1:]+[end])),'heartbeat_gap')
