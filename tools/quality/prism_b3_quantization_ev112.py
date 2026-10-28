"""Read-only B3C census and numerical witness. Never writes a model or runs DayZ."""
import os,time
START=time.monotonic()
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[name]='1'
from pathlib import Path
from fractions import Fraction
from functools import lru_cache
import argparse,collections,json,struct,sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import prism_b3_binary_ev112 as binary
from review_compact_collision_v31 import load,vertices,overlay
from mesh_quality_v31 import closed_component
meter=binary.meter
T=180/512
PLANE=1e-6
MAX_PAIR=100000
MAX_TOTAL=1000000

def require(ok,message):
    if not bool(ok):raise ValueError(message)

class DomainBudget(ValueError):pass

def bits(x):return np.asarray(x,dtype='<f4').view('<u4')
def same_bits(a,b):return np.array_equal(bits(a),bits(b))
def float_at(b):return struct.unpack('<f',struct.pack('<I',int(b)))[0]
def ordered(x):
    b=int(bits(x));return (~b)&0xffffffff if b&0x80000000 else b^0x80000000
def at_ordered(k):return float_at(k^0x80000000 if k&0x80000000 else (~k)&0xffffffff)

def fraction_bits(b):
    sign=-1 if b&0x80000000 else 1;e=(b>>23)&255;m=b&0x7fffff
    require(e!=255,'nonfinite_rational')
    if e:m|=1<<23
    power=(e-127-23) if e else -149
    return sign*Fraction(m)*(Fraction(2)**power)

@lru_cache(maxsize=250000)
def round_fraction32(q):
    """Exact rational nearest/even oracle, independent of numpy rounding."""
    q=Fraction(q);neg=q<0;q=abs(q)
    require(q<=fraction_bits(0x7f7fffff),'oracle_overflow_domain')
    lo,hi=0,0x7f7fffff
    while lo<hi:
        mid=(lo+hi+1)//2
        if fraction_bits(mid)<=q:lo=mid
        else:hi=mid-1
    out=lo
    if fraction_bits(lo)!=q:
        a=q-fraction_bits(lo);b=fraction_bits(lo+1)-q
        if b<a or (b==a and lo&1):out=lo+1
    return float_at(out|(0x80000000 if neg else 0))

def domain(low,high,cap=MAX_PAIR):
    require(np.isfinite([low,high]).all() and low<=high,'domain_bounds')
    a=np.float32(low);b=np.float32(high)
    if float(a)<low:a=np.nextafter(a,np.float32(np.inf),dtype=np.float32)
    if float(b)>high:b=np.nextafter(b,np.float32(-np.inf),dtype=np.float32)
    first,last=ordered(a),ordered(b);size=max(0,last-first+1)
    if size>cap:raise DomainBudget(f'INCONCLUSIVE_DOMAIN_BUDGET:{size}>{cap}')
    return np.asarray([at_ordered(i) for i in range(first,last+1)],dtype='<f4')

def y_frames(y,centre,origin,translation):
    y=np.asarray(y,float);local=(y-centre).astype('<f4')
    return local,(y+origin).astype('<f4'),(local.astype(float)+translation).astype('<f4')

def oracle_op(a,b,subtract=False):
    exact=Fraction(float(a))+(-1 if subtract else 1)*Fraction(float(b))
    if not exact and a==0 and b==0:
        negative=bool(np.signbit(a)) and (not bool(np.signbit(b)) if subtract else bool(np.signbit(b)))
        return float_at(0x80000000 if negative else 0)
    return round_fraction32(exact)

def oracle_frames(y,centre,origin,translation):
    local=oracle_op(y,centre,True)
    return local,oracle_op(y,origin),oracle_op(local,translation)

def verify_domain_oracle(values,centre,origin,translation):
    calculated=np.asarray(y_frames(values,centre,origin,translation)).T
    independent=np.asarray([oracle_frames(y,centre,origin,translation) for y in values])
    require(same_bits(calculated,independent),'rational_domain_disagreement')

