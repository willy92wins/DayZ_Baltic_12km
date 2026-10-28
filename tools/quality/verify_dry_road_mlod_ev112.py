"""Saved-MLOD consumer independent of byte patcher and numeric solver."""
import os,time
START=time.monotonic()
for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[key]='1'
from pathlib import Path
import argparse,collections,hashlib,importlib.util,json,struct,sys
import numpy as np
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'water'))
from review_compact_collision_v31 import load,overlay,vertices
from mesh_quality_v31 import closed_component

# Independent anchors: never accept a replacement supplied only by the author.
ANCHORS={
    'deployed-surface-consumer-lineage-20261028/current-source-pins.json':'f17273f47dc0e331301ecb8b23d857814eacee6467851677213e6fb9e633b845',
    'pilot-kit7-fc-20261026/source/baltic_stream_pilot/cs_kit_118_0000.p3d':'bbf4d5e40dfcb3bf5216981f10cbf21db681d403ea51c4e20676956289207c5a',
    'dry-bed-road-candidate-20261028/kit-118-candidate.npz':'93168efe934d9ff8a95bde1ceff3e54d0667bb0b358b36c0b7c028a443fa707d',
    'pilot-visible-surface-extraction-20261028/models/cs_kit_118_0000.npz':'dcfc5504acfa35ec804d92cc10e9550e3412732eb10b7623d8105f8013fb37ab',
}

def require(ok,why):
    if not bool(ok):raise ValueError(why)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def face_key(tri):return tuple(sorted(tuple(v) for v in tri))
def normal_domains(lod,bed_count=None):
    referenced={v.normal_index for f in lod.faces for v in f.vertices}
    require(referenced==set(range(len(lod.facenormals))),'normal_domain_incomplete')
    if bed_count is not None:
        outside=[f for f in lod.faces if not all(v.point_index<bed_count for v in f.vertices)]
        require(all(v.normal_index>=bed_count for f in outside for v in f.vertices),'water_uses_bed_normal')

def normal_check(lod,faces,bed_count=None,up=False):
    points=np.array([p.coords for p in lod.points]);expected=np.zeros((bed_count,3)) if bed_count is not None else None
    for face in faces:
        ids=[v.point_index for v in face.vertices];tri=points[ids];n=np.cross(tri[1]-tri[0],tri[2]-tri[0]);length=np.linalg.norm(n);require(length>1e-9,'degenerate_face');n/=length
        if bed_count is not None:
            for i in ids:expected[i]+=n
        else:
            for v in face.vertices:require(np.linalg.norm(np.array(lod.facenormals[v.normal_index])-n)<=1e-6,'wrong_geometry_normal')
    if bed_count is not None:
        expected/=np.linalg.norm(expected,axis=1)[:,None]
        if up:expected=-expected
        normals=np.array(lod.facenormals[:bed_count]);require(np.max(np.linalg.norm(normals-expected,axis=1))<=1e-6,'wrong_bed_normal')

