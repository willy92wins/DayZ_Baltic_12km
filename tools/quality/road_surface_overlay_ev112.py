"""Diagnostic of reference road axes against sealed deployed surface prototypes.

All exposure is relative to SOURCE terrain. No motor, bridge or road acceptance.
Ambiguous/proxy surfaces are retained, never silently converted to empty space.
"""
import os, time
STARTED=time.monotonic()
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'): os.environ[key]='1'
import argparse, hashlib, importlib.util, io, json, math, struct
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
import shapely
from shapely import STRtree

HERE=Path(__file__).resolve().parent
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
surface=module('overlay_surface',HERE/'deployed_surface_inventory_ev112.py')
native=module('overlay_native',HERE/'road_water_contacts_ev112.py')
require=surface.require


def cross(a,b): return float(a[0]*b[1]-a[1]*b[0])


def hull(points):
    p=sorted(set(map(tuple,np.asarray(points,float))))
    if len(p)<3:return np.asarray(p)
    def half(items):
        out=[]
        for q in items:
            while len(out)>1 and cross(np.subtract(out[-1],out[-2]),np.subtract(q,out[-1]))<=0:out.pop()
            out.append(q)
        return out
    return np.asarray(half(p)[:-1]+half(p[::-1])[:-1])


def clip(a,b,p,cache=None):
    """Convex footprint clipping; canonical edges give shared crossings one bit pattern."""
    a,b,p=np.asarray(a,float),np.asarray(b,float),np.asarray(p,float)
    require(a.shape==b.shape==(2,) and p.ndim==2 and p.shape[1]==2 and len(p)>0 and
            np.isfinite(a).all() and np.isfinite(b).all() and np.isfinite(p).all(),'clip_input')
    d=b-a; require(float(d@d)>0,'zero_road_edge')
    if len(p)<=2:
        c=p[0];e=p[-1]-c;den=cross(d,e)
        if den:
            t=cross(c-a,e)/den;u=cross(c-a,d)/den
            return (t,t) if 0<=t<=1 and 0<=u<=1 else None
        if cross(c-a,d)!=0:return None
        ts=((p-a)@d)/(d@d);lo=max(0.,float(ts.min()));hi=min(1.,float(ts.max()))
        return (lo,hi) if lo<=hi else None
    center=p.mean(axis=0);lo,hi=0.,1.;cache={} if cache is None else cache
    for q,r in zip(p,np.roll(p,-1,axis=0)):
        key=tuple(sorted((tuple(q),tuple(r))))
        if key not in cache:
            u,v=map(np.asarray,key);e=v-u;c0=cross(e,a-u);s=cross(e,d)
            cache[key]=(c0,s,(-c0/s if s else None))
        c0,s,t=cache[key];u,v=map(np.asarray,key);side=cross(v-u,center-u)
        require(side!=0,'nonconvex_clip_polygon')
        sign=1 if side>0 else -1;c0*=sign;s*=sign
        if not s:
            if c0<0:return None
        elif s>0:lo=max(lo,t)
        else:hi=min(hi,t)
        if lo>hi:return None
    return float(lo),float(hi)


def height(v,points):
    v=np.asarray(v,float);n=np.cross(v[1]-v[0],v[2]-v[0]);require(n[1]!=0,'vertical_height')
    points=np.asarray(points,float)
    return v[0,1]-(n[0]*(points[:,0]-v[0,0])+n[2]*(points[:,1]-v[0,2]))/n[1]


