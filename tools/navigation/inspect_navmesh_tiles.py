"""Read-only empirical TESM6 tile comparison, not a general NM decoder.

Magic and prefix fields match Detour's dtMeshHeader, but installed version11
differs from upstream7. No polygon/state mutation or interpretation is done.
Reference: recastnavigation/Detour/Include/DetourNavMesh.h lines228-255.
Every offset, tile coordinate and horizontal bound is checked against the file.
"""
import hashlib
import json
from pathlib import Path
import struct

ROOT=Path(__file__).resolve().parents[2]

def read(path, tile_width=50):
    data=path.read_bytes()
    if tile_width not in (12.5,25,50):
        raise ValueError('Only the three explicit local diagnostic layouts are supported')
    side=int(12288//tile_width)
    magic,version,count,nx,nz=struct.unpack_from('<5I',data)
    if (magic,version,count,nx,nz)!=(0x4d534554,6,side*side,side,side):
        raise ValueError('Unsupported local format')
    origin_x,origin_y,origin_z,width,depth=struct.unpack_from('<5f',data,20)
    if (origin_x,origin_y,origin_z,width,depth)!=(0,0,0,tile_width,tile_width):
        raise ValueError('Unexpected origin or tile dimensions')
    offsets=struct.unpack_from(f'<{count}I',data,48)
    base=48+4*count
    if offsets[0]!=0 or list(offsets)!=sorted(set(offsets)):
        raise ValueError('Invalid offset table')
    result={}
    for i,offset in enumerate(offsets):
        start=base+offset
        end=base+offsets[i+1] if i+1<count else len(data)
        header=start+16
        ints=struct.unpack_from('<15I',data,header)
        values=struct.unpack_from('<10f',data,header+60)
        if ints[0]!=0x444e4156 or ints[1]!=11 or end<=header+100:
            raise ValueError('Unexpected tile prefix/boundary')
        x,z=ints[2:4]
        if not (0<=x<side and 0<=z<side) or (x,z) in result or abs(values[3]-tile_width*x)>.001 or abs(values[5]-tile_width*z)>.001 or abs(values[6]-tile_width*(x+1))>.001 or abs(values[8]-tile_width*(z+1))>.001:
            raise ValueError('Header bounds do not match tile coordinates')
        # Prefix includes a reference and lengths; compare serialized tile data.
        payload=data[header:end]
        result[(x,z)]={'tile':[x,z],'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest(),
                       'polygons':ints[6],'vertices':ints[7],'y_bounds':[values[4],values[7]]}
    return result

if __name__=='__main__':
    old=read(ROOT/'tb/regional_clearance_v1/navmesh/baltic_regional_v1.nm')
    new=read(ROOT/'tb/narva_navigation_v3/navmesh/baltic_navigation_native_v1.nm')
    changed=[{'old':old[k],'new':new[k]} for k in old if old[k]['sha256']!=new[k]['sha256']]
    structural=[{'old':old[k],'new':new[k]} for k in old if any(old[k][field]!=new[k][field] for field in ['polygons','vertices','y_bounds'])]
    result={'status':'READ_ONLY_EMPIRICAL_TILE_COMPARISON','tiles_checked':len(new),'serialized_changes_count':len(changed),'structural_changes':structural,
            'narva_tiles':[new[(x,z)] for z in range(136,140) for x in range(47,51)],
            'limits':['Empirically checked header subset. No complete format or polygon-topology claim.']}
    (ROOT/'evidence/navigation/native-tile-comparison-v2.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'tiles':len(new),'serialized_changed_count':len(changed),'structural_changes':len(structural),'changed_coordinates':[v['new']['tile'] for v in structural][:40]},indent=2))
