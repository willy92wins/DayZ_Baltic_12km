from pathlib import Path
import hashlib,json,struct,sys
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path.insert(0,str(W/'tools/playtest'))
from attach_navmesh import read_pbo
p=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ/Addons/worlds_chernarusplus_nav.pbo')
raw,props,entries=read_pbo(p);data=entries['navmesh.nm']
assert hashlib.sha256(raw).hexdigest()=='f0503b2bbcca0a5913a6545d6e1b324ef872f48486b7b6960ebeaa1b5b398c2e'
magic,version,count,nx,nz=struct.unpack_from('<5I',data)
offsets=struct.unpack_from(f'<{count}I',data,48);base=48+count*4
assert offsets[0]==0 and list(offsets)==sorted(set(offsets)) and offsets[-1]+base<len(data)
samples=[];prefixes={};hits={};lengths={}
for i,offset in enumerate(offsets):
    start=base+offset;end=base+offsets[i+1] if i+1<count else len(data)
    block=data[start:end];v=struct.unpack_from('<4I',block)
    for j in range(0,min(len(block),256),4):
        if block[j:j+4]==b'VAND':hits[str(j)]=hits.get(str(j),0)+1;break
    prefixes[str(v[1])]=prefixes.get(str(v[1]),0)+1
    lengths[str(len(block))]=lengths.get(str(len(block)),0)+1
    if i in (0,1,307,40000,50000,count-1):samples.append(dict(index=i,offset=start,bytes=len(block),prefix_u32=struct.unpack_from('<29I',block),prefix_f32=struct.unpack_from('<10f',block,76)))
out=dict(status='READ_ONLY_REFERENCE_DISCOVERY',version=version,grid=[nx,nz],tiles=count,ordered_offsets=True,detour_magic_offsets=hits,prefix_second_u32_counts=prefixes,tile_bytes_min=min(map(int,lengths)),tile_bytes_max=max(map(int,lengths)),samples=samples,source_sha256=hashlib.sha256(data).hexdigest(),limits=['Empirical prefixes only; not complete serialized topology or useful-path acceptance.'])
(R/'navmesh-v9-discovery/installed-nav-tiles.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