def check_saved(original,candidate,expected_grid,origin):
    oh,old,ob=load(original);nh,new,nb=load(candidate);require(oh==nh and len(ob)==len(nb)==4,'mlod_header')
    expected=expected_grid.reshape(-1,3)-origin;count=len(expected);bed=None
    for li in range(4):
        require(len(ob[li])==len(nb[li]),'lod_size')
        l0,l1=old[li],new[li];require((len(l0.points),len(l0.facenormals),len(l0.faces))==(len(l1.points),len(l1.facenormals),len(l1.faces)),'lod_counts')
        if li in (0,1,3):normal_domains(l1,count if li in (0,3) else None)
        a=np.frombuffer(ob[li],np.uint8);b=np.frombuffer(nb[li],np.uint8);mask=np.zeros(len(a),bool);n=len(l0.points)
        if li in (0,3):
            for i in range(count):mask[28+16*i+4:28+16*i+8]=True;mask[28+16*n+12*i:28+16*n+12*i+12]=True
        elif li==1:
            for i in range(n):mask[28+16*i+4:28+16*i+8]=True
            mask[28+16*n:28+16*n+12*len(l0.facenormals)]=True
        require(np.array_equal(a[~mask],b[~mask]),'unauthorized_bytes_lod_'+str(li))
        p0=np.array([p.coords for p in l0.points]);p1=np.array([p.coords for p in l1.points])
        if len(p0):require(np.array_equal(p0.min(0),p1.min(0)) and np.array_equal(p0.max(0),p1.max(0)),'bounds_changed')
        require([p.mass for p in l0.points]==[p.mass for p in l1.points],'mass_changed')
        if li in (0,3):
            require(np.array_equal(p1[:count],expected),'bed_not_numeric_candidate')
            faces=[f for f in l1.faces if all(v.point_index<count for v in f.vertices)]
            require(len(faces)==2*(len(expected_grid)-1)*38,'bed_face_count')
            require(all(v.normal_index==v.point_index for f in faces for v in f.vertices),'surface_normal_mapping')
            normal_check(l1,faces,count,li==3)
            tri=vertices(l1,faces)
            if li==0:bed=tri
            else:require(np.array_equal(tri,bed),'roadway_visual_difference')
    roof=[];comp_checks=[];assigned=[];point_assign=[];new_geo=new[1];old_geo=old[1]
    visible={tuple(x[[0,2]]):float(x[1]) for x in expected};require(len(visible)==len(expected),'ambiguous_visible_xz')
    for name,selection in new_geo.selections.items():
        faces=list(selection.faces);tri=vertices(new_geo,faces);prev=vertices(old_geo,list(old_geo.selections[name].faces));closure=closed_component(tri);before=closed_component(prev)
        require(closure['closed'] and closure['signed_volume']<0,'open_or_wrong_winding_component')
        require(abs(closure['signed_volume']-before['signed_volume'])<=1e-9,'prism_volume_changed')
        pts=np.array([p.coords for p in selection.points]);require(len(pts)==6 and len(faces)==8,'component_family')
        top=[];bottom=[]
        for point in pts:
            key=tuple(point[[0,2]]);require(key in visible,'geometry_xz_unmapped')
            y=visible[key]
            if point[1]==y:top.append(key)
            elif point[1]==y-180/512:bottom.append(key)
            else:raise ValueError('geometry_not_saved_visual_prism')
        require(len(top)==len(bottom)==3 and sorted(top)==sorted(bottom),'prism_pairing')
        n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n/=np.linalg.norm(n,axis=1)[:,None]
        distance=np.einsum('fpc,fc->fp',pts[None]-tri[:,0,None],n);require(distance.min()>=-1e-6,'nonconvex_component')
        roof.extend(tri[n[:,1]<-1e-10]);assigned.extend(map(id,faces));point_assign.extend(map(id,selection.points));normal_check(new_geo,faces)
        comp_checks.append(dict(name=name,volume=closure['signed_volume']))
    require(len(assigned)==len(set(assigned))==len(new_geo.faces),'geometry_face_assignment')
    require(len(point_assign)==len(set(point_assign))==len(new_geo.points),'geometry_point_assignment')
    require(collections.Counter(map(face_key,bed))==collections.Counter(map(face_key,roof)),'roof_not_exact_visible_cover')
    contact=overlay(bed,np.array(roof));self_contact=overlay(bed,bed,vertical_limit=1e-6,horizontal_limit=0.)
    require(all(contact['checks'].values()) and all(self_contact['checks'].values()) and max(abs(self_contact['minimum_pair_height_error_m']),abs(self_contact['maximum_height_error_m']))<=1e-6,'overlay_failure')
    return dict(status='SAVED_MLOD_SEMANTICS_VERIFIED',source_sha256=sha(original),candidate_sha256=sha(candidate),components=len(comp_checks),points=len(new_geo.points),faces=len(new_geo.faces),mass=sum(p.mass for p in new_geo.points),contact=contact,self_contact=self_contact,non_authorized_bytes_exact=True,bounds_exact=True)

def run(root,w,raw,out,meter):
    for name,digest in ANCHORS.items():require(sha(root/name)==digest,'independent_anchor:'+name)
    pins=json.loads((raw/'inputs.json').read_bytes())
    for p,d in pins.items():require(sha(p)==d,'input_changed:'+p)
    source_root=root/'pilot-kit7-fc-20261026/source';model='baltic_stream_pilot/cs_kit_118_0000.p3d';target=raw/'source'/model;before=sha(target)
    actual={p.relative_to(raw/'source').as_posix() for p in (raw/'source').rglob('*') if p.is_file()};require(actual=={model},'unexpected_overlay_files')
    effective=json.loads((raw/'effective-models.json').read_bytes());require(len(effective)==201,'effective_universe')
    lineage=json.loads((root/'deployed-surface-consumer-lineage-20261028/current-source-pins.json').read_bytes())
    expected_keys={Path(p).relative_to(source_root).as_posix() for p in lineage if p.endswith('.p3d')};require(set(effective)==expected_keys,'effective_identity')
    for name,d in effective.items():require(sha(target if name==model else source_root/name)==d,'effective_hash')
    number=np.load(root/'dry-bed-road-candidate-20261028/kit-118-candidate.npz')['grid'];original=np.load(root/'pilot-visible-surface-extraction-20261028/models/cs_kit_118_0000.npz')['source_grid'];grid=number[:len(original)];origin=np.array([8262.,7.,8934.])
    result=check_saved(source_root/model,target,grid,origin)
    # All joins of first model into the next strip stay equal to source; no new seam.
    require(np.array_equal(grid[-1],original[-1]),'changed_model_joint')
    for p,d in pins.items():require(sha(p)==d,'input_changed_after:'+p)
    for name,digest in ANCHORS.items():require(sha(root/name)==digest,'independent_anchor_after:'+name)
    require(sha(target)==before,'candidate_changed_during_check')
    result.update(status='MLOD_OFFLINE_VERIFIED',effective_models=201,unchanged_models=200,join_exact=True,measurement=meter.memory(),limits='Saved MLOD only. Compilation, world placement, engine contact, RAM and visual acceptance pending.')
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('worktree',type=Path);ap.add_argument('raw',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(exist_ok=False)
    sp=importlib.util.spec_from_file_location('meter',HERE/'water_constraint_diagnostic_ev112.py');meter=importlib.util.module_from_spec(sp);sp.loader.exec_module(meter);meter.STARTED=START;meter.MAX_SECONDS=300;stop=meter.bounded(a.output)
    try:result=run(a.root,a.worktree,a.raw,a.output,meter);meter.dump(a.output/'report.json',result);print(json.dumps(result))
    except Exception as e:meter.dump(a.output/'failure.json',dict(type=type(e).__name__,error=str(e),measurement=meter.memory()));raise
    finally:stop.set()
