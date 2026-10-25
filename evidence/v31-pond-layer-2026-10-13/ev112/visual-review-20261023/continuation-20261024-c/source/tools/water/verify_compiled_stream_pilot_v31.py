"""Read the packed ODOL models, derive WRP poses, compare saved MLOD surfaces.
No runtime claim. Records are emitted only if every binary model is present,
water/road faces survive, collision components survive and coordinates match.
"""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import Polygon
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'playtest'),'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/py3d',
             'C:/Users/guill/.agents/skills/dayz-p3d-debinarizer/scripts']
import py3d
from attach_navmesh import read_pbo


def xyz(v):return np.array([(p.x,p.y,p.z) for p in v])


def main():
    ap=argparse.ArgumentParser();ap.add_argument('pilot');ap.add_argument('--reader-root');a=ap.parse_args();out=Path(a.pilot)
    if a.reader_root:sys.path.insert(0,a.reader_root)
    from odol_reader import ODOL
    import odol_reader
    backend=dict(path=odol_reader.__file__,sha256=hashlib.sha256(Path(odol_reader.__file__).read_bytes()).hexdigest())
    control=ODOL.from_file('P:/DZ/water/streambed/streambed_leaf_long_straight.p3d')
    assert len(control.lods)==8 and not getattr(control,'lod_errors',{})
    rep=json.loads((out/'author-report.json').read_text());pbo=out/'packed/baltic_stream_pilot.pbo'
    _,props,entries=read_pbo(pbo);checks=[];records=[];polys={};water_vertices={}
    for inst in rep['instances']:
        name=inst['model'].split('\\')[-1];data=entries[name]
        path=out/'temp/baltic_stream_pilot'/name
        assert data==path.read_bytes() and data[:4]==b'ODOL'
        od=ODOL.from_file(str(path),strict=True);bc=od.model_info.bounding_center;bc=np.array([bc.x,bc.y,bc.z])
        assert not getattr(od,'lod_errors',{}) and len(od.lods)==4
        # The local v56 reader was not promoted: its review flagged missing
        # section-index bounds. Check every index here before consuming it;
        # this caller neither changes nor installs that external reader.
        for lod in od.lods:
            assert getattr(lod,'lod_end_ok',True)
            for section in lod.sections:
                assert -1<=section.texture_index<len(lod.textures)
                assert -1<=section.material_index<len(lod.materials)
        pos=(np.array(inst['origin'])+bc).astype(np.float32).astype(float)
        raw=py3d.P3D(open(out/'source/baltic_stream_pilot'/name,'rb'))
        vis=min(od.lods,key=lambda l:l.resolution)
        geo=min(od.lods,key=lambda l:abs(l.resolution-1e13));road=min(od.lods,key=lambda l:abs(l.resolution-3e15))
        A=np.array([p.coords for p in raw.lods[0].points])+inst['origin'];V=xyz(vis.vertices)+pos
        error=float(cKDTree(A).query(V)[0].max())
        road_count=0;water_count=0;water=[];wv=[]
        for section in vis.sections:
            mat=vis.materials[section.material_index].material_name if section.material_index>=0 else section.mat_name
            if 'water_streambed.rvmat' in mat:
                for ix in section.get_face_indices(vis.faces):
                    ids=list(vis.faces[ix].vertex_indices);water.append(Polygon(V[ids][:,[0,2]]));water_count+=1;wv.extend(V[ids])
        for section in road.sections:
            tex=road.textures[section.texture_index] if section.texture_index>=0 else ''
            if 'water_ext.paa' in tex:road_count+=len(section.get_face_indices(road.faces))
        expected_water=sum('water_streambed.rvmat' in f.material for f in raw.lods[0].faces)
        components=sum(ns.name.lower().startswith('component') for ns in geo.named_selections)
        ok=(water_count==road_count==expected_water and components==inst['collision_components'] and error<.001)
        checks.append(dict(model=name,pass_=ok,visual_to_source_max_error_m=error,water_faces=water_count,
                           water_road_faces=road_count,collision_components=components,geometry_properties=geo.named_properties,
                           bounding_centre=bc.tolist(),wrp_translation_rounding_m=(pos-np.array(inst['origin'])-bc).tolist(),
                           odol_bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
        polys.setdefault(inst['site'],[]).append(unary_union(water))
        water_vertices.setdefault(inst['site'],[]).append(np.unique(wv,axis=0))
        records.append(dict(site=inst['site'],piece='continuous',model=inst['model'],matrix=[1,0,0,0,1,0,0,0,1,*pos.tolist()]))
    connections={}
    for site,pp in polys.items():
        u=unary_union(pp)
        zz=np.load(out/(site+'-surfaces.npz'));instances=[i for i in rep['instances'] if i['site']==site]
        seam_errors=[]
        for j,inst in enumerate(instances[:-1]):
            ix=int(np.argmin(abs(zz['station']-inst['station'][1])));want=zz['water'][ix]
            va,vb=water_vertices[site][j:j+2]
            actual_a=va[cKDTree(va).query(want)[1]];actual_b=vb[cKDTree(vb).query(want)[1]]
            seam_errors.append(float(np.linalg.norm(actual_a-actual_b,axis=1).max()))
        connections[site]=dict(exactly_connected=u.geom_type=='Polygon',parts=1 if u.geom_type=='Polygon' else len(u.geoms),
                               adjacent_polygon_distance_max_m=max(float(x.distance(y)) for x,y in zip(pp[:-1],pp[1:])),
                               seam_3d_max_m=max(seam_errors))
    passed=all(c['pass_'] for c in checks) and all(c['exactly_connected'] and c['seam_3d_max_m']<1e-8 for c in connections.values())
    report=dict(status='BINARY_PASS' if passed else 'FAIL',
                pbo_sha256=hashlib.sha256(pbo.read_bytes()).hexdigest(),reader=backend,properties=props,models=checks,connections=connections,
                limitation='Packed geometry and derived float32 poses; engine water/collision and compiled WRP readback remain pending.')
    (out/'binary-review.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    if passed:(out/'records.json').write_text(json.dumps(records,indent=1),encoding='utf-8')
    print(json.dumps(dict(status=report['status'],models=len(checks),max_error_m=max(c['visual_to_source_max_error_m'] for c in checks),connections=connections,pbo_sha256=report['pbo_sha256']),indent=2))
    assert passed


if __name__=='__main__':main()
