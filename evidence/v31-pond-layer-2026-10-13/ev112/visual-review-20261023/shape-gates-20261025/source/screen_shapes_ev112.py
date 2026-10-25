"""Run calibrated shape screens on a hash-pinned S3 source WRP and terrain.

Exit 2 = review/coverage blocks acceptance; 0 only clears these pattern screens.
No output from this tool accepts visuals, water connectivity, runtime or navmesh.
"""
import argparse,collections,hashlib,json,struct,sys
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from shapely.geometry import LineString,Point
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent/'water'),str(HERE.parent/'terrain')]
from shape_patterns_ev112 import POLICY,route_screen,join_screen,pyramid_fit,rectangle_components
import streambed_kit_v31 as K
import despike_v31 as D
from stream_reference_v31 import recover,require_original_endpoints,PINS
from audit_stream_visibility_ev112 import wet_span


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require_site_coverage(declared,reference):
    actual=[s['site'] for s in declared];expected=[s['id'] for s in reference]
    if not actual or len(set(actual))!=len(actual) or len(set(expected))!=len(expected) or set(actual)!=set(expected):
        raise ValueError('declared site coverage differs from pinned original reference')


def require_placed_coverage(placed,used):
    ids=[oid for instances in placed.values() for oid,_ in instances]
    if len(ids)!=len(set(ids)) or set(ids)!=used:raise ValueError('placed water/stone coverage differs from bound records')


def pilot_route_screens(axis,endpoints):
    required,bounds=wet_span(axis,endpoints)
    screens=[dict(route_screen(axis),scope='full_axis_including_dry_apron'),dict(route_screen(axis[required]),scope='original_wet_span')]
    return dict(routes=screens,findings=[dict(f,scope=s['scope']) for s in screens for f in s['findings']],
                wet_bounds_m=bounds,dry_apron_length_m=float(LineString(axis).length-(bounds[1]-bounds[0])))


def placed_water(path,H):
    """Stream 0WZD, bind its native grid, retain only water model matrices."""
    found=collections.defaultdict(list);count=0
    with Path(path).open('rb') as f:
        magic,tx,tz,nx,nz,cell=struct.unpack('<4s4If',f.read(24))
        if magic!=b'0WZD' or (nx,nz)!=(2048,2048):raise ValueError('wrong WRP')
        native=np.frombuffer(f.read(nx*nz*4),'<f4').reshape(nz,nx)
        if not np.array_equal(native,H[::-1]):raise ValueError('WRP/terrain mismatch')
        f.seek(tx*tz*2,1);materials=struct.unpack('<I',f.read(4))[0]
        for _ in range(materials):
            while True:
                length=struct.unpack('<I',f.read(4))[0]
                if not length:break
                f.seek(length,1)
        while True:
            row=f.read(56)
            if len(row)!=56:raise ValueError('truncated object records')
            oid,length=struct.unpack_from('<II',row,48)
            if not length:break
            raw=f.read(length)
            if len(raw)!=length:raise ValueError('truncated model name')
            name=raw.rstrip(b'\0').decode('ascii').lower();count+=1
            if name.startswith(('dz\\water\\streambed\\','baltic_stream_pilot\\')):
                found[name].append((oid,np.array(struct.unpack_from('<12f',row))))
        if f.read(1):raise ValueError('trailing WRP bytes')
    return found,count


def bind_matrix(record,placed,used):
    name=record['model'].lower();m=np.asarray(record['matrix'],float)
    if m.shape!=(12,) or not np.isfinite(m).all():raise ValueError('finite 12-element pose required')
    candidates=placed.get(name,[])
    if not candidates:raise ValueError('unplaced model '+name)
    if any(np.shape(v)!=(12,) or not np.isfinite(v).all() for _,v in candidates):raise ValueError('invalid WRP pose')
    errors=np.array([np.max(abs(v-m)) if oid not in used else np.inf for oid,v in candidates])
    i=int(np.argmin(errors))
    if errors[i]>POLICY['pose_tolerance_m']:raise ValueError('record does not match an unused WRP pose '+name)
    used.add(candidates[i][0]);return float(errors[i])