def face_span(a,b,v,flags=0,cache=None):
    v=np.asarray(v,float);p=hull(v[:,[0,2]]);hit=clip(a,b,p,cache)
    if hit is None:return None
    lo,hi=hit;points=np.asarray(a)+(np.asarray(b)-a)*np.array([[lo],[hi]])
    uncertain=bool(flags & (surface.AMBIGUOUS_FACE|surface.DEGENERATE_FACE)) or len(p)<3
    row=dict(lo=lo,hi=hi,uncertain=uncertain or bool(flags & surface.PROXY_CONDITIONAL),
             flags=int(flags),height_bounds=[float(v[:,1].min()),float(v[:,1].max())])
    if uncertain:
        row.update(status='INCONCLUSIVE_VERTICAL_FACE' if len(p)<3 else 'INCONCLUSIVE_TRIANGULATION',y=None,fans=[])
        # Both possible diagonals; no diagonal is selected as authoritative.
        if len(v)==4:
            for fan,tris in enumerate((((0,1,2),(0,2,3)),((0,1,3),(1,2,3)))):
                for ti,ids in enumerate(tris):
                    tri=v[list(ids)];hp=hull(tri[:,[0,2]])
                    if len(hp)<3:continue
                    th=clip(a,b,hp,cache)
                    if th is not None:
                        ps=np.asarray(a)+(np.asarray(b)-a)*np.array(th)[:,None]
                        row['fans'].append(dict(fan=fan,triangle=ti,lo=th[0],hi=th[1],y=height(tri,ps).tolist()))
    else:row.update(status='CONDITIONAL_PROXY_FRAME' if flags&surface.PROXY_CONDITIONAL else 'PLANAR_FACE',y=height(v,points).tolist())
    return row


def at(row,t,key='y'):
    y=row[key];return y[0] if row['hi']==row['lo'] else y[0]+(y[1]-y[0])*(t-row['lo'])/(row['hi']-row['lo'])


def split_sign(row,key):
    lo,hi=row['lo'],row['hi'];d0,d1=row[key];cuts=[lo,hi]
    if d0*d1<0:cuts.insert(1,lo+(hi-lo)*d0/(d0-d1))
    out=[]
    for x,z in zip(cuts,cuts[1:]):
        mid=at(row,(x+z)/2,key);r=dict(row,lo=x,hi=z,sign=0 if mid==0 else (1 if mid>0 else -1))
        for k in ('y','terrain_y','difference'):
            if row.get(k) is not None:r[k]=[at(row,x,k),at(row,z,k)]
        out.append(r)
    return out


def terrain_parts(a,b,h):
    top=(len(h)-1)*6.;ts=native.cuts(a,b,top);out=[]
    for lo,hi in zip(ts,ts[1:]):
        ps=np.asarray(a)+(np.asarray(b)-a)*np.array([lo,hi])[:,None]
        fs=native.faces_at(ps.mean(axis=0),len(h),top)
        for r,c,ti in fs:
            hv=np.array([h[r+native.OFF[k][0],c+native.OFF[k][1]] for k in native.TRI[ti]],float)
            ws=np.array([native.bary(p,r,c,ti,top) for p in ps]);require(ws.min()>=-1e-9,'terrain_domain')
            out.append(dict(lo=lo,hi=hi,y=(ws@hv).tolist(),face=[r,c,ti]))
    return out


def exposure(row,terrain):
    if row['y'] is None:return [dict(row,exposure='INCONCLUSIVE_GEOMETRY')]
    result=[]
    for part in terrain:
        lo=max(row['lo'],part['lo']);hi=min(row['hi'],part['hi'])
        if lo>hi:continue
        ys=[at(row,t) for t in (lo,hi)];hs=[at(part,t) for t in (lo,hi)]
        r=dict(row,lo=lo,hi=hi,y=ys,terrain_y=hs,difference=list(np.subtract(ys,hs)),terrain_face=part['face'])
        for p in split_sign(r,'difference'):
            p['exposure']={1:'EXPOSED',-1:'BURIED',0:'CONTACT'}[p.pop('sign')]+'_RELATIVE_TO_SOURCE_TERRAIN';result.append(p)
    require(result,'surface_outside_terrain_partition');return result


def roadway_role(group,texture):
    if surface.norm(texture).split('/')[-1]=='water_ext.paa':return 'water_roadway'
    return 'bridge' if group=='bridge' else group+'_roadway'


