"""One bounded read-only discovery; never imports preflight or build helpers."""
from pathlib import Path
import argparse,ctypes,hashlib,json,os,re,subprocess,sys,threading,time,traceback
from ctypes import wintypes

ROOT=Path('E:/DayZ-Baltic-Build/shape-repair-20261025')
RECEIPTS=(('old',ROOT/'dry-road-build-preflight-20261028/report.json','354fbb2e5edea80e88521f02cd135ac2f6a7608a14085af5cc088395a542e68e'),
          ('prior',ROOT/'prism-b3-binary-replay-20261028/contract-r1.json','5df5009176342658eb7b31c7c099e643c9e99cc898d2a14f319858a9df391244'))
SOURCES=(Path('C:/Users/guill/.agents/skills/dayz-preflight/preflight.py'),ROOT/'dry-road-build-preflight-20261028/preflight_syntax_repaired.py')
TOOLS=('Bin/AddonBuilder/AddonBuilder.exe','Bin/PboUtils/FileBank.exe','Bin/CfgConvert/CfgConvert.exe')
LIMIT='Read timings only; neither historical causality nor complete preflight/native readiness.'

class ContractError(ValueError):pass
class HashMismatch(ValueError):pass
def require(ok,label):
    if not ok:raise ContractError(label)
def key(p):return os.path.normcase(os.path.abspath(p))
def digest_valid(h):return isinstance(h,str) and re.fullmatch('[0-9a-f]{64}',h) is not None
def dump(path,value):
    with Path(path).open('w',encoding='utf-8') as f:
        json.dump(value,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())

