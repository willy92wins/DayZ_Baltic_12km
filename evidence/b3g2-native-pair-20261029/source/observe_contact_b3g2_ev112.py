"""One bounded poll; owns only new receipts, never the game or its file handles."""
import argparse,json,os,sys
from pathlib import Path
from datetime import timedelta
import shared_log_b3g2_ev112 as s
from contact_pair_b3g_ev112 import require
from contact_pair_b3g1_receipts_ev112 import utc

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(root,name,value):
    raw=value if isinstance(value,bytes) else (json.dumps(value,indent=2)+'\n').encode()
    with (root/name).open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())

def alive(host):
    sys.path.insert(0,'E:/DayZ-Baltic-Build/shape-repair-20261025/dry-road-build-dependencies-20261028')
    import psutil
    process=psutil.Process(host['pid'])
    require(process.is_running() and abs(process.create_time()-utc(host['created_utc']).timestamp())<=.001,'process_identity_changed')

def native_health(raw,meta,host):
    import ntpath
    s.metadata(raw,meta)
    norm=lambda p:ntpath.normcase(ntpath.normpath(p))
    require(norm(meta['source'])==norm(ntpath.join(host['profiles'],'baltic_contact_b3g.log')),'native_location')
    require(utc(meta['last_write_utc'])>=utc(host['created_utc']),'stale_native')
    lines=raw.decode('utf-8-sig').splitlines()
    if not lines:return None
    if len(lines)==1 and not raw.endswith(b'\n') and 'BALTIC_CONTACT_B3G;BalticTrial'.startswith(lines[0]):return None
    require(lines and lines[0]=='BALTIC_CONTACT_B3G;BalticTrial','native_header')
    require(not any(x.startswith('FAIL;') for x in lines),'producer_failed')
    if lines[-1]!='END;270':return None
    require(sum(x.startswith('Q;') for x in lines)==270,'native_Q_count')
    return 270

def observe(root,ready):
    root=Path(root);require(not (root/'native.log').exists(),'capture_consumed')
    require(not (root/'script-failure.json').exists(),'script_failure_present')
    host=read(root/'host-identity.json');dep=read(root/'deployment.json')
    golden=s.load_golden(dep['golden']);require(s.digest(Path(dep['golden']).read_bytes())==dep['inputs'][dep['golden']],'golden_pin')
    deadline=utc(ready)+timedelta(seconds=180)
    require(utc(s.now())<=deadline,'capture_deadline');alive(host)
    # Fresh directory metadata selects candidates only. The read handle supplies identity.
    logs=[]
    for p in Path(host['profiles']).glob('script_*.log'):
        st=p.stat()
        if getattr(st,'st_birthtime',st.st_ctime)>=utc(host['created_utc']).timestamp():logs.append(p)
    require(len(logs)==1,'unique_fresh_script')
    script,sm=s.snapshot(logs[0])
    try:diagnostic=s.health(script,sm,host,golden)
    except Exception:
        save(root,'script-failure.log',script);save(root,'script-failure.json',sm);raise
    if not (root/'capture-start.json').exists():
        save(root,'script-before.log',script);save(root,'script-before.json',sm)
        save(root,'script-before-diagnostic.json',diagnostic)
        save(root,'capture-start.json',dict(basis='HOST_UTC_FIRST_SERVER_BOUND_VERSION_OK_FRESH',run_id=host['run_id'],pid=host['pid'],
             ready_utc=ready,capture_started_utc=s.now(),capture_deadline_utc=deadline.isoformat(),script_log_checked_utc=sm['checked_utc'],
             script_log_sha256=sm['sha256'],mission_error_before_capture=False,script_source=sm['source'],script_created_utc=sm['created_utc'],script_last_write_utc=sm['last_write_utc']))
    else:require(read(root/'script-before.json')['file_id']==sm['file_id'],'script_rotated')
    path=Path(host['profiles'])/'baltic_contact_b3g.log'
    if not path.exists():return dict(status='PENDING_NATIVE_LOG')
    native,nm=s.snapshot(path);count=native_health(native,nm,host)
    if not (root/'native-first.json').exists():save(root,'native-first.json',nm)
    else:require(read(root/'native-first.json')['file_id']==nm['file_id'],'native_rotated')
    if count is None:return dict(status='PENDING_SAMPLES',bytes=len(native))
    second,second_meta=s.snapshot(path);s.stable_pair((native,nm),(second,second_meta))
    post,pm=s.snapshot(logs[0]);pd=s.health(post,pm,host,golden)
    require(pm['file_id']==read(root/'script-before.json')['file_id'],'script_rotated')
    # Retain the entire earlier prefix; same FileID cannot excuse a rewrite.
    require(post.startswith((root/'script-before.log').read_bytes()),'script_prefix_changed')
    alive(host);ended=s.now();require(utc(ended)<=deadline,'capture_deadline')
    save(root,'native.log',native);save(root,'native-second.log',second)
    save(root,'native-snapshots.json',{'first':nm,'second':second_meta})
    save(root,'script-at-capture.log',post);save(root,'script-at-capture.json',pm);save(root,'script-at-capture-diagnostic.json',pd)
    save(root,'capture-window.json',{**read(root/'capture-start.json'),'capture_ended_utc':ended})
    save(root,'log-capture.json',dict(status='CAPTURED_NOT_JUDGED',pid=host['pid'],created_utc=host['created_utc'],count=count,source=nm['source'],last_write_utc=nm['last_write_utc'],sha256=nm['sha256'],captured_utc=ended))
    return dict(status='CAPTURED_NOT_JUDGED',count=count,sha256=nm['sha256'])

def main():
    p=argparse.ArgumentParser();p.add_argument('--directory',required=True,type=Path);p.add_argument('--ready',required=True);a=p.parse_args()
    print(json.dumps(observe(a.directory,a.ready)))
if __name__=='__main__':main()