def plane_at(top,xz):
    u,v=top[1]-top[0],top[2]-top[0]
    ab=np.linalg.solve(np.column_stack((u[[0,2]],v[[0,2]])),(np.asarray(xz)-top[0,[0,2]]).T).T
    return top[0,1]+ab[...,0]*u[1]+ab[...,1]*v[1]

def source_groups(lod):
    xyz=np.asarray([p.coords for p in lod.points],float)
    pi={id(p):i for i,p in enumerate(lod.points)};fi={id(f):i for i,f in enumerate(lod.faces)}
    groups={};usedp=[];usedf=[]
    for name,sel in lod.selections.items():
        ids=[pi[id(p)] for p in sel.points];fs=[fi[id(f)] for f in sel.faces]
        require(len(ids)==6 and len(fs)==8 and len(set(ids))==6 and len(set(fs))==8,'source_component_counts')
        pairs={}
        for i in ids:pairs.setdefault(tuple(xyz[i,[0,2]]),[]).append(i)
        require(len(pairs)==3 and all(len(p)==2 for p in pairs.values()),'source_pairs')
        pairs=[sorted(p,key=lambda i:xyz[i,1]) for p in pairs.values()]
        groups[name.lower()]=dict(ids=ids,faces=fs,pairs=pairs)
        usedp+=ids;usedf+=fs
    require(len(groups)==len(lod.selections) and sorted(usedp)==list(range(len(xyz))) and sorted(usedf)==list(range(len(lod.faces))),'source_coverage')
    return xyz,groups

def faces_bits(tri):return binary.face_counter(bits(tri))
def unit_normals(tri):
    n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);length=np.linalg.norm(n,axis=1)
    require((length>0).all(),'degenerate_triangle');return n/length[:,None]

