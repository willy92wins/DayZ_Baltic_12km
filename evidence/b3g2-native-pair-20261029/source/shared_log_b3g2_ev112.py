"""Bounded Windows shared reads and an exact, source-bound diagnostic classifier.

Win32 layout: learn.microsoft.com/windows/win32/api/fileapi/ns-fileapi-by_handle_file_information
File IDs here are for the NTFS profile volume checked by the host preflight.
"""
import ctypes,hashlib,json,re,os,time
from ctypes import wintypes as wt
from pathlib import Path
from datetime import datetime,timezone,timedelta
from contact_pair_b3g_ev112 import require
from contact_pair_b3g1_receipts_ev112 import utc

LIMIT=20*1024**2
class FileInfo(ctypes.Structure):
    _fields_=[('attributes',wt.DWORD),('created',wt.FILETIME),('accessed',wt.FILETIME),('written',wt.FILETIME),
              ('volume',wt.DWORD),('size_hi',wt.DWORD),('size_lo',wt.DWORD),('links',wt.DWORD),('index_hi',wt.DWORD),('index_lo',wt.DWORD)]

def kernel():
    require(os.name=='nt','windows_only');k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.CreateFileW.argtypes=[wt.LPCWSTR,wt.DWORD,wt.DWORD,wt.LPVOID,wt.DWORD,wt.DWORD,wt.HANDLE];k.CreateFileW.restype=wt.HANDLE
    k.CloseHandle.argtypes=[wt.HANDLE];k.CloseHandle.restype=wt.BOOL
    k.GetFileInformationByHandle.argtypes=[wt.HANDLE,ctypes.POINTER(FileInfo)];k.GetFileInformationByHandle.restype=wt.BOOL
    k.ReadFile.argtypes=[wt.HANDLE,wt.LPVOID,wt.DWORD,ctypes.POINTER(wt.DWORD),wt.LPVOID];k.ReadFile.restype=wt.BOOL
    return k