def alignment(vertices,a,b):
    p=np.asarray(vertices,float)[:,[0,2]];center=p.mean(axis=0);_,vectors=np.linalg.eigh((p-center).T@(p-center));axis=vectors[:,-1]
    d=np.asarray(b)-a;direction=d/np.linalg.norm(d)
    return dict(method='Roadway vertex PCA diagnostic, not designed road heading',
                axis_xz=axis.tolist(),center_xz=center.tolist(),
                heading_difference_degrees=float(np.degrees(np.arccos(np.clip(abs(axis@direction),0,1)))),
                midpoint_offset_m=abs(cross(axis,(np.asarray(a)+b)/2-center)))


def union(intervals):
    out=[]
    for lo,hi in sorted(intervals):
        if out and lo<=out[-1][1]:out[-1][1]=max(hi,out[-1][1])
        else:out.append([lo,hi])
    return out


def gap_provenance(spans,lo,hi):
    left=[s['ref'] for s in spans if s['hi']==lo];right=[s['ref'] for s in spans if s['lo']==hi]
    same=sorted(set(x[0] for x in left)&set(x[0] for x in right))
    return dict(left_surfaces=left,right_surfaces=right,shared_instances=same,
                status='INCONCLUSIVE_INTRAMESH_GAP' if same else 'GEOMETRIC_SEPARATION_NOT_DRIVING_VERDICT')


def overlay(water,bridges):
    """Presence, uncertainty and clearance are separate. No driving acceptance."""
    lo,hi=water['lo'],water['hi'];ts={lo,hi}
    for b in bridges:
        x=max(lo,b['lo']);z=min(hi,b['hi'])
        if x>z:continue
        ts.update((x,z))
        if b['y'] is not None and water['y'] is not None:
            d0=at(b,x)-at(water,x);d1=at(b,z)-at(water,z)
            if d0*d1<0:ts.add(x+(z-x)*d0/(d0-d1))
    ts=sorted(ts);pairs=list(zip(ts,ts[1:])) if lo<hi else [(lo,hi)];out=[]
    for x,z in pairs:
        t=(x+z)/2;cover=[b for b in bridges if b['lo']<=t<=b['hi']]
        clear=[]
        for b in cover:
            clear.append(dict(surface=b['ref'],uncertain=b['uncertain'],difference=None if b['y'] is None or water['y'] is None else [at(b,q)-at(water,q) for q in (x,z)]))
        if water['uncertain']:state='INCONCLUSIVE_WATER'
        elif any(not b['uncertain'] and at(b,t)>at(water,t) for b in cover if b['y'] is not None):state='ROADWAY_ABOVE_WATER'
        elif any(b['uncertain'] for b in cover):state='INCONCLUSIVE_BRIDGE_GEOMETRY'
        elif cover:state='ROADWAY_AT_OR_BELOW_WATER'
        else:state='NOMINAL_WET_AXIS_WITHOUT_BRIDGE_ROADWAY' if water.get('nominal') else 'WET_AXIS_WITHOUT_BRIDGE_ROADWAY'
        provenance=None
        if not cover:
            left=[b['hi'] for b in bridges if b['hi']<=t];right=[b['lo'] for b in bridges if b['lo']>=t]
            if left and right:
                provenance=gap_provenance(bridges,max(left),min(right))
                if provenance['shared_instances'] and not water['uncertain']:state='INCONCLUSIVE_INTRAMESH_GAP'
        out.append(dict(lo=x,hi=z,status=state,water=water['ref'],clearance=clear,gap_provenance=provenance))
    return out


def sealed(path,expected,pins):
    raw=path.read_bytes();require(hashlib.sha256(raw).hexdigest()==expected,'input_hash:'+str(path));pins[path]=expected;return raw


