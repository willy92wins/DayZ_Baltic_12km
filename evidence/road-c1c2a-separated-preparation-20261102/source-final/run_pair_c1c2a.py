"""One-shot owned-process supervisor; byte preparation and observer only."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
sys.path.insert(0,'E:/DayZ-Baltic-Build/shape-repair-20261025/dry-road-build-dependencies-20261028')
import psutil
def save(p,v):
    with Path(p).open('xb') as f:f.write((json.dumps(v,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
def hashrow(p):
    p=Path(p);s=p.stat();i=lambda t:[t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns];h=hashlib.sha256();n=0
    if s.st_size>33554432:raise ValueError('METADATA_CAP')
    with p.open('rb') as f:
        if i(os.fstat(f.fileno()))!=i(s):raise ValueError('IDENTITY')
        while True:
            b=f.read(1048576)
            if not b:break
            n+=len(b)
            if n>33554432:raise ValueError('METADATA_CAP')
            h.update(b)
        if i(os.fstat(f.fileno()))!=i(s):raise ValueError('IDENTITY')
    if i(p.stat())!=i(s) or n!=s.st_size:raise ValueError('IDENTITY')
    return {'bytes':n,'sha256':h.hexdigest(),'identity':i(s)}
def run(command,cwd,dest,seconds,rsscap,diskroot=None):
    dest=Path(dest);dest.mkdir();start=time.monotonic();owned={};peak=0;diskpeak=0;reason=None;nextdisk=0
    with (dest/'stdout').open('xb') as stdout,(dest/'stderr').open('xb') as stderr:
        child=subprocess.Popen(command,cwd=cwd,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,creationflags=0x08000000)
        p=psutil.Process(child.pid);owned[p.pid]=p.create_time();birth=owned[p.pid]
        save(dest/'running.json',{'command':command,'root_pid':p.pid,'root_birth':birth,'seconds':seconds})
        def live():
            result=[]
            for pid,t in list(owned.items()):
                try:
                    q=psutil.Process(pid)
                    if q.create_time()==t and q.is_running():result.append(q)
                except psutil.NoSuchProcess:pass
            return result
        try:
            while True:
                for q in live():
                    try:
                        for node in q.children(recursive=True):owned[node.pid]=node.create_time()
                    except psutil.NoSuchProcess:pass
                active=live();rss=0
                for q in active:
                    try:rss+=q.memory_info().rss
                    except psutil.NoSuchProcess:pass
                peak=max(peak,rss);elapsed=time.monotonic()-start
                if elapsed>=seconds:reason='TIMEOUT';break
                if rss>rsscap:reason='MEMORY_LIMIT';break
                if diskroot and elapsed>=nextdisk and Path(diskroot).exists():
                    count=0;size=0
                    for file in Path(diskroot).rglob('*'):
                        count+=1
                        if count>32768:raise ValueError('ENTRY_CAP')
                        if file.is_file():size+=file.stat().st_size
                    diskpeak=max(size,diskpeak);nextdisk=elapsed+1
                    if size>2147483648:reason='DISK_LIMIT';break
                if any((dest/n).stat().st_size>33554432 for n in ['stdout','stderr']):reason='STREAM_CAP';break
                if child.poll() is not None and not active:break
                time.sleep(.10)
        except Exception as e:reason='SUPERVISOR:'+type(e).__name__+':'+str(e)
        finally:
            for q in reversed(live()):
                try:
                    if q.create_time()==owned[q.pid]:q.kill()
                except psutil.NoSuchProcess:pass
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:reason='DRAIN_TIMEOUT'
        retired=not live()
    r={'command':command,'root_pid':child.pid,'root_birth':birth,'rc':child.returncode,'reason':reason,'seconds':time.monotonic()-start,'peak_rss':peak,'observed_disk_peak':diskpeak,'identities':owned,'owned_retired':retired,'stdout':{'path':str(dest/'stdout'),**hashrow(dest/'stdout')},'stderr':{'path':str(dest/'stderr'),**hashrow(dest/'stderr')}}
    save(dest/'completion.json',r);return r
def main():
    config_path=Path(sys.argv[1]);cfg=json.loads(config_path.read_bytes());out=Path(cfg['out']);out.mkdir();begin=time.monotonic();contract=Path(cfg['contract']);data=contract.read_bytes()
    assert hashlib.sha256(data).hexdigest()==cfg['contract_sha256'];c=json.loads(data);root=Path(c['root']);assert not root.exists()
    for role in ['producer','consumer']:
        assert hashrow(cfg[role]['path'])['sha256']==cfg[role]['sha256']
    command=[sys.executable,'-I','-X','utf8',cfg['producer']['path'],'--contract',str(contract),'--sha',cfg['contract_sha256']]
    r=run(command,str(out),out/'producer',min(360,540-(time.monotonic()-begin)),536870912,root)
    assert r['owned_retired'];meta={p.name:hashrow(p) for p in (root/'meta').iterdir() if p.is_file()} if (root/'meta').exists() else {}
    obs={'schema':'c1c2a-external-observation.v1','contract_sha256':cfg['contract_sha256'],'contract_path':str(contract),'producer_code':cfg['producer'],'command':command,'completion':r,'owned_retired':True,'meta':meta}
    save(out/'external-observation.json',obs);left=540-(time.monotonic()-begin)
    if left<180:save(out/'result.json',{'status':'INCONCLUSIVE_CONSUMER_NOT_LAUNCHED','remaining':left});return
    cmd=[sys.executable,'-I','-X','utf8',cfg['consumer']['path'],'--contract',str(contract),'--sha',cfg['contract_sha256'],'--observation',str(out/'external-observation.json'),'--observation-sha',hashrow(out/'external-observation.json')['sha256'],'--output',str(out/'consumer.json')]
    q=run(cmd,str(out),out/'consumer',180,268435456)
    result={'status':'PAIR_FINISHED','producer':r,'consumer':q,'elapsed':time.monotonic()-begin};save(out/'result.json',result);print(json.dumps({'status':result['status'],'producer_rc':r['rc'],'consumer_rc':q['rc'],'seconds':result['elapsed']}))
if __name__=='__main__':main()