def pilot_axis(sid,pilot,author,inputs):
    sys.path.insert(0,'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/py3d');import py3d
    inputs[str(Path(py3d.__file__))]=sha(py3d.__file__)
    p=pilot/(sid+'-surfaces.npz');inputs[str(p)]=sha(p);z=np.load(p);water=[]
    for inst in author['instances']:
        if inst['site']!=sid:continue
        p=pilot/'source'/inst['model'].replace('\\','/');digest=sha(p)
        if digest!=inst['sha256']:raise ValueError('pilot source changed')
        inputs[str(p)]=digest
        with p.open('rb') as f:
            magic,version,nlod=struct.unpack('<4sII',f.read(12))
            if magic!=b'MLOD' or nlod!=4:raise ValueError('wrong pilot schema')
            lod=py3d.LOD(f)
        v=np.array([v.coords for v in lod.points])+inst['origin']
        for face in lod.faces:
            if 'water_streambed.rvmat' in face.material:water.extend(v[[p.point_index for p in face.vertices]])
    error=float(cKDTree(np.asarray(water)).query(z['water'].reshape(-1,3))[0].max())
    if error>POLICY['source_geometry_tolerance_m']:raise ValueError('pilot NPZ not represented by source water')
    axis=z['water'][:,[0,-1]].mean(axis=1)[:,[0,2]]
    return axis,error


def shape_axis_world(record,models):
    """Rung axis, with diagonal *end cap* bias explicitly separated for slanted pieces.

    Their flat interior has a straight axis. Extend that measured line to the
    original cap stations for macro-shape screening; keep raw rungs as diagnostics.
    This proxy is not a water silhouette or proof of a water connection.
    """
    g=models[K.model_key(record['model'])];R,T=K.rec_frame(record)
    C=np.array(g['centre'],float);raw=(C@R.T+T)[:,[0,2]];diagnostic=None
    if 'slanted' in K.kind_of(record['model']):
        flat=abs(C[:,1]-g['roadway_flat_y'])<=POLICY['slanted_axis_flat_tolerance_m']
        body=C[flat]
        if len(body)<2 or np.ptp(body[:,2])<1e-8:raise ValueError('slanted body axis unavailable')
        coef=np.polyfit(body[:,2],body[:,0],1)
        if np.max(abs(np.polyval(coef,body[:,2])-body[:,0]))>POLICY['slanted_axis_linear_tolerance_m']:
            raise ValueError('slanted body no longer straight')
        C[:,0]=np.polyval(coef,C[:,2]);axis=(C@R.T+T)[:,[0,2]]
        diagnostic=dict(kind='slanted_cap_rung_bias',max_axis_offset_m=float(np.linalg.norm(axis-raw,axis=1).max()),
                        raw_route=route_screen(raw),raw_axis=raw.tolist())
    else:axis=raw
    return axis,diagnostic