def prepare(root,worktree,road_root):
    pins={};manifest_path=worktree/'evidence/deployed-surface-prototypes-20261028/artifact-hashes.json'
    raw=manifest_path.read_bytes();pins[manifest_path]=hashlib.sha256(raw).hexdigest();manifest=surface.manifest_keys(json.loads(raw))
    base=root/'deployed-surface-prototypes-20261028'
    def artifact(name):
        p=base/name;key=surface.norm(p.relative_to(root).as_posix());require(key in manifest,'missing_artifact');return sealed(p,manifest[key]['sha256'],pins)
    with np.load(io.BytesIO(artifact('surface-prototypes.npz'))) as z:v,m=z['vertices'],z['meta']
    with np.load(io.BytesIO(artifact('instances.npz'))) as z:ids,mi,poses=z['ids'],z['model_index'],z['matrix']
    catalog=json.loads(artifact('model-catalog.json'));sections=json.loads(artifact('model-sections.json'));proxy_paths=json.loads(artifact('proxy-paths.json'))
    source_inputs=json.loads(artifact('inputs.json'))
    require(hashlib.sha256(Path(surface.__file__).read_bytes()).hexdigest()==source_inputs['script_sha256'],'surface_transform_source_changed')
    require(hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest()=='6853a78f11a065949f0e4ea522fb03c29c7b0e20a576ac9cfc2221e80c69bf74','native_source_changed')
    surface.instance_guard(ids,mi,poses,catalog)
    require(len(v)==len(m)==539009 and len(ids)==17818,'surface_coverage')
    expected={root/'river-kit7-merged-byteexact-20261026/terrain-buried.npz':'815ef8b772bfa10e9d6886d953878c24ef6819c5667ce4700c91faab992aec40',
      road_root/'tests/regional_foundation_roads_v6/reference.npz':'94ecbca61bd5ba9ba61f89b765b043676a4a65703729a0b69009ae233984a1c2',
      road_root/'evidence/regional-foundation-v1/road-grade-chains-v6.json':'b31fb7d72398981ee98132ce59eab48c4aa404043718475fbb2725b13de1b824',
      worktree/'evidence/road-water-census-20261028/contacts.json':'3827291ed36e15a4320f18fd2d921badaacf6d575a8f1954e319d7fcc6b09c3d',
      worktree/'evidence/road-water-census-20261028/chain-coverage.json':'e53011aae3277eb2ad0c9dbd60cf2ec6829198f0cc09d638d7ff4ccdbe8dffa8',
      root/'river-kit7-merged-byteexact-20261026/bury-work/fp0/footprint.npz':'084171b0e29df5c220f9d5aab42a3dc683a2f70a07579f08cd930dfd109e716b'}
    raw={p.name:sealed(p,d,pins) for p,d in expected.items()}
    with np.load(io.BytesIO(raw['terrain-buried.npz'])) as z:h=z['heights']
    with np.load(io.BytesIO(raw['footprint.npz'])) as z:plane=z['plane']
    with np.load(io.BytesIO(raw['reference.npz'])) as z:xy,edges=z['xy'],z['edges']
    chains=json.loads(raw['road-grade-chains-v6.json'])['chains'];coverage=native.graph_guard(xy,edges,chains)
    require((coverage['chains'],coverage['nodes'],coverage['edges'])==(124,36428,36467),'road_universe')
    contacts={(x['chain'],x['edge']):x for x in json.loads(raw['contacts.json'])}
    require(len(contacts)==770,'native_contacts')
    road_rows=[]
    for ci,chain in enumerate(chains):
        station=0.
        for ei,(a,b) in enumerate(zip(chain,chain[1:])):
            length=float(np.linalg.norm(xy[b]-xy[a]));road_rows.append((ci,ei,a,b,station,length));station+=length
    source_wrp=root/'stage-kit7-fc-20261026/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
    require(str(source_wrp) in source_inputs['source_pins'],'source_wrp_pin')
    pins[source_wrp]=source_inputs['source_pins'][str(source_wrp)]
    with source_wrp.open('rb') as f:
        magic,tx,tz,nx,nz,cell=struct.unpack('<4s4If',f.read(24));require(magic==b'0WZD' and (nz,nx)==h.shape,'source_wrp_header')
        require(f.read(nx*nz*4)==np.ascontiguousarray(h[::-1],dtype='<f4').tobytes(),'source_terrain_not_wrp_exact')
    for p in (Path(__file__),Path(surface.__file__),Path(native.__file__),HERE/'water_constraint_diagnostic_ev112.py'):
        pins[p]=hashlib.sha256(p.read_bytes()).hexdigest()
    return dict(pins=pins,v=v,m=m,ids=ids,mi=mi,poses=poses,catalog={x['index']:x for x in catalog},sections={x['index']:x for x in sections},proxy_paths=proxy_paths,
                h=h,plane=plane,xy=xy,road_rows=road_rows,coverage=coverage,contacts=contacts)


