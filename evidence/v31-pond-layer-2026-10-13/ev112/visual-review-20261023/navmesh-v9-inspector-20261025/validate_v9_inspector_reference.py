from pathlib import Path
import hashlib,json,struct,sys
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/playtest'),str(W/'tools/navigation')]
from attach_navmesh import read_pbo
from inspect_navmesh_v9_ev112 import inspect
p=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ/Addons/worlds_chernarusplus_nav.pbo')
raw,_,entries=read_pbo(p);data=entries['navmesh.nm']
assert hashlib.sha256(data).hexdigest()=='0b18d48d6c1e902e41b35b91588e84a3e3068a28df6d71cf6d74a6f80d29a163'
result=inspect(data,(307,307));result['reference_pbo_sha256']=hashlib.sha256(raw).hexdigest()
result['inspector_sha256']=hashlib.sha256((W/'tools/navigation/inspect_navmesh_v9_ev112.py').read_bytes()).hexdigest()
(R/'navmesh-v9-discovery/reference-inspection.json').write_text(json.dumps(result,indent=2)+'\n')
base=48+4*94249; offsets=struct.unpack_from('<3I',data,48)
header=bytearray(data[:48]);struct.pack_into('<3I',header,8,2,2,1);struct.pack_into('<I',header,40,2)
fixture=header+struct.pack('<2I',0,offsets[1])+data[base:base+offsets[2]]
out=R/'navmesh-v9-discovery/navmesh-v9-two-reference-tiles.nm'
out.write_bytes(fixture)
meta=dict(source_sha256=result['sha256'],source_tile_indices=[0,1],fixture_sha256=hashlib.sha256(fixture).hexdigest(),changes='Only TESM count/grid/maxTiles and two-entry offset table adjusted. Original two serialized tile payloads byte-exact. Not a generated or engine-accepted map.')
out.with_suffix('.json').write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps(result,indent=2))
