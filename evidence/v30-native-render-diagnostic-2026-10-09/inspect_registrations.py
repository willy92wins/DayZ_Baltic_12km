"""Read-only PE string references; never attaches to or patches the process."""
from pathlib import Path
import sys,struct,re,json,hashlib,bisect
B=Path(__file__).parent;sys.path.insert(0,str(B/'analysis-deps'))
import pefile,capstone
p=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ/DayZDiag_x64.exe')
raw=p.read_bytes();pe=pefile.PE(data=raw);base=pe.OPTIONAL_HEADER.ImageBase
targets={}
for label in [b'GetEngineValue',b'SetEngineValue']:
 for hit in re.finditer(re.escape(label)+b'\0',raw):
  if hit.start() and raw[hit.start()-1]!=0:continue
  try:targets[base+pe.get_rva_from_offset(hit.start())]=label.decode()
  except pefile.PEFormatError:pass
text=next(s for s in pe.sections if s.Name.rstrip(b'\0')==b'.text');code=text.get_data();va=base+text.VirtualAddress
functions=sorted((base+x.struct.BeginAddress,base+x.struct.EndAddress) for x in pe.DIRECTORY_ENTRY_EXCEPTION)
starts=[a for a,b in functions];md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
out=[]
for m in re.finditer(rb'[\x48-\x4f]\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]',code):
 i=m.start();dest=va+i+7+struct.unpack_from('<i',code,i+3)[0]
 if dest not in targets:continue
 at=va+i;j=bisect.bisect_right(starts,at)-1;lo,hi=functions[j]
 if not lo<=at<hi:continue
 ins=list(md.disasm(code[lo-va:hi-va],lo));k=next((k for k,x in enumerate(ins) if x.address==at),None)
 if k is None:continue
 lines=[f'{x.address:016x}: {x.mnemonic} {x.op_str}' for x in ins[max(0,k-14):min(len(ins),k+20)]]
 out.append(dict(label=targets[dest],string_va=hex(dest),reference_va=hex(at),function_start=hex(lo),function_end=hex(hi),instructions=lines))
result=dict(executable=str(p),sha256=hashlib.sha256(raw).hexdigest(),image_base=hex(base),references=out)
(B/'api-registrations.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(sha256=result['sha256'],references=[{k:v for k,v in x.items() if k!='instructions'} for x in out]),indent=2))
for x in out:
 print(x['label']+'\n'+'\n'.join(x['instructions']))