def broad_phase(data):
    v,m=data['v'],data['m'];order=np.argsort(m['model'],kind='stable');keys,starts=np.unique(m['model'][order],return_index=True)
    bymodel={int(k):order[x:y] for k,x,y in zip(keys,starts,list(starts[1:])+[len(order)])}
    boxes=[];indices=[];empty=[]
    for i,(model,pose) in enumerate(zip(data['mi'],data['poses'])):
        face_ids=bymodel.get(int(model),[])
        if not len(face_ids):empty.append(i);continue
        ps=surface.transform(v[face_ids],pose);mask=np.arange(4)[None,:]<m['vertices'][face_ids,None];flat=ps[mask][:,[0,2]]
        low,high=flat.min(axis=0),flat.max(axis=0);boxes.append([*low,*high]);indices.append(i)
    bb=np.asarray(boxes);tree=STRtree(shapely.box(bb[:,0],bb[:,1],bb[:,2],bb[:,3]))
    xy=data['xy'];segments=np.asarray([[xy[x[2]],xy[x[3]]] for x in data['road_rows']]);pairs=tree.query(shapely.linestrings(segments))
    candidates=defaultdict(list)
    for edge,local in pairs.T:candidates[int(edge)].append(indices[int(local)])
    counts=[sum(len(bymodel[int(data['mi'][i])]) for i in candidates.get(e,[])) for e in range(len(segments))]
    info=dict(instance_boxes=len(indices),instances_without_surface=len(empty),bbox_pairs=pairs.shape[1],candidate_faces=sum(counts),max_candidate_faces_per_edge=max(counts),candidate_edges=len(candidates))
    return bymodel,candidates,info


def native_water(contact,plane=None):
    result=[]
    if contact is None:return result
    for pi,p in enumerate(contact['parts']):
        for fi,f in enumerate(p['faces']):
            spans=f['wet']+([[p['lo'],p['hi']]] if f['contact_interval'] else [])
            spans += [[t,t] for t in f['roots']]
            spans += [[t,t] for t,d in zip((p['lo'],p['hi']),f['difference']) if d==0 and not f['contact_interval']]
            for j,(lo,hi) in enumerate(spans):
                row=dict(lo=p['lo'],hi=p['hi'],y=f['water']);y=[at(row,t) for t in (lo,hi)]
                result.append(dict(ref=['native',pi,fi,j],lo=lo,hi=hi,y=y,nominal=True,
                    uncertain=p['ambiguous_water_boundary'] or p['numerical_incidence_ambiguity'],exposure='NOMINAL_WET' if (lo,hi) in map(tuple,f['wet']) else 'NOMINAL_CONTACT',cell=f['cell'],triangle=f['triangle'],
                    nominal_layer='UNSPECIFIED' if plane is None else ('POND' if np.isfinite(plane[tuple(f['cell'])]) else 'SEA')))
    return result


def layer_differences(natives,models):
    out=[]
    for n in natives:
        for m in models:
            lo=max(n['lo'],m['lo']);hi=min(n['hi'],m['hi'])
            if lo>hi:continue
            out.append(dict(lo=lo,hi=hi,native=n['ref'],model=m['ref'],uncertain=n['uncertain'] or m['uncertain'],
                            model_minus_native=None if m['y'] is None else [at(m,t)-at(n,t) for t in (lo,hi)],model_height_bounds=m['height_bounds']))
    return out