def census(mlod,od,origin,matrix,known_prefix=None):
    src,groups=source_groups(mlod);geo=od.lods[1];centre=binary.old.xyz([od.model_info.bounding_center])[0]
    binary.pose_check(matrix,origin,centre)
    dec=np.frombuffer(geo.vertex_raw,'<f4').reshape(-1,3).astype(float)
    require(same_bits(dec,binary.old.xyz(geo.vertices)),'raw_decode_disagreement')
    named={s.name.lower():s for s in geo.named_selections};require(set(named)==set(groups) and len(named)==len(geo.named_selections),'component_names')
    world_src=(src+origin).astype('<f4').astype(float);world_dec=(dec+np.asarray(matrix)[9:]).astype('<f4').astype(float)
    rows=[];mismatches=[];noncomparable=[];mapped={};all_vertices=[];all_faces=[]
    names=list(named);prefix=names.index(known_prefix)+1 if known_prefix is not None else len(names)
    for ordinal,name in enumerate(names):
        group=groups[name];sel=named[name];ids=group['ids'];did=list(sel.selected_vertices);fis=list(sel.selected_faces)
        require(len(did)==6 and len(fis)==8 and len(set(did))==6 and len(set(fis))==8,'decoded_component_counts')
        require(all(0<=i<len(dec) for i in did) and all(0<=i<len(geo.faces) for i in fis),'decoded_component_indices')
        all_vertices+=did;all_faces+=fis
        predicted=(src[ids]-centre).astype('<f4').astype(float)
        lookup=collections.defaultdict(list)
        for i in did:lookup[tuple(dec[i])].append(i)
        matches=[lookup[tuple(p)] for p in predicted]
        if any(len(x)!=1 for x in matches) or len({x[0] for x in matches})!=6:
            noncomparable.append(dict(component=name,reason='NONUNIQUE_OR_MISSING_EXACT_LOCAL_MAPPING',predicted=predicted.tolist(),decoded=dec[did].tolist()))
            rows.append(dict(component=name,status='NONCOMPARABLE',ordinal=ordinal));continue
        mapping=dict(zip(ids,[x[0] for x in matches]));mapped.update(mapping);reverse={v:k for k,v in mapping.items()}
        sf=np.asarray([[v.point_index for v in mlod.faces[i].vertices] for i in group['faces']],int)
        cf=np.asarray([list(geo.faces[i].vertex_indices)[::-1] for i in fis],int)
        if any(i not in reverse for i in cf.flat):
            noncomparable.append(dict(component=name,reason='FACE_OUTSIDE_COMPONENT'));rows.append(dict(component=name,status='NONCOMPARABLE',ordinal=ordinal));continue
        source_keys=collections.Counter(binary.key(np.asarray(f)[:,None]) for f in sf)
        decoded_keys=collections.Counter(binary.key(np.asarray([reverse[i] for i in f])[:,None]) for f in cf)
        topology=source_keys==decoded_keys
        s_tri=world_src[sf];d_tri=world_dec[cf]
        delta=world_dec[[mapping[i] for i in ids]]-world_src[ids]
        local_bits=bits(predicted)!=bits(dec[[mapping[i] for i in ids]])
        world_bits=bits(world_src[ids])!=bits(world_dec[[mapping[i] for i in ids]])
        top={hi for lo,hi in group['pairs']}
        for j,i in enumerate(ids):
            if world_bits[j].any() or local_bits[j].any():
                d=mapping[i];mismatches.append(dict(component=name,source_index=i,compiled_index=d,kind='roof' if i in top else 'base',local_value_equal=bool(np.array_equal(predicted[j],dec[d])),local_bit_difference=local_bits[j].tolist(),world_value_difference=(delta[j]!=0).tolist(),world_bit_difference=world_bits[j].tolist(),source_local=src[i].tolist(),compiled_local=dec[d].tolist(),source_world=world_src[i].tolist(),compiled_world=world_dec[d].tolist(),world_residual_m=delta[j].tolist(),world_ulp_m=np.abs(np.spacing(world_src[i].astype('<f4'))).astype(float).tolist()))
        corresponding=world_dec[np.asarray([[mapping[i] for i in f] for f in sf])]
        normals=float(np.linalg.norm(unit_normals(s_tri)-unit_normals(corresponding),axis=1).max()) if topology else None
        face_value_missing=sum((binary.face_counter(s_tri)-binary.face_counter(d_tri)).values())
        face_bit_missing=sum((faces_bits(s_tri)-faces_bits(d_tri)).values())
        rows.append(dict(component=name,status='COMPARABLE',ordinal=ordinal,in_r1_local_checked_prefix=ordinal<prefix,topology_exact=topology,local_bits_different=int(local_bits.sum()),world_values_different=int((delta!=0).sum()),world_bits_different=int(world_bits.sum()),face_value_missing=face_value_missing,face_bit_missing=face_bit_missing,maximum_world_residual_m=np.abs(delta).max(axis=0).tolist(),maximum_geometric_normal_l2_change=normals))
    require(sorted(all_vertices)==list(range(len(dec))) and sorted(all_faces)==list(range(len(geo.faces))),'decoded_coverage')
    comparable=[x for x in rows if x['status']=='COMPARABLE']
    summary=dict(components=len(groups),vertices=len(src),faces=len(mlod.faces),comparable=len(comparable),noncomparable=len(noncomparable),local_value_match_all=not noncomparable,local_bit_differences=sum(x['local_bits_different'] for x in comparable),world_value_differences=sum(x['world_values_different'] for x in comparable),world_bit_differences=sum(x['world_bits_different'] for x in comparable),face_value_missing=sum(x['face_value_missing'] for x in comparable),face_bit_missing=sum(x['face_bit_missing'] for x in comparable),r1_local_checked_prefix=prefix,new_local_components=len(groups)-prefix,topology_exact_all=all(x['topology_exact'] for x in comparable) and not noncomparable)
    return dict(status='CENSUS_COMPLETE' if not noncomparable else 'CENSUS_INCONCLUSIVE',summary=summary,components=rows,mismatches=mismatches,noncomparable=noncomparable,centre=centre.tolist(),frame_note='Only local prediction versus vertex_raw is empirical compiler evidence. Both world frames are calculated by this instrument. B3B remains REJECTED_BINARY.'),mapped

