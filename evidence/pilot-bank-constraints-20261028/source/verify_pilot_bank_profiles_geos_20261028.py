"""Independent GEOS/native-face consumer. Does not import section producer/cut/H functions."""
from pathlib import Path
import sys,json,time,hashlib,importlib.util,math
import numpy as np
from shapely.geometry import Polygon,LineString
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025')
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
I=R/'pilot-bank-constraint-census-20261028';O=R/'pilot-bank-constraint-consumer-20261028'
def load(p):
    with np.load(p,allow_pickle=False) as f:return {k:f[k] for k in f.files}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def bary_samples(h,p):
    """Native triangle barycentric coordinates from cell-relative determinant, float64 first."""
    p=np.asarray(p,float);u=p[...,0]/6;v=(12282-p[...,1])/6
    c=np.minimum(np.floor(u).astype(int),2046);r=np.minimum(np.floor(v).astype(int),2046)
    f=u-c;z=v-r;lower=z>f
    # Triangles00,10,11 if below diagonal; otherwise00,01,11.
    vals=np.stack((h[r,c],np.where(lower,h[r+1,c],h[r,c+1]),h[r+1,c+1]),axis=-1).astype(float)
    weights=np.stack((1-np.maximum(f,z),abs(f-z),np.minimum(f,z)),axis=-1)
    return np.sum(vals*weights,axis=-1)

def geos_cuts(a,b):
    delta=b-a;den=float(delta@delta);assert den>0
    line=LineString([a,b]);low=np.minimum(a,b);high=np.maximum(a,b);ts={0.,1.}
    r0=max(0,math.floor((12282-high[1])/6));r1=min(2046,math.floor((12282-low[1])/6))
    c0=max(0,math.floor(low[0]/6));c1=min(2046,math.floor(high[0]/6))
    lengths=[]
    for r in range(r0,r1+1):
        for c in range(c0,c1+1):
            q=np.array([[6*c,12282-6*r],[6*(c+1),12282-6*r],[6*c,12282-6*(r+1)],[6*(c+1),12282-6*(r+1)]],float)
            for ids in ((0,1,3),(0,2,3)):
                cut=line.intersection(Polygon(q[list(ids)]))
                if cut.is_empty:continue
                if cut.geom_type=='Point':points=list(cut.coords)
                elif cut.geom_type=='LineString':points=list(cut.coords);lengths.append(cut)
                else:raise ValueError('unexpected section intersection:'+cut.geom_type)
                for p in points:ts.add(float(np.clip((np.asarray(p)-a)@delta/den,0,1)))
    from shapely import union_all
    assert abs(union_all(lengths).length-line.length)<=1e-7,'GEOS coverage'
    return np.array(sorted(ts))

