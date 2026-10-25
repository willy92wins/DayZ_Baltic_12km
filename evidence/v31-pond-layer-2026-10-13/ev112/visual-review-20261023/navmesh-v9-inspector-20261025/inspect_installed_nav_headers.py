from pathlib import Path
import hashlib,json,struct,sys
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path.insert(0,str(W/'tools/playtest'))
from attach_navmesh import read_pbo
p=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ/Addons/worlds_chernarusplus_nav.pbo')
raw,props,entries=read_pbo(p)
rows=[]
for name,data in entries.items():
    if not name.endswith('.nm'):continue
    rows.append(dict(entry=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),header_u32=struct.unpack_from('<12I',data),header_f32=struct.unpack_from('<7f',data,20),first96_hex=data[:96].hex()))
out=dict(source=str(p),pbo_sha256=hashlib.sha256(raw).hexdigest(),entries=rows,scope='Installed reference header inspection only; no assumed Baltic version9 layout.')
(R/'navmesh-v9-discovery/installed-nav-headers.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