def census(data,bymodel,candidates,output,meter):
    v,m=data['v'],data['m'];cache_instances={};rows=[];nodeobs=defaultdict(list);chainspans=defaultdict(list);coverage=[]
    for edge,(ci,ei,na,nb,station,length) in enumerate(data['road_rows']):
        a,b=data['xy'][[na,nb]];hits=[];cache={};tp=None
        for ii in candidates.get(edge,[]):
            model=int(data['mi'][ii]);face_ids=bymodel[model];group=data['catalog'][model]['group']
            if ii not in cache_instances:cache_instances[ii]=surface.transform(v[face_ids],data['poses'][ii])
            faces=cache_instances[ii]
            for j,mid in enumerate(face_ids):
                meta=m[mid];face=faces[j,:meta['vertices']];xz=face[:,[0,2]]
                if np.any(xz.max(axis=0)<np.minimum(a,b)) or np.any(xz.min(axis=0)>np.maximum(a,b)):continue
                hit=face_span(a,b,face,int(meta['flags']),cache)
                if hit is None:continue
                sections=data['sections'][int(meta['source_model'])]['lods'][int(meta['lod'])]['sections']
                tex=sections[int(meta['section'])]['texture'];kind=int(meta['kind'])
                role='model_water' if kind in (1,2) else roadway_role(group,tex)
                hit.update(ref=[int(data['ids'][ii]),int(mid)],instance_index=ii,model=model,prototype=int(mid),group=group,role=role,proxy_path=int(meta['proxy']))
                if role=='model_water':
                    if tp is None:tp=terrain_parts(a,b,data['h'])
                    hits.extend(exposure(hit,tp))
                elif role=='bridge':
                    if tp is None:tp=terrain_parts(a,b,data['h'])
                    bridge_mask=(m['kind'][face_ids,None]==0)&(np.arange(4)[None,:]<m['vertices'][face_ids,None])
                    hit['alignment']=alignment(faces[bridge_mask],a,b)
                    hit['terrain_clearance']=exposure(hit,tp)
                    hits.append(hit)
                else:hits.append(hit)
        natives=native_water(data['contacts'].get((ci,ei)),data['plane'])
        waters=natives+[x for x in hits if x['role']=='model_water' and (x['uncertain'] or not x['exposure'].startswith('BURIED'))]
        bridges=[x for x in hits if x['role']=='bridge'];findings=[]
        for w in waters:
            if 'CONTACT' in w['exposure'] and not w['uncertain']:continue
            findings.extend(overlay(w,bridges))
        for x in bridges:
            chainspans[ci].append(dict(lo=station+x['lo']*length,hi=station+x['hi']*length,ref=x['ref'],uncertain=x['uncertain']))
        for node,t in ((na,0.),(nb,1.)):
            seen=set()
            for x in hits+natives:
                if x['lo']<=t<=x['hi']:
                    obs=dict(chain=ci,edge=ei,ref=x['ref'],role=x.get('role','native_water'),y=at(x,t) if x['y'] is not None else None,uncertain=x['uncertain'])
                    key=json.dumps(obs,sort_keys=True)
                    if key not in seen:nodeobs[node].append(obs);seen.add(key)
        coverage.append((ci,ei,na,nb,length,len(candidates.get(edge,[])),len(hits)))
        if hits or waters:
            rows.append(dict(chain=ci,edge=ei,nodes=[na,nb],a=a.tolist(),b=b.tolist(),station_m=station,length_m=length,surfaces=hits,native_water=natives,findings=findings,
                             water_layer_differences=layer_differences(natives,[s for s in hits if s['role']=='model_water'])))
    gaps=[]
    for ci,spans in chainspans.items():
        for left,right in zip(union([(s['lo'],s['hi']) for s in spans]),union([(s['lo'],s['hi']) for s in spans])[1:]):
            gaps.append(dict(chain=ci,lo=left[1],hi=right[0],gap_m=right[0]-left[1],station_ulp_m=float(max(np.spacing(left[1]),np.spacing(right[0]))),**gap_provenance(spans,left[1],right[0])))
    node_rows=[]
    for node,obs in nodeobs.items():
        # Full observations include every incident chain; no pair or height is selected as truth.
        values=[x['y'] for x in obs if x['y'] is not None]
        node_rows.append(dict(node=node,xz=data['xy'][node].tolist(),observations=obs,height_spread_m=max(values)-min(values) if values else None))
    meter.dump(output/'contacts.json',rows);meter.dump(output/'nodes.json',node_rows);meter.dump(output/'bridge-gaps.json',gaps)
    np.savez_compressed(output/'edge-coverage.npz',rows=np.asarray(coverage))
    require(len(coverage)==data['coverage']['edges'],'edge_coverage')
    states=Counter(f['status'] for r in rows for f in r['findings']);exposures=Counter(s['exposure'] for r in rows for s in r['surfaces'] if s['role']=='model_water')
    report=dict(status='SURFACE_OVERLAY_DIAGNOSTIC_ONLY',coverage=data['coverage'],contact_edges=len(rows),model_exposure_pieces=dict(exposures),finding_pieces=dict(states),node_observations=len(node_rows),source_terrain_matches_editable_wrp=True,
                limitations=['No full compiled terrain decode; exposure relative to exact editable source terrain.','Proxy frame and ambiguous/vertical geometry remain conditional.','Reference road axes only, no pavement width, driving, navigation, visual or map acceptance.','Finding pieces are not distinct crossings or missing bridges.'])
    contexts=[]
    for label,point in [('Narva',[2391,6941]),('kit118',[8253,9038]),('reported_crossing',[4789.51465,5516.52197])]:
        ranked=sorted(((native.point_segment_distance(np.asarray(point),np.array([r['a'],r['b']])),r) for r in rows),key=lambda p:p[0])[:6]
        contexts.append(dict(label=label,point=point,nearest=[dict(distance_m=d,chain=r['chain'],edge=r['edge'],states=dict(Counter(f['status'] for f in r['findings']))) for d,r in ranked],association='CONTEXT_NOT_CAMERA_IDENTITY'))
    meter.dump(output/'contexts.json',contexts);return report