def solve_pair(current,expected_plane,centre,origin,translation,bbox,remaining=MAX_TOTAL):
    values=domain(expected_plane-PLANE,expected_plane+PLANE,min(MAX_PAIR,remaining))
    top=values.astype(float);base=(top-T).astype('<f4').astype(float)
    lo,hi=bbox
    ok=(top-base==T)&(np.abs(top-expected_plane)<=PLANE)&(np.abs(base-(expected_plane-T))<=PLANE)
    ok&=(base>=lo)&(top<=hi)
    # Conservative extremum guard; unchanged extrema are allowed.
    if current[0] in (lo,hi):ok&=base==current[0]
    if current[1] in (lo,hi):ok&=top==current[1]
    lt,st,dt=y_frames(top,centre,origin,translation);lb,sb,db=y_frames(base,centre,origin,translation)
    for v in (top,base):verify_domain_oracle(v,centre,origin,translation)
    ok&=(bits(st)==bits(dt))&(bits(sb)==bits(db))
    indices=np.flatnonzero(ok)
    if not len(indices):return dict(status='NO_WITNESS_IN_THIS_PAIR_DOMAIN',domain_size=len(values),eligible=0,plane_y=expected_plane,domain_low=expected_plane-PLANE,domain_high=expected_plane+PLANE,rational_domain_values_verified=2*len(values))
    index=min(indices,key=lambda i:(abs(top[i]-current[1])+abs(base[i]-current[0]),top[i]))
    result=[float(base[index]),float(top[index])]
    return dict(status='PAIR_WITNESS',domain_size=len(values),eligible=len(indices),plane_y=expected_plane,before=list(map(float,current)),after=result,maximum_move_m=max(abs(result[i]-current[i]) for i in (0,1)),rational_frames_verified=True,rational_domain_values_verified=2*len(values),reported_local_thickness=float(lt[index])-float(lb[index]),reported_world_thickness=float(st[index])-float(sb[index]),thickness_contract_frame='MLOD exact; local/world differences reported, not additional filters')

def control_gate(control):
    s=control['summary']
    return (control['status']=='CENSUS_COMPLETE' and s['comparable']==s['components'] and not s['noncomparable'] and s['topology_exact_all'] and s['local_bit_differences']==s['world_bit_differences']==s['face_bit_missing']==0)

