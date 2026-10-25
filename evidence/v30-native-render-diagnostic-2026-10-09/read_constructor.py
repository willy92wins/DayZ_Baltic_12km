from pathlib import Path
import sys,json,struct,bisect
B=Path(__file__).parent;sys.path.insert(0,str(B/'analysis-deps'))
import pefile,capstone
p=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ/DayZDiag_x64.exe');pe=pefile.PE(str(p));base=pe.OPTIONAL_HEADER.ImageBase
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);md.detail=True
functions=sorted((base+x.struct.BeginAddress,base+x.struct.EndAddress) for x in pe.DIRECTORY_ENTRY_EXCEPTION);starts=[a for a,b in functions]
refs=json.loads((B/'registrations.json').read_text())['references']
def string(va):
 try:
  raw=pe.get_data(va-base,160).split(b'\0')[0]
  return raw.decode('ascii') if raw and all(32<=v<127 for v in raw) else None
 except Exception:return None
def dump(addr):
 j=bisect.bisect_right(starts,addr)-1;lo,hi=functions[j];lines=[]
 if not lo<=addr<hi:lo,hi=addr,addr+240
 for x in md.disasm(pe.get_data(lo-base,min(hi-lo,2500)),lo):
  notes=[]
  for op in x.operands:
   if op.type==capstone.x86.X86_OP_MEM and op.mem.base==capstone.x86.X86_REG_RIP:
    dest=x.address+x.size+op.mem.disp;s=string(dest);notes.append(hex(dest)+((' '+repr(s)) if s else ''))
  lines.append(f'{x.address:x}: {x.mnemonic} {x.op_str}'+(' ; '+', '.join(notes) if notes else ''))
  if x.mnemonic=='ret':break
 return dict(start=hex(lo),end=hex(hi),instructions=lines)
result=[dump(x) for x in [0x1402f18d0,0x1402f2c10,0x1402f1ed0]]
(B/'api-value-access.json').write_text(json.dumps(result,indent=2)+'\n')
for x in result:print('\n'.join(x['instructions']))