def ticks(ft):return (ft.dwHighDateTime<<32)|ft.dwLowDateTime
def stamp(value):return (datetime(1970,1,1,tzinfo=timezone.utc)+timedelta(microseconds=(value-116444736000000000)//10)).isoformat()
def now():return datetime.now(timezone.utc).isoformat()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def info(k,h):
    f=FileInfo()
    if not k.GetFileInformationByHandle(h,ctypes.byref(f)):raise ctypes.WinError(ctypes.get_last_error())
    require(not f.attributes&0x10,'not_regular_file')
    return {'file_id':[f.volume,f.index_hi,f.index_lo,ticks(f.created)],'size':(f.size_hi<<32)|f.size_lo,
            'created_filetime':ticks(f.created),'last_write_filetime':ticks(f.written),
            'created_utc':stamp(ticks(f.created)),'last_write_utc':stamp(ticks(f.written))}

def snapshot(path):
    path=Path(path).absolute();k=kernel()
    # GENERIC_READ; share READ|WRITE|DELETE; OPEN_EXISTING. Never open a writer.
    h=k.CreateFileW(str(path),0x80000000,7,None,3,0x80,None)
    if h==wt.HANDLE(-1).value:raise ctypes.WinError(ctypes.get_last_error())
    try:
        before=info(k,h);require(0<=before['size']<=LIMIT,'snapshot_size')
        data=ctypes.create_string_buffer(before['size']);count=wt.DWORD()
        if not k.ReadFile(h,data,before['size'],ctypes.byref(count),None):raise ctypes.WinError(ctypes.get_last_error())
        require(count.value==before['size'],'snapshot_short_read');after=info(k,h)
        require(before['file_id']==after['file_id'] and after['size']>=before['size'],'snapshot_replaced_or_truncated')
        raw=data.raw;checked=time.time_ns()//100+116444736000000000
        record={**after,'source':str(path),'bytes':len(raw),'sha256':digest(raw),'checked_filetime':checked,'checked_utc':stamp(checked),'grew_during_read':after['size']!=len(raw)}
        return raw,record
    finally:k.CloseHandle(h)

def stable_pair(a,b):
    ra,ma=a;rb,mb=b
    require(ma['file_id']==mb['file_id'],'snapshot_file_changed')
    require(not ma['grew_during_read'] and not mb['grew_during_read'] and len(ra)==len(rb) and digest(ra)==digest(rb),'snapshot_not_stable')

def metadata(raw,meta):
    require(isinstance(meta['file_id'],list) and len(meta['file_id'])==4 and all(type(x) is int and x>=0 for x in meta['file_id']),'file_id')
    require(meta['sha256']==digest(raw) and meta['bytes']==len(raw)<=LIMIT and meta['size']>=len(raw),'snapshot_binding')
    require(type(meta['grew_during_read']) is bool and meta['grew_during_read']==(meta['size']!=len(raw)),'snapshot_growth')
    require(meta['created_filetime']==meta['file_id'][3],'file_creation_binding')
    for k in ('created','last_write','checked'):
        require(type(meta[k+'_filetime']) is int and meta[k+'_utc']==stamp(meta[k+'_filetime']),'filetime_binding')
    require(meta['created_filetime']<=meta['last_write_filetime']<=meta['checked_filetime'],'snapshot_times')

def load_golden(path):
    from water_query_native_b1_ev112 import verify
    golden=json.loads(Path(path).read_text(encoding='utf-8'));verify(golden['inputs'])
    raw=Path(golden['archive']).read_bytes()
    require(digest(raw)=='99df8cd592333b5978cb1ba870720592be1607b35099bbaea3f67d5fb2238c0b','golden_archive')
    rows=raw.decode('utf-8-sig').splitlines()[19:29];parsed=[LINE.fullmatch(s) for s in rows]
    require(all(m and m[1]==parsed[0][1] for m in parsed),'golden_timestamp')
    require([m[2].replace(golden['archived_mission'],'$MISSION') for m in parsed]==golden['lines'],'golden_derivation')
    require(len(golden['lines'])==10 and len(golden['sources'])==4,'golden_scope')
    for s in golden['sources']:
        require(golden['inputs'][s['local']]==s['entry_sha256'] and golden['inputs'][s['package']]==s['package_sha256'],'golden_source_binding')
    return golden

LINE=re.compile(r'^(\d{2}:\d{2}:\d{2}\.\d{3})\s+(SCRIPT.*)$')
ERROR=re.compile(r'SCRIPT\s*\(E\)')

def classify(raw,golden,mission):
    require(len(raw)<=LIMIT,'script_size')
    lines=raw.decode('utf-8-sig',errors='replace').splitlines();parsed=[LINE.fullmatch(s) for s in lines]
    require(not any(re.search(r'Can.t compile mission init script|Formula too complex',s) for s in lines),'mission_compile_error')
    expected=golden['lines'];used=set();blocks=[]
    for i,m in enumerate(parsed):
        if m and m[2]==expected[0]:
            require(not blocks and i+len(expected)<=len(lines),'duplicate_or_truncated_diagnostic')
            group=parsed[i:i+len(expected)];require(all(x and x[1]==m[1] for x in group),'diagnostic_timestamp_or_contiguity')
            actual=[x[2].replace(str(mission),'$MISSION') for x in group]
            require(actual==expected,'diagnostic_frames_changed')
            used.update(range(i,i+len(expected)));blocks.append({'kind':'KNOWN_OPTIONAL_DEBUG_PROFILE_DUMPSTACK','timestamp':m[1],'line':i+1,'golden_sha256':digest(json.dumps(golden,sort_keys=True).encode())})
    require(not any(ERROR.search(s) and i not in used for i,s in enumerate(lines)),'unknown_script_error')
    return {'known_diagnostics':blocks,'warnings':[s for s in lines if re.search(r'SCRIPT\s*\(W\)',s)],'status':'NO_BLOCKING_SCRIPT_ERRORS'}

def health(raw,meta,host,golden):
    import ntpath
    metadata(raw,meta)
    require(raw.endswith(b'\n'),'script_incomplete_line')
    norm=lambda p:ntpath.normcase(ntpath.normpath(p))
    require(norm(ntpath.dirname(meta['source']))==norm(host['profiles']) and re.fullmatch(r'script_\d{4}-\d\d-\d\d_\d\d-\d\d-\d\d\.log',ntpath.basename(meta['source'])),'script_location')
    require(utc(host['created_utc'])<=utc(meta['created_utc'])<=utc(meta['last_write_utc'])<=utc(meta['checked_utc']),'script_freshness')
    text=raw.decode('utf-8-sig',errors='replace');m=re.search(r'started at .*\((\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) UTC\)',text)
    require(m is not None,'script_header')
    start=datetime.strptime(m[1],'%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    require(-1<=(start-utc(host['created_utc'])).total_seconds() and start<=utc(meta['checked_utc']),'script_header_time')
    require(meta['sha256']==digest(raw) and meta['bytes']==len(raw),'script_snapshot_binding')
    return classify(raw,golden,host['mission_path'])
