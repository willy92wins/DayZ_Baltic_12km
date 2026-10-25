"""Read-only label inventory restricted to water/terrain/render diagnostic entries."""
from pathlib import Path
import ctypes as c,struct,json,re
B=Path(__file__).parent;ids=json.loads((B/'live-ids.json').read_text());base=int(ids['module_base'],0)
k=c.WinDLL('kernel32',use_last_error=True);k.OpenProcess.argtypes=[c.c_uint32,c.c_int,c.c_uint32];k.OpenProcess.restype=c.c_void_p;k.ReadProcessMemory.argtypes=[c.c_void_p,c.c_void_p,c.c_void_p,c.c_size_t,c.POINTER(c.c_size_t)];k.ReadProcessMemory.restype=c.c_int;k.CloseHandle.argtypes=[c.c_void_p]
h=k.OpenProcess(0x410,False,ids['pid']);assert h
def read(a,n):
 b=c.create_string_buffer(n);got=c.c_size_t();assert k.ReadProcessMemory(h,a,b,n,c.byref(got)) and got.value==n;return b.raw
try:
 out=[]
 for i in range(ids['count']):
  row=read(base+0x11d3190+i*0x88,0x88);ptr=struct.unpack_from('<Q',row)[0]
  if not ptr:continue
  try:name=read(ptr,96).split(b'\0')[0].decode('ascii')
  except Exception:continue
  if not re.search('water|ocean|shore|terrain|render debug|enfusion renderer',name,re.I):continue
  obj=struct.unpack('<Q',read(base+0x11cd180+i*8,8))[0]
  value,index=struct.unpack('<ii',read(obj,8));assert index==i
  out.append(dict(id=i,label=name,value=value,range_index=struct.unpack_from('<i',row,0x40)[0]))
 (B/'water-menu-readonly.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
finally:k.CloseHandle(h)
