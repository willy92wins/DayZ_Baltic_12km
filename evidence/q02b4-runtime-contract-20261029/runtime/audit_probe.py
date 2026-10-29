"""Bounded API discovery on two own literals only; no saved-map source access."""
import sys,os,json,hashlib
from pathlib import Path
sys.path.insert(0,'E:/DayZ-Baltic-Build/shape-repair-20261025/dry-road-build-dependencies-20261028')
import psutil
base=Path(__file__).resolve().parent
allowed=base/'own-allowed.literal'; forbidden=base/'own-forbidden.literal'
for p,b in ((allowed,b'Q02B4 own literal\x00\xff\r\n'),(forbidden,b'not to read after hook')):
    with p.open('xb') as f:f.write(b)
maps=psutil.Process().memory_maps(grouped=True)
runtime=[]
for m in maps:
    if Path(m.path).name.lower() in ('python312.dll','python3.dll','python.exe'):
        p=Path(m.path);b=p.read_bytes();runtime.append({'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'evidence':'self memory_maps observed, not upstream source identity'})
events=[];seen=False
def hook(event,args):
    global seen
    if event=='q02b4.probe':seen=True;return
    if event=='open':
        if len(events)>=16:raise RuntimeError('event cap')
        path=args[0];ok=type(path)is str and os.path.normcase(os.path.abspath(path))==os.path.normcase(str(allowed))
        events.append({'event':'open','path':str(path),'allowed':ok})
        if not ok:raise PermissionError('Q02B4 forbidden open')
    elif event=='import':
        if len(events)>=16:raise RuntimeError('event cap')
        events.append({'event':'import','module':args[0],'allowed':False})
        raise PermissionError('Q02B4 forbidden import')
sys.addaudithook(hook);sys.audit('q02b4.probe');assert seen
with allowed.open('rb') as f:literal=f.read(64)
assert literal==b'Q02B4 own literal\x00\xff\r\n'
checks={}
for label,call in [('builtin_open',lambda:open(forbidden,'rb')),('os_open',lambda:os.open(forbidden,os.O_RDONLY)),('import',lambda:__import__('q02b4_forbidden_module_never_loaded'))]:
    try:call()
    except PermissionError:checks[label]='REJECTED_AS_EXPECTED'
    else:raise AssertionError(label)
print(json.dumps({'state':'AUDIT_API_LITERAL_PROBE_ONLY','runtime_images_observed':runtime,'hook_selftest':seen,'checks':checks,'events':events,'no_capture_opened':True,'codec_data_calls':0,'security_sandbox':False,'scope':'hook installed only after preloads in isolated child'}))