def stitch_for_screen(lines,joins):
    """Chain within a versioned measured gap; disclose every synthetic connector.

    Used only to screen route patterns, never as water connectivity evidence.
    """
    chains=[];current=[];starts=[0.]+[j['after_station_m'] for j in joins]
    ends=[j['before_station_m'] for j in joins]+[LineString(lines[-1]).length]
    incomplete=[];bridges=[]
    for i,(points,start,end) in enumerate(zip(lines,starts,ends)):
        line=LineString(points)
        if end<=start+1e-6:
            incomplete.append(dict(piece=i,reason='reversed_or_empty_trim'))
            if len(current)>1:chains.append(np.asarray(current))
            current=[];continue
        distance=np.r_[0,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
        part=np.vstack([line.interpolate(start).coords[0],points[(distance>start+1e-8)&(distance<end-1e-8)],line.interpolate(end).coords[0]])
        gap=float(np.linalg.norm(np.asarray(current[-1])-part[0])) if current else 0.
        if current and gap>POLICY['chain_bridge_max_m']:
            incomplete.append(dict(piece=i,reason='centreline_gap_not_bridged',gap_m=gap))
            if len(current)>1:chains.append(np.asarray(current))
            current=[]
        elif current and gap>1e-8:
            bridges.append(dict(before_piece=i-1,after_piece=i,bridged_gap_m=gap,scope='pattern_proxy_only'))
            current.append(part[0])
        current.extend(part if not current else part[1:])
    if len(current)>1:chains.append(np.asarray(current))
    return chains,incomplete,bridges


def river_screen(build,pilot,placed,inputs):
    records_path=build/'water-fix-b/kit/kit-records.json';report_path=build/'water-fix-b/kit/kit-report.json'
    author_path=pilot/'author-report.json'
    for p in (records_path,report_path,author_path,K.GEOM_PATH,Path(K.__file__)):inputs[str(p)]=sha(p)
    records=json.loads(records_path.read_text());declared=json.loads(report_path.read_text())['sites'];author=json.loads(author_path.read_text())
    baseline=build.parent/'ev112-ot1-20261018/sites-d.json'
    if sha(baseline)!=PINS['ev112-ot1-20261018/sites-d.json']:raise ValueError('changed site reference')
    inputs[str(baseline)]=sha(baseline);require_site_coverage(declared,json.loads(baseline.read_text()))
    if set(r['site'] for r in records)-{s['site'] for s in declared}:raise ValueError('records outside declared site coverage')
    models=json.loads(K.GEOM_PATH.read_text())['models'];replaced={s['site'] for s in author['sites']};original=recover(build,list(replaced));used=set();pose_errors=[]
    if set(author['removed_sites'])!=replaced:raise ValueError('pilot removal coverage differs from replacement coverage')
    # Compiled ODOL centres offset author origins. Consume the binary-derived
    # poses used by stage_visual_pilot_ev112.py:28-31, not guessed translations.
    records_file=pilot/'records.json';binary_file=pilot/'binary-review.json';packed=pilot/'packed/baltic_stream_pilot.pbo'
    for p in (records_file,binary_file,packed):inputs[str(p)]=sha(p)
    binary=json.loads(binary_file.read_text());pilot_records=json.loads(records_file.read_text())
    if binary['status']!='BINARY_PASS' or binary['pbo_sha256']!=sha(packed):raise ValueError('unverified pilot PBO')
    if collections.Counter(r['model'] for r in pilot_records)!=collections.Counter(i['model'] for i in author['instances']):raise ValueError('pilot record/model coverage mismatch')
    for record in pilot_records:pose_errors.append(bind_matrix(record,placed,used))
    rows=[];paths={}
    for site in declared:
        sid=site['site'];selected=sorted([r for r in records if r['site']==sid and r['piece']!='stones'],key=lambda r:r['station'][0])
        if sid in replaced:
            s=next(s for s in author['sites'] if s['site']==sid);require_original_endpoints(s['original_raw_endpoints'],original[sid])
            axis,error=pilot_axis(sid,pilot,author,inputs);paths[sid]=[axis]
            rows.append(dict(site=sid,source='placed_continuous_pilot',geometry_error_m=error,joins=[],coverage_open=[],
                             **pilot_route_screens(axis,s['original_raw_endpoints'])))
            continue
        if not selected:
            rows.append(dict(site=sid,source='unbuilt',routes=[],joins=[],findings=[],coverage_open=[dict(reason='declared_site_without_built_pieces')]))
            continue
        lattice=LineString(np.asarray(site['lattice'],float));lines=[];representation=[]
        for r in selected:
            pose_errors.append(bind_matrix(r,placed,used))
            p,diagnostic=shape_axis_world(r,models)
            if diagnostic:representation.append(dict(diagnostic,index=len(lines)))
            if lattice.project(Point(p[-1]))<lattice.project(Point(p[0])):p=p[::-1]
            lines.append(p)
        joins=[dict(join_screen(a,b),before_piece=selected[i]['piece'],after_piece=selected[i+1]['piece']) for i,(a,b) in enumerate(zip(lines,lines[1:]))]
        chains,opened,bridges=stitch_for_screen(lines,joins);paths[sid]=lines
        # Also screen every actual piece: an ambiguous connection never removes
        # the piece's corners or straight length from the inventory.
        screens=[dict(route_screen(p),scope='piece',index=i) for i,p in enumerate(lines)]
        screens += [dict(route_screen(p),scope='measured_gap_chain_proxy',index=i) for i,p in enumerate(chains)]
        findings=[]
        for s in screens:
            findings.extend([dict(f,scope=s['scope'],index=s['index']) for f in s['findings']])
        for j in joins:
            findings.extend([dict(kind=k,xy=j['xy'],turn_deg=j['turn_deg'],gap_m=j['gap_m'],before_piece=j['before_piece'],after_piece=j['after_piece']) for k in j['findings']])
        rows.append(dict(site=sid,source='wrp_bound_vanilla_pieces',pieces=len(lines),routes=screens,joins=joins,coverage_open=opened,findings=findings,
                         representation_diagnostics=representation,chain_bridges=bridges))
        print('river',sid,'pieces',len(lines),'findings',len(findings),'open',len(opened),flush=True)
    water_bound=len(used)
    for r in records:
        if r['piece']=='stones' and r['site'] not in replaced:pose_errors.append(bind_matrix(r,placed,used))
    unconsumed=[dict(id=oid,model=name) for name,instances in placed.items() for oid,_ in instances if oid not in used]
    if unconsumed:raise ValueError('placed water models omitted from shape coverage: '+str(unconsumed[:5]))
    require_placed_coverage(placed,used)
    return dict(sites=rows,declared_sites=len(rows),bound_poses=len(used),placed_total=sum(map(len,placed.values())),
                water_bound_poses=water_bound,stone_poses_excluded_from_route_screen=len(used)-water_bound,max_pose_error_m=max(pose_errors),
                finding_counts=dict(collections.Counter(f['kind'] for r in rows for f in r['findings'])),
                open_sites=[r['site'] for r in rows if r['coverage_open']],
                scope='WRP-bound shape axes. Slanted cap rung bias retained separately. Measured sub-threshold connectors are proxies, not water. Counts overlap across scopes; not unique defects. External receptors/branches and water silhouettes remain outside this gate.'),paths


def terrain_screen(terrain,footprint):
    z=np.load(terrain);H=z['heights'].astype(float);fp=np.load(footprint)
    masks={k:z[k].astype(bool) for k in ('reserve','platform','narva','v31_dam','v31_kit','v31_bridge_cut','v31_bridge_fill','v31_shore_ramp','v31_causeway','v31_continuous_pilot') if k in z.files}
    rr,cc=np.mgrid[:2048,:2048];masks['protected_01545_60m']=np.hypot(cc*6-10397.4,12282-rr*6-9421.9)<=60
    masks['pond_corners']=D.env_vertex_plane(fp['plane'])[0];masks['sea_bed']=H<.75
    def tags(r,c):return [k for k,m in masks.items() if m[r,c]] or ['outside_listed_domains']
    findings=[];pk,pt=D.prominence(H)
    for kind,metric in [('native_spike',pk),('native_pit',pt)]:
        labels,n=ndi.label(metric>POLICY['native_prominence_m'],structure=np.ones((3,3)))
        for ident,sl in enumerate(ndi.find_objects(labels),1):
            local=np.where(labels[sl]==ident,metric[sl],-np.inf);r,c=np.unravel_index(np.argmax(local),local.shape);r+=sl[0].start;c+=sl[1].start
            findings.append(dict(kind=kind,row=int(r),col=int(c),xy=[int(c*6),int(12282-r*6)],prominence_m=float(metric[r,c]),domains=tags(r,c),vertices=int((labels[sl]==ident).sum())))
    # Broad apex candidate selection is independent of the native .30m spike.
    # A background slope can hide the raw apex. A centred mean cancels a plane
    # exactly in the interior; screen maxima of the residual as well as H.
    residual=H-ndi.uniform_filter(H,size=3)
    extrema=((H>=ndi.maximum_filter(H,size=3))&(H>ndi.minimum_filter(H,size=3)+1e-5))|((residual>=ndi.maximum_filter(residual,size=3))&(residual>1e-5))
    candidates=np.argwhere(extrema);tested=0;seen=set()
    for n in POLICY['pyramid_radius_cells']:
        print('terrain pyramid radius',n*6,'candidates',len(candidates),flush=True)
        for r,c in candidates:
            if r<n or c<n or r+n>=len(H) or c+n>=len(H):continue
            key=(int(r),int(c))
            if key in seen:continue
            patch=H[r-n:r+n+1,c-n:c+n+1]
            edge=np.r_[patch[0],patch[-1],patch[1:-1,0],patch[1:-1,-1]]
            if H[r,c]-np.median(edge)<POLICY['pyramid_relief_m']:continue
            tested+=1;fit=pyramid_fit(patch)
            if fit['detected']:
                seen.add(key);findings.append(dict(kind='faceted_pyramid',row=int(r),col=int(c),xy=[int(c*6),int(12282-r*6)],radius_m=n*6,domains=tags(r,c),**fit))
    print('terrain rectangles',flush=True)
    for f in rectangle_components(H):
        r,c=int(round(f['row'])),int(round(f['col']));f.update(xy=[c*6,12282-r*6],domains=tags(r,c));findings.append(f)
    return dict(findings=findings,finding_counts=dict(collections.Counter(f['kind'] for f in findings)),
                apex_candidates=len(candidates),fitted_patches=tested,vertices=H.size,
                excluded_border_for_pyramid_m=[12,24,48],
                limits=['Rectangle screen covers isolated closed edge components; fused edges may be missed.',
                        'Pyramid screen fits closed square/diamond tents plus a plane; truncated peaks, arbitrary subcell phases and non-tent facets are not certified.'],
                scope='Native grid only. Domain tags do not suppress findings or authorize edits; model bed/silhouette requires separate review.'),H


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('build','pilot','terrain','footprint','wrp','output'):ap.add_argument('--'+name,type=Path,required=True)
    ap.add_argument('--terrain-sha256',required=True);ap.add_argument('--wrp-sha256',required=True)
    a=ap.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    if sha(a.terrain)!=a.terrain_sha256 or sha(a.wrp)!=a.wrp_sha256:raise ValueError('candidate identity mismatch')
    H=np.load(a.terrain)['heights']
    if H.shape!=(2048,2048) or not np.isfinite(H).all():raise ValueError('invalid terrain')
    inputs={str(p):sha(p) for p in (a.terrain,a.footprint,a.wrp,Path(__file__),HERE/'shape_patterns_ev112.py',Path(D.__file__))}
    a.output.mkdir(parents=True);(a.output/'policy.json').write_text(json.dumps(POLICY,indent=2))
    placed,count=placed_water(a.wrp,H);rivers,paths=river_screen(a.build,a.pilot,placed,inputs)
    (a.output/'rivers.json').write_text(json.dumps(rivers,indent=2,allow_nan=False))
    np.savez_compressed(a.output/'river-lines.npz',**{sid+'__'+str(i):p for sid,parts in paths.items() for i,p in enumerate(parts)})
    terrain,H=terrain_screen(a.terrain,a.footprint)
    (a.output/'terrain.json').write_text(json.dumps(terrain,indent=2,allow_nan=False))
    counts=dict(rivers=rivers['finding_counts'],terrain=terrain['finding_counts'])
    pending=any(counts['rivers'].values()) or any(counts['terrain'].values()) or bool(rivers['open_sites'])
    result=dict(status='REVIEW_REQUIRED' if pending else 'PATTERN_SCREEN_CLEAR',visual_acceptance=False,policy=POLICY,counts=counts,
                river_open_sites=rivers['open_sites'],source_wrp_objects=count,inputs=inputs,
                limits=['No global aesthetic PASS. Findings are review triggers, not universal defects.',
                        'Original protected domains, missing reaches, receptors and visual pilot gate remain open.',
                        'Rounded staircases require repeated long straight anchors; no complete silhouette coverage is claimed.',
                        'Terrain fused rectangles, truncated peaks and arbitrary facet shapes remain outside certified coverage.',
                        'No terrain, river, forest, PBO or deployed artifacts were modified.'])
    (a.output/'report.json').write_text(json.dumps(result,indent=2,allow_nan=False))
    print(json.dumps({k:v for k,v in result.items() if k not in ('inputs','policy')},indent=2))
    raise SystemExit(2 if pending else 0)


if __name__=='__main__':main()