class Events:
    def __init__(self,path):self.path=path;self.start=time.monotonic()
    def __call__(self,phase,**data):
        with self.path.open('a',encoding='utf-8') as f:
            f.write(json.dumps(dict(phase=phase,seconds=time.monotonic()-self.start,**data),allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())

def read_hash(path,label,emit,keep=False):
    start=time.monotonic();emit('read_start',label=label,path=str(path));h=hashlib.sha256();size=0;blocks=[]
    with Path(path).open('rb') as f:
        while True:
            block=f.read(4<<20)
            if not block:break
            if size==0:emit('first_block',label=label,bytes=len(block))
            h.update(block);size+=len(block)
            if keep:blocks.append(block)
    row=dict(label=label,path=str(path),sha256=h.hexdigest(),bytes=size,seconds=time.monotonic()-start)
    emit('read_done',**row);return row,b''.join(blocks) if keep else None

def load_receipts(receipts,out,emit):
    result={}
    require([r[0] for r in receipts]==['old','prior'],'receipt_names')
    for name,path,expected in receipts:
        require(digest_valid(expected),'receipt_expected_hash')
        row,data=read_hash(path,'receipt_'+name,emit,True)
        require(row['sha256']==expected,'receipt_hash:'+name)
        (out/('input-'+name+'.json')).write_bytes(data)
        try:value=json.loads(data)
        except (ValueError,UnicodeError) as e:raise ContractError('receipt_json:'+name) from e
        require(isinstance(value,dict),'receipt_object:'+name);result[name]=value
    return result

def jobs_from_receipts(old,prior,sources,config):
    require(isinstance(old.get('tools_root'),str),'tools_root')
    root=Path(old['tools_root']);require(root.is_absolute(),'relative_tools_root')
    require(key(old.get('original_source',''))==key(sources[0]),'unexpected_preflight_source')
    raw=old.get('tools_sha256');pins=prior.get('pins')
    require(isinstance(raw,dict) and isinstance(pins,dict),'receipt_maps')
    expected=[root/n for n in TOOLS];normalized={key(p):h for p,h in raw.items()}
    require(len(normalized)==len(raw)==3 and set(normalized)=={key(p) for p in expected},'unexpected_tool_path')
    result=[('source_original',sources[0],old.get('original_sha256')),('source_archived',sources[1],old.get('local_sha256'))]
    result +=[(p.name,p,normalized[key(p)]) for p in expected]
    for p in (root/'Bin/Binarize/Binarize.exe',config):
        require(str(p) in pins,'missing_prior_pin:'+str(p))
        result +=[(p.name+':'+str(i),p,pins[str(p)]) for i in (1,2)]
    require(len(result)==9 and all(digest_valid(h) for _,_,h in result),'job_hashes')
    return result

def discover(receipts,out,sources,config,dirs,emit):
    start=time.monotonic();docs=load_receipts(receipts,out,emit)
    jobs=jobs_from_receipts(docs['old'],docs['prior'],sources,config)
    for p in dirs:
        stamp=time.monotonic();emit('directory_start',path=str(p));present=Path(p).is_dir()
        emit('directory_done',path=str(p),is_directory=present,seconds_spent=time.monotonic()-stamp)
        require(present,'missing_directory:'+str(p))
    rows=[]
    for label,p,expected in jobs:
        row,_=read_hash(p,label,emit);row['expected_sha256']=expected;rows.append(row)
        if row['sha256']!=expected:
            emit('hash_mismatch',**row);raise HashMismatch(json.dumps(row))
    # Receipts are read again only for integrity, not included in measured tool phases.
    for name,p,h in receipts:
        row,_=read_hash(p,'post_receipt_'+name,emit);require(row['sha256']==h,'receipt_changed:'+name)
    return dict(status='HASHES_MATCH',readings=rows,readings_count=len(rows),distinct_paths=len({key(p) for _,p,_ in jobs}),seconds=time.monotonic()-start,limitation=LIMIT,read_mode='4MiB blocks; instrumentation and fsync included')

def child(output):
    require(output.is_dir() and not any((output/n).exists() for n in ('events.jsonl','report.json','input-old.json','input-prior.json')),'child_output_reuse')
    emit=Events(output/'events.jsonl')
    try:
        report=discover(RECEIPTS,output,SOURCES,Path('P:/bin/config.cpp'),[Path('P:/'+n) for n in ('DZ','bin','core','scripts')],emit);code=0
    except Exception as e:
        status='HASH_MISMATCH' if isinstance(e,HashMismatch) else ('INCONCLUSIVE_IO' if isinstance(e,OSError) else 'INCONCLUSIVE_CONTRACT')
        report=dict(status=status,type=type(e).__name__,reason=str(e),traceback=traceback.format_exc(),limitation=LIMIT);code=1
    report['pid']=os.getpid();dump(output/'report.json',report);return code

def interpreter_image():
    # Same loaded CPython behind the GIS venv, not a PATH/global interpreter.
    # Direct image + -I -S avoids the venv launcher creating an unowned child.
    kernel=ctypes.WinDLL('kernel32',use_last_error=True);fn=kernel.GetModuleFileNameW
    fn.argtypes=[wintypes.HMODULE,wintypes.LPWSTR,wintypes.DWORD];fn.restype=wintypes.DWORD
    text=ctypes.create_unicode_buffer(32768);size=fn(None,text,len(text))
    require(0<size<len(text),'interpreter_image');return text.value

def creation_time(process):
    # Microsoft GetProcessTimes: HANDLE + four LPFILETIME; handle owned by Popen.
    # https://learn.microsoft.com/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes
    kernel=ctypes.WinDLL('kernel32',use_last_error=True);fn=kernel.GetProcessTimes
    fn.argtypes=[wintypes.HANDLE]+[ctypes.POINTER(wintypes.FILETIME)]*4;fn.restype=wintypes.BOOL
    values=[wintypes.FILETIME() for _ in range(4)]
    if not fn(int(process._handle),*[ctypes.byref(v) for v in values]):raise ctypes.WinError(ctypes.get_last_error())
    return (values[0].dwHighDateTime<<32)|values[0].dwLowDateTime

def launch(command,output,seconds=60):
    require(0<seconds<=60,'timeout_range');start=time.monotonic();expired=threading.Event()
    with (output/'child.stdout').open('wb') as stdout,(output/'child.stderr').open('wb') as stderr:
        p=subprocess.Popen(command,stdout=stdout,stderr=stderr,creationflags=0x08000000)
        def timeout():
            if p.poll() is None:
                expired.set()
                try:p.kill() # uses this Popen's process handle, never lookup by PID
                except ProcessLookupError:pass
        timer=threading.Timer(max(0,seconds-(time.monotonic()-start)),timeout);timer.daemon=True;timer.start()
        try:
            identity=dict(pid=p.pid,creation_filetime=creation_time(p),max_seconds=seconds,command=command)
            dump(output/'identity.json',identity);p.wait(timeout=max(0,seconds-(time.monotonic()-start))+10)
        except BaseException:
            timeout();p.wait(timeout=10);raise
        finally:timer.cancel()
    result=dict(status='INCONCLUSIVE_TIMEOUT' if expired.is_set() else 'CHILD_FINISHED',returncode=p.returncode,seconds=time.monotonic()-start,identity=identity)
    dump(output/'lifecycle.json',result);return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path);parser.add_argument('--child',action='store_true');args=parser.parse_args()
    if args.child:return child(args.output)
    args.output.mkdir(exist_ok=False)
    lifecycle=launch([interpreter_image(),'-I','-S',str(Path(__file__).resolve()),str(args.output),'--child'],args.output)
    if lifecycle['status']=='INCONCLUSIVE_TIMEOUT':report=dict(status='INCONCLUSIVE_TIMEOUT',limitation=LIMIT)
    else:
        try:
            report=json.loads((args.output/'report.json').read_bytes());require(report['status'] in ('HASHES_MATCH','HASH_MISMATCH','INCONCLUSIVE_IO','INCONCLUSIVE_CONTRACT'),'child_status')
            require(report['pid']==lifecycle['identity']['pid'],'child_pid_not_owned_handle')
            require((lifecycle['returncode']==0)==(report['status']=='HASHES_MATCH'),'exit_status_disagreement')
        except Exception as e:report=dict(status='INCONCLUSIVE_CHILD',reason=str(e),limitation=LIMIT)
    report['lifecycle']=lifecycle;dump(args.output/'completion.json',report);print(report['status']);return 0 if report['status']=='HASHES_MATCH' else 1

if __name__=='__main__':raise SystemExit(main())
