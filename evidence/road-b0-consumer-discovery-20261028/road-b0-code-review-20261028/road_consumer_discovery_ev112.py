"""Bounded RoadB0 subset: local full faces/materials, not placement or driving."""
import time
START=time.monotonic()
from pathlib import Path
import argparse,importlib,json,math,struct,sys,traceback
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import road_asset_catalog_ev112 as cat
import build_prism_b3e2_ev112 as runtime
from deployed_surface_inventory_ev112 import sections
from shapely import Polygon,union_all
meter=cat.meter;sha=meter.sha;dump=meter.dump
CFG=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/CfgConvert/CfgConvert.exe')
CFG_SHA='4c4fc15ef9773b42b4191155d4e243d8c95d3156cf7b6f24e7d84dea7cd15a4c'
SELECTED={'Parts/asf1_25.p3d':'d72224ed23c03e2cc2d265aba895d534af4b5a8039adc192b783ef856984d69b','Parts/asf2_25.p3d':'4ce4b0a76b017d023b2c26e05dc144d26aae5b0272314790cae214746c1257ca','Parts/asf1_10 100.p3d':'2d52f9e5123d74d27ec91fe2f52dacf13e863e4a149c94e460ce675fcfd480ec'}
CONFIG_SHA='1c7aad19b4a2a92adbc4c46ddc6a1eda5a83aac33c81478fa4dfbc31f80f068c'
CAT_SHA='fb8ac8972e834c21084b2f22c6dd7409daeb052c6c466d97a6ea4929ad5f0427'
require=cat.require

def faces(lod):
    points=[cat.xyz(p) for p in lod.vertices]
    require(list(struct.iter_unpack('<fff',lod.vertex_raw))==[tuple(p) for p in points],'raw_decoded_vertices')
    assignment,materials=sections(lod);rows=[];polygons=[];by_material={}
    for fi,face in enumerate(lod.faces):
        ids=list(face.vertex_indices);require(len(ids) in (3,4) and all(0<=i<len(points) for i in ids),'face_indices')
        xyz=[points[i] for i in ids];poly=Polygon([(p[0],p[2]) for p in xyz]);si=int(assignment[fi]);section=materials[si]
        # Retain every source face, including vertical/degenerate projections.
        state='AREA' if poly.is_valid and poly.area>0 else 'DEGENERATE_OR_INVALID'
        rows.append(dict(face=fi,vertex_indices=ids,xyz=xyz,section=si,material=section['material'],texture=section['texture'],projection=state))
        if state=='AREA':polygons.append(poly);by_material.setdefault((section['material'],section['texture']),[]).append(poly)
    footprint=union_all(polygons)
    return dict(faces=rows,face_count=len(rows),bbox=cat.bbox(points),sections=materials,
                projection_area_m2=float(footprint.area),projection_wkt=footprint.wkt,
                material_masks=[dict(material=k[0],texture=k[1],area_m2=float((g:=union_all(v)).area),wkt=g.wkt) for k,v in by_material.items()],
                degenerate_projection_faces=sum(r['projection']!='AREA' for r in rows))

def discovery_fields(roadway):
    require(isinstance(roadway,bool),'roadway_not_boolean')
    return dict(consumer_observed='UNKNOWN',pivot_convention='UNKNOWN',usable_width='UNKNOWN',shoulder_material='UNKNOWN',roadway_present=roadway,crossings_exact='UNKNOWN')

def status(rows):
    required=('consumer_observed','pivot_convention','usable_width','shoulder_material','roadway_present','crossings_exact')
    require(bool(rows),'empty_discovery')
    for row in rows:
        require(all(k in row for k in required),'missing_discovery_field')
        require(isinstance(row['roadway_present'],bool),'roadway_not_boolean')
        require(row['usable_width']=='UNKNOWN' or (isinstance(row['usable_width'],(int,float)) and math.isfinite(row['usable_width']) and row['usable_width']>0),'invalid_width')
    return 'INCONCLUSIVE_DISCOVERY' if any(row[k]=='UNKNOWN' for row in rows for k in required) else 'DISCOVERY_COMPLETE_NOT_PLACEMENT'

