"""Freeze nine vanilla poses, and an import containing only the six NEW spans."""
from pathlib import Path
import hashlib,json,sys,struct
import xml.etree.ElementTree as ET
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/playtest'))
from verify_texture_grid_change import read
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    folder=ROOT/'tests/narva_bridge_v10'
    if folder.exists():raise ValueError('Fresh output required')
    original=ROOT/'tb/regional_outline_v3/baltic_regional_persisted_v3.wrp'
    assert sha(original)=='9bf50853799764571d4c3a7ce87c17583019af149bed93ac1e73f2c91c7c8c68'
    old=read(original)['objects'];assert len(old)==3
    fit=json.loads((ROOT/'evidence/narva/evidence/narva-fit.json').read_text())
    model=Path('P:/DZ/structures/roads/bridges/bridge_metal_25.p3d')
    assert sha(model)=='baf79ddd19e08cdcdbec99b15043a319d6b958a1b7884082c2ae069cf3f3cee2'
    measured=json.loads((ROOT/'evidence/navigation/vanilla-assets.json').read_text())
    asset=next(b for b in measured['bridges'] if b['sha256']==sha(model))
    template=ROOT/'tb/regional_foundation_v10/TemplateLibs/Narva_Vanilla.tml'
    tree=ET.parse(template)
    t=next(v for v in tree.getroot().findall('Template') if v.findtext('Name')=='bridge_metal_25')
    assert t.findtext('AutoCenter')=='1'
    centre_y=float(t.find('BoundingCenter').get('Y'))
    deck=11.; origin=deck-asset['central_roadway_raw_y'];import_y=origin-centre_y
    u=np.array(fit['axis_east_unit']);c=np.array(fit['bridge_centre_tb']);yaw=fit['heading_from_north_degrees']
    center_old=next(b for b in old if b['id']==16777216)
    rotation=list(struct.unpack('<12f',bytes.fromhex(center_old['matrix'])))[:9]
    objects=[];rows=[]
    for offset in range(-100,101,25):
        xz=c+offset*u
        prior=None
        if abs(offset)<=25:
            prior=min(old,key=lambda b:abs(struct.unpack('<12f',bytes.fromhex(b['matrix']))[9]-(xz[0]-200000)))
            raw=list(struct.unpack('<12f',bytes.fromhex(prior['matrix'])))
            xyz=[raw[9],raw[10]+2,raw[11]]
        else:
            xyz=[xz[0]-200000,origin,xz[1]]
            rows.append(f'"bridge_metal_25";{xz[0]:.6f};{xz[1]:.6f};{yaw:.6f};0.000000;0.000000;1.000000;{import_y:.6f};')
        objects.append(dict(offset_m=offset,existing_id=prior['id'] if prior else None,native_xyz=xyz,native_rotation=rotation,model='dz\\structures\\roads\\bridges\\bridge_metal_25.p3d',tb_xz=xz.tolist(),tb_absolute_elevation_m=import_y))
    corridor=next(v for v in asset['corridors'] if v['width_m']==18)
    clearance=deck+corridor['lowest_collision_relative_to_deck_m']-3
    assert clearance>=6 and len(rows)==6
    folder.mkdir(parents=True)
    txt=folder/'new_six_spans_absolute.txt';txt.write_text('\n'.join(rows)+'\n',encoding='ascii')
    receipt=dict(status='FROZEN_DESIGN_NOT_NATIVE',objects=objects,model_sha256=sha(model),template_sha256=sha(template),base_wrp_sha256=sha(original),new_six_import_sha256=sha(txt),deck_m=deck,water_envelope_m=3,opening_width_m=18,minimum_predicted_clearance_m=clearance,existing_operation='Raise the existing three objects by exactly2m; do not import duplicates',native_gate=dict(original_xz_and_rotation='EXACT',original_y_delta_m=2,original_y_tolerance_m=1e-6,new_xyz_tolerance_m=.001,new_rotation_tolerance=1e-7,reopen_canonical_records='EXACT'),limits=['Predicted geometry is not runtime collision acceptance','Piers constrain passage; regional boat route currently stalls near a pier'])
    (folder/'reference.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='objects'},indent=2))

if __name__=='__main__':main()