def row(row,water,h,geometry=None,extrapolated=False):
    # GEOS clipping is reused for candidate only because XZ equality is separately asserted.
    if geometry is None:geometry=[geos_cuts(a[[0,2]],b[[0,2]]) for a,b in zip(row[:-1],row[1:])]
    n=(water[1,[0,2]]-water[0,[0,2]]);width=float(np.linalg.norm(n));n/=width
    mid=row[len(row)//2,[0,2]];metrics=np.zeros(9);metrics[0]=np.inf;metrics[1:3]=-np.inf
    edges=np.array([-width/2,width/2]) if extrapolated else (water[:,[0,2]]-mid)@n
    for j,(a,b,t) in enumerate(zip(row[:-1],row[1:],geometry)):
        p=a+(b-a)*t[:,None];hdelta=p[:,1]-bary_samples(h,p[:,[0,2]]);wdelta=p[:,1]-water[0,1]
        metrics[0]=min(metrics[0],float(hdelta.min()));metrics[1]=max(metrics[1],float(hdelta.max()));metrics[2]=max(metrics[2],float(wdelta.max()))
        side=0 if j<len(row)//2 else 1;length=float(np.linalg.norm(b[[0,2]]-a[[0,2]]))
        for k in range(len(t)-1):
            roots=[0.,1.]
            for d in (hdelta,wdelta):
                if d[k]!=d[k+1]:
                    root=float(d[k]/(d[k]-d[k+1]))
                    if 0<root<1:roots.append(root)
            roots=sorted(set(roots))
            for start,end in zip(roots[:-1],roots[1:]):
                centre=(start+end)/2
                dh=hdelta[k]+centre*(hdelta[k+1]-hdelta[k]);dw=wdelta[k]+centre*(wdelta[k+1]-wdelta[k])
                span=length*(t[k+1]-t[k])*(end-start)
                if dh>0:
                    metrics[3+side]+=span
                    if dw>0:
                        metrics[5+side]+=span
                        for f in (start,end):
                            global_t=t[k]+(t[k+1]-t[k])*f
                            point=a[[0,2]]+(b[[0,2]]-a[[0,2]])*global_t
                            q=float((point-mid)@n);reach=edges[0]-q if side==0 else q-edges[1]
                            metrics[7+side]=max(metrics[7+side],reach)
    return metrics,geometry

def reconstruct_masks(context):
    base=load(context['paths']['base']);h=load(context['paths']['support'])['heights'].astype(float)
    names=['reserve','platform','narva','v31_bridge_cut','v31_bridge_fill','v31_dam','v31_causeway','v31_shore_ramp']
    names += [k for k in ('v31_road_repair','v31_road_mesh_repair','v31_continuous_pilot') if k in base]
    masks={k:base[k] for k in names}
    # Frozen road-guard helper is an external policy reference, shared with the historic checker.
    sys.path.insert(0,str(W/'tools/terrain'));from shape_repair_constraints_ev112 import s3_road_guard
    masks['s3_road_guard']=s3_road_guard()[0]
    plane=load(context['paths']['footprint'])['plane'];wet=np.isfinite(plane)
    masks['old_footprint_pond']=np.pad(wet,((0,1),(0,1)))|np.pad(wet,((1,0),(0,1)))|np.pad(wet,((0,1),(1,0)))|np.pad(wet,((1,0),(1,0)))
    z=12282-np.arange(2048)*6;x=np.arange(2048)*6
    masks['crossing_015_45_60m']=np.sqrt((x[None]-10397.4)**2+(z[:,None]-9421.9)**2)<=60
    return h,masks

def same(a,b,label):
    if a.shape!=b.shape or a.dtype!=b.dtype or not np.array_equal(a,b):raise ValueError(label)

def source_guard(f,source,candidate=None):
    n=len(source['bed']);assert f['grid'].shape==(n+16,39,3)
    same(f['grid'][8:-8],source['bed'],'baseline_body_not_source')
    same(f['baseline_grid'],f['grid'],'baseline_variant_changed')
    same(f['water'][8:-8],source['water'],'body_water_changed')
    same(f['water'][:8],np.repeat(source['water'][:1],8,axis=0),'start_reference_changed')
    same(f['water'][-8:],np.repeat(source['water'][-1:],8,axis=0),'end_reference_changed')
    same(f['station'][8:-8],source['station'],'body_station_changed')
    same(f['station'],np.r_[source['station'][0]-np.arange(8,0,-1),source['station'],source['station'][-1]+np.arange(1,9)],'station_metadata_changed')
    cap=np.zeros(n+16,bool);cap[:8]=True;cap[-8:]=True;same(f['extra_cap'],cap,'cap_labels_changed')
    if candidate is not None:
        same(f['candidate_grid'][8:-8],candidate['bed'],'candidate_body_not_input')
        same(f['candidate_grid'][cap],f['grid'][cap],'candidate_cap_changed')
    elif 'candidate_grid' in f:raise ValueError('candidate_on_wrong_site')

def main():
    O.mkdir(exist_ok=False);start=time.monotonic()
    spec=importlib.util.spec_from_file_location('meter',W/'tools/quality/water_constraint_diagnostic_ev112.py');meter=importlib.util.module_from_spec(spec);spec.loader.exec_module(meter)
    meter.STARTED=start;meter.MAX_SECONDS=600;stop=meter.bounded(O)
    try:
        inputs=json.loads((I/'inputs.json').read_bytes());pins=inputs['pins']
        for p,d in pins.items():assert sha(p)==d,p
        ctx=json.loads((R/'dry-bank-visual-water-setup-20261027/context.json').read_bytes());h,masks=reconstruct_masks(ctx)
        source=R/'pilot-visible-surface-extraction-20261028';models=json.loads((source/'models.json').read_bytes())
        exraw=R/'pilot-visible-exposure-census-r2-20261028';emodels={m['model']:m for m in json.loads((exraw/'models.json').read_bytes())}
        faceout={m['model']:m for m in json.loads((I/'face-partitions.json').read_bytes())};maxdiff=np.zeros(9);count=0;facecount=0;reports=[]
        sites=json.loads((I/'sites.json').read_bytes());assert len(sites)==4 and {s['site'] for s in sites}=={'kit-7','kit-118','65.0-0','131.0-0'}
        candidate_input=load(R/'dry-bank-visual-water-pilot-20261027/candidate-surfaces.npz')
        expected_profiles=0
        files={str(I/'inputs.json'):sha(I/'inputs.json'),str(I/'face-partitions.json'):sha(I/'face-partitions.json'),str(I/'sites.json'):sha(I/'sites.json')}
        for s in sites:
            p=I/s['file'];assert sha(p)==s['sha256'];files[str(p)]=sha(p);f=load(p);grid=f['grid'];water=f['water'];station=f['station']
            sp=R/('river-kit7-contact-only-20261026/kit-7-surfaces.npz' if s['site']=='kit-7' else 'collision-overlap-u2/'+s['site']+'-surfaces.npz')
            assert str(sp) in pins;source_arrays=load(sp)
            source_guard(f,source_arrays,candidate_input if s['site']=='kit-7' else None)
            expected_profiles+=(len(source_arrays['bed'])+16)*(2 if s['site']=='kit-7' else 1)
            assert list(f['metric_fields'])==['min_B_H','max_B_H','max_B_section_W','left_above_H_length','right_above_H_length','left_dry_above_H_length','right_dry_above_H_length','left_outer_reach','right_outer_reach']
            assert set(f['protection_names'])==set(masks)
            actual_touch=np.array([bary_samples(masks[name],grid[:,:,[0,2]])>0 for name in f['protection_names']])
            np.testing.assert_array_equal(actual_touch,f['protection_touch'])
            ground=bary_samples(h,grid[:,:,[0,2]]);assert np.max(abs(ground-f['ground']))<=1e-9
            qs=np.array(list(range(-18,-2))+[-2.25,-2,-1,0,1,2,2.25]+list(range(3,19)),float);assert len(qs)==39
            reasons={'wet_profile':np.broadcast_to(abs(qs)<=2.25,grid.shape[:2]),'outer_border':np.broadcast_to(abs(qs)==18,grid.shape[:2]),
                'endpoint_transition':np.broadcast_to((np.minimum(station,station[-9]-station)<=6)[:,None],grid.shape[:2]),
                'extra_cap':np.broadcast_to(f['extra_cap'][:,None],grid.shape[:2]),'touched_legacy_protection':actual_touch.any(axis=0)}
            floor=ground+.02;was_dry=grid[:,:,1]>=water[:,0,1,None]+.025
            floor[was_dry]=np.maximum(floor,np.broadcast_to(water[:,0,1,None]+.025,floor.shape))[was_dry]
            reasons['floor_above_original']=floor>grid[:,:,1];reasons['no_quantized_value']=np.ceil(floor*512)>np.floor(grid[:,:,1]*512)
            for name,mask in zip(f['reason_names'],f['reasons']):np.testing.assert_array_equal(mask,reasons[name])
            assert set(f['reason_names'])==set(reasons)
            excluded=np.array(list(reasons.values())).any(axis=0);np.testing.assert_array_equal(excluded,f['excluded'])
            if s['site']=='kit-7':
                c=f['candidate_grid'];np.testing.assert_array_equal(c[:,:,[0,2]],grid[:,:,[0,2]]);np.testing.assert_array_equal(c[excluded],grid[excluded])
            localdiff=np.zeros(9)
            for i in range(len(grid)):
                base,geom=row(grid[i],water[i],h,extrapolated=bool(f['extra_cap'][i]));delta=abs(base-f['baseline_metrics'][i]);localdiff=np.maximum(localdiff,delta);count+=1
                if s['site']=='kit-7':
                    candidate,_=row(f['candidate_grid'][i],water[i],h,geom,extrapolated=bool(f['extra_cap'][i]));localdiff=np.maximum(localdiff,abs(candidate-f['candidate_metrics'][i]));count+=1
                direction=water[i,1,[0,2]]-water[i,0,[0,2]];width=float(np.linalg.norm(direction));direction/=width
                centre=grid[i,19,[0,2]];offset=(water[i,0,[0,2]]+water[i,1,[0,2]])*.5-centre
                residual=float(np.max(abs((grid[i][:,[0,2]]-centre)@np.array([-direction[1],direction[0]]))))
                for variant in ('baseline','candidate') if s['site']=='kit-7' else ('baseline',):
                    assert abs(width-f[variant+'_section_water_width'][i])<=1e-12
                    assert abs(residual-f[variant+'_maximum_row_offaxis_residual'][i])<=1e-12
                    assert np.max(abs(offset-f[variant+'_water_midpoint_minus_bed_centre'][i]))<=1e-12
                    assert f[variant+'_width_below_nominal_4p5'][i]==(width<4.5)
            assert np.all(localdiff[:3]<=1e-9) and np.all(localdiff[3:]<=1e-7),(s['site'],localdiff)
            maxdiff=np.maximum(maxdiff,localdiff)
            for m in (m for m in models if m['site']==s['site']):
                mf=load(source/m['file']);offset=int(mf['npz_start'])+8-int(mf['cap_before']);mask=excluded[offset:offset+len(mf['source_grid'])].ravel()
                same(grid[offset:offset+len(mf['source_grid'])],mf['source_grid'],'assembled_grid_not_sealed_model')
                verts=mf['source_triangles'][mf['bed_source_face']];bits=mask[verts];cla=np.zeros(len(bits),int)
                for j,values in enumerate(bits):cla[j]=0 if all(values) else (1 if any(values) else 2)
                data=load(exraw/emodels[m['model']]['file']);ni=list(data['fields']).index('corridor_rectangle_above_H_area')
                for k,name in enumerate(('ALL_DRY_PILOT_EXCLUDED','MIXED','ALL_POINT_FREE')):
                    got=sum(t['corridor_rectangle_above_H_area'] for t in faceout[m['model']]['groups'] if t['dry_pilot_class']==name)
                    expected=float(data['metrics'][cla==k,ni].sum());assert abs(got-expected)<=1e-10
                assert sum(t['faces'] for t in faceout[m['model']]['groups'])==len(cla);facecount+=len(cla)
            reports.append(dict(site=s['site'],rows=len(grid),maximum_residual=localdiff.tolist(),mask_values_verified=int(f['reasons'].size+f['protection_touch'].size)))
            write(O/'progress.json',dict(sites=len(reports),profiles=count,faces=facecount,measurement=meter.memory()))
        assert facecount==185744 and count==expected_profiles
        for p,d in {**pins,**files}.items():assert sha(p)==d,p
        write(O/'inputs.json',dict(pins=files,consumer_sha256=sha(__file__)))
        write(O/'sites.json',reports)
        report=dict(status='ALL_STORED_SECTIONS_AND_DRY_CONTRACT_VERIFIED',profiles=count,faces=facecount,maximum_residual=maxdiff.tolist(),measurement=meter.memory(),
            limits=['All stored transverse sections, not longitudinal surface/render acceptance.','Historic road guard is a shared external policy reference; section cuts/heights and mask evaluation independent of new producer.','No repair or water/topology change.'])
        write(O/'report.json',report);print(json.dumps(report))
    except Exception as e:write(O/'failure.json',dict(error=str(e),type=type(e).__name__,measurement=meter.memory()));raise
    finally:stop.set()
if __name__=='__main__':main()
