"""Inspect actual FileBank entries and compare them to the isolated compiled tree.
Table layout is also used by DayZ_MCP's verified tools/verify_pbo.py.
"""
from pathlib import Path
import argparse,collections,hashlib,json,re,struct
ap=argparse.ArgumentParser()
ap.add_argument('--pbo',type=Path,required=True)
ap.add_argument('--compiled',type=Path,required=True)
ap.add_argument('--out',type=Path,required=True)
ap.add_argument('--extract-config',type=Path)
ap.add_argument('--expected-materials',type=int,default=367)
ap.add_argument('--expected-textures',type=int,default=50)
ap.add_argument('--expected-water-object',choices=['none','pond_50x50','lake_50x50'],default='none',
                help='Explicit water-object expectation; default preserves the original no-pond gate')
a=ap.parse_args();data=a.pbo.read_bytes();pos=0;entries=[];properties={}
def string():
    global pos
    end=data.index(b'\0',pos);s=data[pos:end].decode('utf-8');pos=end+1;return s
while True:
    name=string();mime,original,res,ts,size=struct.unpack_from('<5I',data,pos);pos+=20
    if not name:
        if mime==0x56657273:
            while True:
                k=string()
                if not k:break
                properties[k]=string()
            continue
        break
    assert mime==0,('compressed entry requires decoder',name,mime)
    entries.append({'name':name,'size':size})
blob={};mismatch=[]
for e in entries:
    b=data[pos:pos+e['size']];pos+=e['size']
    assert len(b)==e['size']
    key=e['name'].replace('\\','/').lower()
    assert key not in blob
    blob[key]=b
    p=a.compiled/e['name'].replace('\\','/')
    if not p.is_file() or p.read_bytes()!=b:mismatch.append(e['name'])
    e['sha256']=hashlib.sha256(b).hexdigest()
wrp=blob.get('baltic_trial.wrp',b'');cfg=blob.get('config.bin',b'')
material_entries=[k for k in blob if k.endswith('.rvmat')]
texture_entries=[k for k in blob if k.endswith('.paa')]
checks={
 'expected_prefix':properties.get('prefix','').lower().rstrip('\\')=='dayz_baltic_12km_dev\\tb\\narva_trial',
 'world_binarized':wrp[:4]==b'OPRW',
 'config_compiled':cfg[:4]==b'\0raP',
 'config_world_identity':b'BalticTrial\0' in cfg and b'baltic_trial.wrp' in cfg,
 'bridge_in_world':b'bridge_metal_25.p3d' in wrp.lower(),
 'expected_water_object':(b'pond_50x50' not in wrp.lower() and b'lake_50x50' not in wrp.lower()) if a.expected_water_object=='none' else (a.expected_water_object+'.p3d').encode() in wrp.lower(),
 'generated_materials_present':a.expected_materials>0 and len(material_entries)==a.expected_materials,
 'generated_textures_present':a.expected_textures>0 and len(texture_entries)==a.expected_textures,
 'compiled_tree_byte_parity':not mismatch,
 'no_raw_sources_or_vanilla_models':not any(k.endswith(('.png','.cpp','.p3d','.asc','.log')) for k in blob),
}
if a.extract_config:a.extract_config.write_bytes(cfg)
result={'status':'PASS_PACKED_CONTENT' if all(checks.values()) else 'FAIL',
        'checks':checks,'pbo_sha256':hashlib.sha256(data).hexdigest(),'pbo_bytes':len(data),
        'properties':properties,'entry_count':len(entries),'entries':entries,'mismatch':mismatch,
        'expected_materials':a.expected_materials,'expected_textures':a.expected_textures,
        'expected_water_object':a.expected_water_object,
        'wrp_version':struct.unpack_from('<I',wrp,4)[0] if wrp[:4]==b'OPRW' else None,
        'limits':['Binarized archive verified; not deployed or loaded in game.','No CE/navmesh/80-100-player acceptance.']}
a.out.parent.mkdir(parents=True,exist_ok=True)
a.out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='entries'},indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