def feasibility(original_lods,candidate_lods,od,origin,matrix,selected,candidate_census):
    if candidate_census['noncomparable'] or not candidate_census['summary']['topology_exact_all'] or candidate_census['summary']['local_bit_differences']:
        return dict(status='INCONCLUSIVE_NUMERIC_MODEL_DOMAIN',reason='local correspondence or bits/topology not established')
    allowed={s.lower() for s in selected}
    for item in candidate_census['mismatches']:
        if item['component'] not in allowed or any(item['world_bit_difference'][i] for i in (0,2)):
            return dict(status='INCONCLUSIVE_Y_DOMAIN',reason='mismatch outside authorized Y domain',case=item)
    source,sg=source_groups(original_lods[1]);current,cg=source_groups(candidate_lods[1]);require(set(sg)==set(cg),'source_group_mismatch')
    new=current.copy();centre=binary.old.xyz([od.model_info.bounding_center])[0];translation=np.asarray(matrix)[9:]
    bbox=(float(current[:,1].min()),float(current[:,1].max()));rows=[];total=0;conflicts=[];authorized=[]
    for name in sorted(allowed):
        require(name in cg,'unauthorized_component');authorized+=cg[name]['ids']
        old_top=source[[hi for lo,hi in sg[name]['pairs']]]
        for lo,hi in cg[name]['pairs']:
            expected=float(plane_at(old_top,current[hi,[0,2]]))
            try:r=solve_pair(current[[lo,hi],1],expected,centre[1],origin[1],translation[1],bbox,MAX_TOTAL-total)
            except DomainBudget as e:return dict(status='INCONCLUSIVE_DOMAIN_BUDGET',reason=str(e),pairs=rows,domain_values_seen=total)
            r.update(component=name,source_indices=[lo,hi]);rows.append(r);total+=r['domain_size']
            if r['status']!='PAIR_WITNESS':conflicts.append(r)
            else:new[[lo,hi],1]=r['after']
    if conflicts:return dict(status='NO_WITNESS_IN_THIS_Y_DOMAIN',conflicts=conflicts,pairs=rows,domain_values_seen=total,not_global_unsat=True)
    require(len(set(authorized))==72,'authorized_domain')
    mask=np.zeros(len(current),bool);mask[authorized]=True
    require(same_bits(new[~mask],current[~mask]) and same_bits(new[:,[0,2]],current[:,[0,2]]),'outside_authorized_y')
    require(same_bits([new.min(0),new.max(0)],[current.min(0),current.max(0)]),'geometry_bbox_changed')
    other=np.concatenate([np.asarray([p.coords for p in lod.points],float).reshape(-1,3) for i,lod in enumerate(candidate_lods) if i!=1])
    full=np.concatenate((current,other));changed=np.concatenate((new,other));require(same_bits([full.min(0),full.max(0)],[changed.min(0),changed.max(0)]),'model_bbox_changed')
    pred=(new-centre).astype('<f4').astype(float);world=(pred+translation).astype('<f4').astype(float);source_world=(new+origin).astype('<f4').astype(float)
    require(same_bits(world,source_world),'witness_world_frame_mismatch')
    require(same_bits([pred.min(0),pred.max(0)],[binary.old.xyz(od.lods[1].vertices).min(0),binary.old.xyz(od.lods[1].vertices).max(0)]),'predicted_compiled_bbox_changed')
    face_ids=np.asarray([[v.point_index for v in f.vertices] for f in candidate_lods[1].faces]);max_plane=0.;closure=[]
    for name in sorted(allowed):
        g=cg[name];old_top=source[[hi for lo,hi in sg[name]['pairs']]]
        for lo,hi in g['pairs']:
            expect=float(plane_at(old_top,new[hi,[0,2]]));error=max(abs(new[hi,1]-expect),abs(new[lo,1]-(expect-T)));max_plane=max(max_plane,error)
            require(error<=PLANE and new[hi,1]-new[lo,1]==T,'witness_plane_thickness')
        tri=new[face_ids[g['faces']]];closed=closed_component(tri);require(closed['closed'] and closed['signed_volume']<0,'witness_closed_winding')
        normals=unit_normals(tri)
        require(min(float(((new[g['ids']]-t[0])@n).min()) for t,n in zip(tri,normals))>=-1e-6,'witness_convexity')
        closure.append(dict(component=name,closed=True,signed_volume=closed['signed_volume']))
    tri=world[face_ids][:,::-1];normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);roof=tri[normal[:,1]>1e-10]
    bed=vertices(candidate_lods[0],[f for f in candidate_lods[0].faces if 'water_streambed.rvmat' not in f.material])+origin
    over=overlay(bed,roof);require(all(over['checks'].values()),'witness_overlay')
    changed_ids=np.flatnonzero(np.any(bits(current)!=bits(new),axis=1))
    witness=[dict(source_index=int(i),before=current[i].tolist(),after=new[i].tolist()) for i in changed_ids]
    return dict(status='FEASIBILITY_ONLY',pairs=rows,domain_values_seen=total,changed_vertices=len(witness),witness=witness,maximum_plane_error_m=max_plane,maximum_y_move_m=float(np.abs(new[:,1]-current[:,1]).max()),source_and_predicted_bbox_exact=True,world_frames_bit_exact=True,other_lods_unchanged=True,closure=closure,overlay=over,centre_fixed=centre.tolist(),translation_fixed=translation.tolist(),compiled_model_info_bbox=dict(min=binary.old.xyz([od.model_info.bbox_min])[0].tolist(),max=binary.old.xyz([od.model_info.bbox_max])[0].tolist()),limits=['Numerical witness JSON only. No model authored, compiler invoked, engine algorithm or future compiled centre certified.','Future author must rederive Geometry normals; prior positions_only/normals_only experiment does not certify new Y.','700dry/723wet and X/Z remain unchanged; B3B stays REJECTED_BINARY and original47FAIL21uncertain remain open.'])

