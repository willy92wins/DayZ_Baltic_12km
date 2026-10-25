"""Read our native DayZ 0WZD export; check against independent ASC and V3 poses.

Layout reference: BI Community Wiki, Wrp_File_Format_-_8WVR, section 0WZD.
No editing of the native source. Optional filtered copy removes ONLY named pond.
"""
from pathlib import Path
import argparse, hashlib, json, struct
import numpy as np
import rasterio
ap=argparse.ArgumentParser()
ap.add_argument('--wrp',type=Path,required=True)
ap.add_argument('--asc',type=Path,required=True)
ap.add_argument('--out',type=Path,required=True)
ap.add_argument('--without-diagnostic-pond',type=Path)
a=ap.parse_args()
b=a.wrp.read_bytes()
magic,tx,tz,nx,nz,cell=struct.unpack_from('<4s4If',b)
assert (magic,tx,tz,nx,nz,cell)==(b'0WZD',1024,1024,2048,2048,12.0)
heights=np.frombuffer(b,dtype='<f4',count=nx*nz,offset=24).reshape(nz,nx)
o=24+nx*nz*4
indices=np.frombuffer(b,dtype='<u2',count=tx*tz,offset=o)
o+=tx*tz*2
def u32():
    global o
    n=struct.unpack_from('<I',b,o)[0];o+=4;return n
n=u32(); assert 1<n<2000
materials=[]
for _ in range(n):
    names=[]
    while True:
        length=u32()
        if not length: break
        assert length<1024
        names.append(b[o:o+length].decode('ascii').rstrip('\0'));o+=length
    materials.append(names)
assert int(indices.max())<n
object_start=o
objects=[]
while True:
    start=o
    matrix=struct.unpack_from('<12f',b,o);o+=48
    ident=u32();length=u32()
    assert length<1024
    if not length:
        sentinel=b[start:o]
        break
    name=b[o:o+length].decode('ascii').rstrip('\0');o+=length
    objects.append(dict(name=name,id=ident,matrix=list(matrix),start=start,end=o))
assert o==len(b),('unexpected trailing bytes',o,len(b))
with rasterio.open(a.asc) as src: raster=src.read(1)
delta=np.abs(heights[::-1,:]-raster)
bridge=[x for x in objects if x['name'].lower()=='dz\\structures\\roads\\bridges\\bridge_metal_25.p3d']
pond=[x for x in objects if x['name'].lower()=='dz\\water\\ponds\\pond_50x50.p3d']
assert len(bridge)==len(pond)==1 and len(objects)==2
position=bridge[0]['matrix'][9:12]
pose_error=float(np.max(np.abs(np.array(position)-[2417.143066,-6.054884,6889.884766])))
checks={'all_heights_match_native_asc':bool(delta.max()<=.00501),
        'bridge_pose_matches_v3':pose_error<=.00001,
        'no_unparsed_bytes':o==len(b),'materials_in_bounds':int(indices.max())<n}
result={'status':'PASS_NATIVE_WRP' if all(checks.values()) else 'FAIL',
        'checks':checks,'source_sha256':hashlib.sha256(b).hexdigest(),
        'terrain_grid':[nx,nz],'terrain_spacing_m':tx*cell/nx,
        'texture_grid':[tx,tz],'texture_spacing_m':cell,'materials':n,
        'height_max_error_m':float(delta.max()),'bridge_pose_error_m':pose_error,
        'objects':objects,'limits':['Export height/pose only; project reopening must be evidenced separately. Not an in-game collision test.',
                                    'Height-mode persistence not inspected in UI.',
                                    'Hidden diagnostic pond is included by native WRP export.']}
if a.without_diagnostic_pond:
    assert all(checks.values())
    assert not a.without_diagnostic_pond.exists(),'refuse overwrite'
    p=pond[0]
    filtered=b[:p['start']]+b[p['end']:]
    assert filtered[:object_start]==b[:object_start]
    assert filtered[-len(sentinel):]==sentinel
    assert p['name'].encode() not in filtered and bridge[0]['name'].encode() in filtered
    a.without_diagnostic_pond.parent.mkdir(parents=True,exist_ok=True)
    a.without_diagnostic_pond.write_bytes(filtered)
    result['filtered']={'path':str(a.without_diagnostic_pond),
                        'sha256':hashlib.sha256(filtered).hexdigest(),
                        'removed_bytes':p['end']-p['start'],
                        'terrain_and_material_bytes_identical':True,
                        'retained_bridge_record_identical':True,
                        'consumer_validation':'PENDING_BINARIZE_AND_GAME'}
a.out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
raise SystemExit(0 if all(checks.values()) else 1)