def run(output):
    pins={str(cat.PBO):cat.PBO_SHA,str(CFG):CFG_SHA,str(HERE/'road_asset_catalog_ev112.py'):CAT_SHA,
          **{str(cat.READER/n):h for n,h in cat.READER_PINS.items()},**{str((HERE/n).resolve()):h for n,h in cat.HELPER_PINS.items()},
          **{str(p):h for p,h in runtime.HELPERS.items()},str(HERE/'build_prism_b3e2_ev112.py'):'b131794d75a2748f40dfdd87e5e01389cf6434ca2f9b160253f70f241f538cbb'}
    cat.check_pins(pins);dump(output/'inputs.json',pins)
    raw,props,entries=cat.read_pbo(cat.PBO);require(cat.digest(raw)==cat.PBO_SHA,'pbo_changed');del raw
    require(props.get('prefix')=='dz\\structures\\roads' or props.get('prefix')=='dz/structures/roads','prefix')
    require(cat.digest(entries['config.bin'])==CONFIG_SHA,'config_changed')
    for name,h in SELECTED.items():require(cat.digest(entries[name])==h,'selected_changed:'+name)
    (output/'installed-config.bin').write_bytes(entries['config.bin'])
    runtime.run_process([str(CFG),'-txt','-dst',str(output/'installed-config.cpp'),str(output/'installed-config.bin')],output/'decode.log',min(60,max(1,120-(time.monotonic()-START))))
    cpp=(output/'installed-config.cpp').read_text(encoding='utf-8-sig');require(bool(cpp.strip()),'empty_decoded_config')
    # This is source evidence only: declarations do not imply WRP instances.
    source_lines=[dict(line=i+1,text=s.strip()) for i,s in enumerate(cpp.splitlines()) if 'StaticObj_Roads_Partasf' in s or any(n[6:-4] in s for n in SELECTED)]
    dump(output/'config-source-observations.json',dict(config_bin_sha256=CONFIG_SHA,decoded_sha256=sha(output/'installed-config.cpp'),lines=source_lines,consumer_observed='UNKNOWN',limit='Declarations only; no WRP/RoadNetwork/runtime consumer attested.'))
    sys.path.insert(0,str(cat.READER));backend=importlib.import_module('odol_reader');cat.loaded_reader_binding();summaries=[]
    for number,(name,h) in enumerate(SELECTED.items()):
        od=backend.ODOL.from_bytes(entries[name],strict=True);meta=cat.model_metadata(od);local=[]
        for li,lod in enumerate(od.lods):
            role=meta['lods'][li]['role']
            if role not in ('Visual','Roadway'):continue
            local.append(dict(lod=li,role=role,resolution=float(lod.resolution),stored_center=cat.xyz(lod.b_center),reader_applied_offset=[0,0,0],**faces(lod)))
        path=output/('local-faces-'+str(number)+'.json');dump(path,dict(model=name,sha256=h,bounding_center=meta['bounding_center'],lods=local,space='stored_local_raw',pivot_convention='UNKNOWN'))
        summaries.append(dict(model=name,sha256=h,local_geometry_sha256=sha(path),bounding_center=meta['bounding_center'],lods=[{k:v for k,v in row.items() if k not in ('faces','projection_wkt','material_masks')} for row in local],**discovery_fields(meta['roadway_present'])))
    del entries;cat.check_pins(pins);measurement=meter.memory()
    require(measurement['seconds']<=120 and max(measurement['peak_resident_bytes'],measurement['peak_commit_bytes'])<=2*1024**3,'resource_budget')
    return dict(status=status(summaries),models=summaries,sources=pins,config_bin_sha256=CONFIG_SHA,decoded_config_sha256=sha(output/'installed-config.cpp'),coverage=dict(selected=3,catalog_models=265,wrp_instances='NOT_READ',crossings='NOT_EVALUATED',all_visual_lods_and_roadway=True),elapsed_s=measurement['seconds'],peak_bytes=max(measurement['peak_resident_bytes'],measurement['peak_commit_bytes']),measurement=measurement,no_placement_build_or_dayz=True,limits=['Local geometry and config declarations only.','No native pivot/width/material friction proof.','World/crossing/access footprint remains unmeasured.','No vanilla coordinates or binaries for public release.'])

def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(exist_ok=False)
    meter.STARTED=START;meter.MAX_SECONDS=120;meter.MAX_BYTES=2*1024**3;stop=meter.bounded(a.output)
    try:r=run(a.output);dump(a.output/'report.json',r);return 0 if r['status']=='DISCOVERY_COMPLETE_NOT_PLACEMENT' else 2
    except Exception as e:dump(a.output/'report.json',dict(status='INCONCLUSIVE_DISCOVERY',error=type(e).__name__+':'+str(e),traceback=traceback.format_exc(),measurement=meter.memory()));return 2
    finally:stop.set()

if __name__=='__main__':raise SystemExit(main())