def run(root,output):
    contract=root/'prism-b3-binary-replay-20261028/contract-r1.json'
    require(meter.sha(contract)=='5df5009176342658eb7b31c7c099e643c9e99cc898d2a14f319858a9df391244','contract_identity')
    c=json.loads(contract.read_bytes());pins=dict(c['pins']);pins[str(contract)]=meter.sha(contract)
    for p,h in pins.items():require(meter.sha(p)==h,'input_changed:'+p)
    recorded={}
    for p in (Path(__file__),HERE/'test_prism_b3_quantization_ev112.py',HERE.parent.parent/'plans/ev112-prism-b3-quantization-discovery-20261028.md'):
        recorded[str(p)]=meter.sha(p)
    ODOL=binary.old.read_backend(Path('C:/temp/moto_lanes/review_g3/tools'))
    _,original,_=load(c['source_control']);_,candidate,_=load(c['candidate_mlod'])
    control_od=ODOL.from_file(str(root/'prism-b3-binary-pair-20261028/control/saved-odol.p3d'),strict=True)
    candidate_od=ODOL.from_file(str(root/'prism-b3-binary-pair-20261028/candidate/saved-odol.p3d'),strict=True)
    historical_od=ODOL.from_file(str(c['baseline_odol']),strict=True)
    for od in (control_od,candidate_od,historical_od):require(not od.lod_errors and len(od.lods)==4 and all(l.lod_end_ok for l in od.lods),'odol_structure')
    binary.control_identity(historical_od,control_od)
    control,_=census(original[1],control_od,c['origin'],c['matrix'])
    proposed,_=census(candidate[1],candidate_od,c['origin'],c['matrix'],'component1335')
    require(control['summary']['components']==proposed['summary']['components']==1520,'census_denominator')
    census_report=dict(status='CENSUS_RECORDED',control=control,candidate=proposed,verified_input_pins=pins,recorded_instrument_hashes=recorded,historical_control_semantic_identity=True,measurement=meter.memory(),original_binary_verdict='REJECTED_BINARY')
    meter.dump(output/'census.json',census_report)
    meter.STARTED=time.monotonic()
    result=feasibility(original,candidate,candidate_od,np.asarray(c['origin']),c['matrix'],c['selected_components'],proposed) if control_gate(control) else dict(status='INCONCLUSIVE_CONTROL_FRAME',control_summary=control['summary'])
    result.update(census_sha256=meter.sha(output/'census.json'),verified_input_pins=pins,recorded_instrument_hashes=recorded,measurement=meter.memory(),no_model_written=True,no_build=True,no_dayz=True)
    for p,h in {**pins,**recorded}.items():require(meter.sha(p)==h,'input_changed_after:'+p)
    meter.dump(output/'report.json',result)
    print(json.dumps(dict(status=result['status'],control=control['summary'],candidate=proposed['summary'],changed_vertices=result.get('changed_vertices'),domain_values_seen=result.get('domain_values_seen'),maximum_y_move_m=result.get('maximum_y_move_m'))))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(exist_ok=False)
    meter.STARTED=START;meter.MAX_SECONDS=180;stop=meter.bounded(a.output)
    try:run(a.root,a.output)
    except Exception as e:meter.dump(a.output/'failure.json',dict(status='INCONCLUSIVE_DISCOVERY',type=type(e).__name__,reason=str(e),measurement=meter.memory()));raise
    finally:stop.set()
