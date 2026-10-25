"""Read three verified registry fields of our diagnostic client. No memory writes."""
from pathlib import Path
import argparse,ctypes as c,struct,json,hashlib
B=Path(__file__).parent
ap=argparse.ArgumentParser();ap.add_argument('--pid',type=int,required=True);ap.add_argument('--base',type=lambda s:int(s,0),required=True);a=ap.parse_args()
exe=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ/DayZDiag_x64.exe')
digest=hashlib.sha256(exe.read_bytes()).hexdigest();assert digest=='34f6377be4fd065d104e67263e0c96ac2cb2e348119a4838eba08d2e61b7a69a'
k=c.WinDLL('kernel32',use_last_error=True)
k.OpenProcess.argtypes=[c.c_uint32,c.c_int,c.c_uint32];k.OpenProcess.restype=c.c_void_p
k.ReadProcessMemory.argtypes=[c.c_void_p,c.c_void_p,c.c_void_p,c.c_size_t,c.POINTER(c.c_size_t)];k.ReadProcessMemory.restype=c.c_int
k.CloseHandle.argtypes=[c.c_void_p];k.CloseHandle.restype=c.c_int
handle=k.OpenProcess(0x0410,False,a.pid);assert handle,c.get_last_error()
def read(addr,size):
 buf=c.create_string_buffer(size);got=c.c_size_t()
 assert k.ReadProcessMemory(handle,addr,buf,size,c.byref(got)) and got.value==size,c.get_last_error()
 return buf.raw
def u64(addr):return struct.unpack('<Q',read(addr,8))[0]
try:
 count=struct.unpack('<I',read(a.base+0x11cd174,4))[0];assert 1<=count<=4096
 result=[]
 for name,rva in [('Render debug mode',0x12697d8),('Water',0x1269c60)]:
  obj=a.base+rva;value,index=struct.unpack('<ii',read(obj,8));assert 0<=index<count
  assert u64(a.base+0x11cd180+index*8)==obj
  ptr=u64(a.base+0x11d3190+index*0x88)
  label=read(ptr,len(name)+1);assert label==name.encode()+b'\0',label
  assert value==0,(name,value)
  result.append(dict(label=name,id=index,initial_value=value,object_rva=hex(rva),registry_backlink=True,label_verified=True))
 out=dict(status='READ_ONLY_LIVE_LABEL_AND_REGISTRY_PARITY',pid=a.pid,module_base=hex(a.base),exe_sha256=digest,count=count,items=result)
 (B/'live-ids.json').write_text(json.dumps(out,indent=2)+'\n')
 target=Path('P:/DayZ_MCP_dev/_client/profiles/baltic_render_probe_v1.ids');assert not target.exists()
 target.write_text(digest+'\n'+'\n'.join(str(x['id']) for x in result)+'\n',encoding='ascii')
 print(json.dumps(out,indent=2))
finally:k.CloseHandle(handle)