def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('worktree',type=Path);p.add_argument('road_root',type=Path);p.add_argument('output',type=Path);p.add_argument('--preflight',action='store_true');args=p.parse_args()
    args.output.mkdir(exist_ok=False);meter=module('overlay_meter',HERE/'water_constraint_diagnostic_ev112.py');meter.STARTED=STARTED;stop=meter.bounded(args.output)
    try:
        data=prepare(args.root,args.worktree,args.road_root);bymodel,candidates,cost=broad_phase(data)
        meter.dump(args.output/'cost.json',cost);meter.dump(args.output/'inputs.json',{str(p):v for p,v in data['pins'].items()})
        report=dict(status='COST_PREFLIGHT_ONLY',cost=cost) if args.preflight else census(data,bymodel,candidates,args.output,meter)
        for path,digest in data['pins'].items():require(meter.sha(path)==digest,'input_changed:'+str(path))
        report['resources']=meter.memory()
        require(report['resources']['seconds']<=meter.MAX_SECONDS and max(report['resources']['peak_resident_bytes'],report['resources']['peak_commit_bytes'])<=meter.MAX_BYTES,'resource_budget')
        require(not (args.output/'resource-stop.json').exists(),'resource_stop')
        meter.dump(args.output/'report.json',report);print(json.dumps(report))
    except Exception as e:meter.dump(args.output/'failure.json',dict(reason=str(e),resources=meter.memory()));raise
    finally:stop.set()


if __name__=='__main__':main()
