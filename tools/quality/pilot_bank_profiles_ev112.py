"""Piecewise-linear section diagnostics, not longitudinal or visual acceptance."""
import math
import numpy as np

FIELDS=('min_B_H','max_B_H','max_B_section_W','left_above_H_length','right_above_H_length',
        'left_dry_above_H_length','right_dry_above_H_length','left_outer_reach','right_outer_reach')

def require(ok,msg):
    if not bool(ok):raise ValueError(msg)

def native(h,xz,cell=6.):
    p=np.asarray(xz,float); n=len(h);top=(n-1)*cell
    require(h.shape==(n,n) and np.isfinite(p).all() and (p>=0).all() and (p<=top).all(),'native_domain')
    u=p[...,0]/cell;v=(top-p[...,1])/cell
    c=np.minimum(np.floor(u).astype(int),n-2);r=np.minimum(np.floor(v).astype(int),n-2)
    f=u-c;g=v-r
    a=np.asarray(h[r,c],float);b=np.asarray(h[r,c+1],float)
    d=np.asarray(h[r+1,c],float);e=np.asarray(h[r+1,c+1],float)
    require(np.isfinite([a,b,d,e]).all(),'nonfinite_native_height')
    return np.where(f>=g,a+(b-a)*f+(e-b)*g,a+(d-a)*g+(e-d)*f)

def cuts(a,b,top,cell=6.):
    a=np.array([a[0]/cell,(top-a[1])/cell]);b=np.array([b[0]/cell,(top-b[1])/cell])
    result={0.,1.}
    for x,y in ((a[0],b[0]),(a[1],b[1]),(a[1]-a[0],b[1]-b[0])):
        if x==y:continue
        for k in range(math.floor(min(x,y))+1,math.ceil(max(x,y))):
            t=(k-x)/(y-x)
            if 0<t<1:result.add(float(t))
    return np.array(sorted(result))

def positive_interval(a,b):
    """Open positive region represented by closed endpoints; zero length ignored exactly."""
    if max(a,b)<=0:return None
    if min(a,b)>=0:return (0.,1.)
    root=a/(a-b)
    return (root,1.) if b>0 else (0.,root)

def intersect(a,b):
    if a is None or b is None:return None
    lo=max(a[0],b[0]);hi=min(a[1],b[1])
    return (lo,hi) if hi>lo else None

def row_profile(row,water,h,cell=6.,extrapolated=False):
    row=np.asarray(row,float);water=np.asarray(water,float)
    require(row.ndim==2 and row.shape[1]==3 and len(row)%2==1 and np.isfinite(row).all(),'row_shape')
    require(water.shape==(2,3) and np.isfinite(water).all() and water[0,1]==water[1,1],'water_row')
    delta=water[1,(0,2)]-water[0,(0,2)];width=float(np.linalg.norm(delta))
    require(width>0,'zero_water_width');normal=delta/width
    centre=row[len(row)//2,(0,2)]
    q=(row[:,(0,2)]-centre)@normal
    require(np.all(np.diff(q)>0),'inverted_or_collapsed_section')
    values=dict.fromkeys(FIELDS,0.);values['min_B_H']=math.inf;values['max_B_H']=-math.inf
    values['max_B_section_W']=-math.inf
    # CAP uses the endpoint water width translated to its own centre, not an actual water footprint.
    edges=(-width/2,width/2) if extrapolated else (water[:,(0,2)]-centre)@normal
    crossings=[];length_accounted=0.
    for j,(a,b) in enumerate(zip(row[:-1],row[1:])):
        side='left' if j<len(row)//2 else 'right'
        dx=b[(0,2),]-a[(0,2),];length=float(np.linalg.norm(dx));require(length>0,'zero_section_segment')
        ts=cuts(a[(0,2),],b[(0,2),],(len(h)-1)*cell,cell)
        points=a[None]+(b-a)[None]*ts[:,None]
        dh=points[:,1]-native(h,points[:,(0,2)],cell);dw=points[:,1]-water[0,1]
        values['min_B_H']=min(values['min_B_H'],float(dh.min()))
        values['max_B_H']=max(values['max_B_H'],float(dh.max()))
        values['max_B_section_W']=max(values['max_B_section_W'],float(dw.max()))
        for k in range(len(ts)-1):
            span=length*(ts[k+1]-ts[k]);length_accounted+=span
            exposed=positive_interval(dh[k],dh[k+1]);dry=intersect(exposed,positive_interval(dw[k],dw[k+1]))
            if exposed:values[side+'_above_H_length']+=span*(exposed[1]-exposed[0])
            if dry:
                values[side+'_dry_above_H_length']+=span*(dry[1]-dry[0])
                for f in dry:
                    t=ts[k]+(ts[k+1]-ts[k])*f;coord=(a[(0,2),]+dx*t-centre)@normal
                    reach=edges[0]-coord if side=='left' else coord-edges[1]
                    values[side+'_outer_reach']=max(values[side+'_outer_reach'],float(reach))
            for name,z in (('H',dh),('SECTION_W',dw)):
                za,zb=z[k],z[k+1]
                if za==0:crossings.append(dict(field=name,side=side,segment=j,t=float(ts[k]),xyz=points[k].tolist()))
                if (za<0<zb) or (zb<0<za):
                    t=ts[k]+(ts[k+1]-ts[k])*za/(za-zb)
                    crossings.append(dict(field=name,side=side,segment=j,t=float(t),xyz=(a+(b-a)*t).tolist()))
        if dh[-1]==0:crossings.append(dict(field='H',side=side,segment=j,t=1.,xyz=b.tolist()))
        if dw[-1]==0:crossings.append(dict(field='SECTION_W',side=side,segment=j,t=1.,xyz=b.tolist()))
    total=float(np.linalg.norm(np.diff(row[:,(0,2)],axis=0),axis=1).sum())
    require(abs(length_accounted-total)<=1e-10*max(1,total),'profile_length_gap')
    for side in ('left','right'):
        require(values[side+'_dry_above_H_length']<=values[side+'_above_H_length']+1e-12,'dry_length_subset')
    perpendicular=np.array([-normal[1],normal[0]])
    return dict(metrics=values,crossings=crossings,section_water_width=width,
                maximum_row_offaxis_residual=float(np.max(abs((row[:,(0,2)]-centre)@perpendicular))),
                water_midpoint_minus_bed_centre=(water[:,(0,2)].mean(axis=0)-centre).tolist(),
                water_reference_extrapolated=bool(extrapolated),width_below_nominal_4p5=width<4.5)

def candidate_guard(source,candidate,site):
    require(site=='kit-7','candidate_wrong_site')
    require(set(source)==set(candidate),'candidate_keys')
    for k,a in source.items():
        b=candidate[k];require(a.shape==b.shape and a.dtype==b.dtype and np.isfinite(b).all(),'candidate_shape_or_finitude')
        if k!='bed':require(np.array_equal(a,b),'candidate_changed_'+k)
    require(np.array_equal(source['bed'][:,:,(0,2)],candidate['bed'][:,:,(0,2)]),'candidate_changed_XZ')

def attach_grid(target,seen,start,grid):
    require(start>=0 and start+len(grid)<=len(target),'grid_range')
    sl=slice(start,start+len(grid));occupied=seen[sl]
    require(np.array_equal(target[sl][occupied],grid[occupied]),'discordant_shared_rows')
    target[sl]=grid;seen[sl]=True

def face_classes(excluded,triangles):
    a=np.asarray(excluded,bool).ravel()[triangles]
    return np.where(a.all(axis=1),0,np.where(a.any(axis=1),1,2)).astype(np.uint8)

def dry_contract(bed,water_y,station,ground,touched,cap_extra):
    qs=np.unique(np.r_[np.arange(-18,19,dtype=float),-2.25,2.25])
    require(bed.shape[1]==len(qs),'q_domain')
    wet=np.broadcast_to(abs(qs)<=2.25,bed.shape[:2]);border=np.broadcast_to(abs(qs)==18,bed.shape[:2])
    # station for extra CAP may extend beyond the body; these rows are always excluded separately.
    body=~cap_extra;lo=float(station[body].min());hi=float(station[body].max())
    cap=np.broadcast_to((np.minimum(station-lo,hi-station)<=6)[:,None],bed.shape[:2])
    floor=np.maximum(ground+.02,np.where(bed[:,:,1]>=water_y[:,None]+.025,water_y[:,None]+.025,-np.inf))
    infeasible=floor>bed[:,:,1];quant_bad=np.ceil(floor*512)>np.floor(bed[:,:,1]*512)
    extra=np.broadcast_to(cap_extra[:,None],bed.shape[:2])
    reasons=dict(wet_profile=wet,outer_border=border,endpoint_transition=cap,extra_cap=extra,
                 touched_legacy_protection=touched,floor_above_original=infeasible,no_quantized_value=quant_bad)
    excluded=np.logical_or.reduce(list(reasons.values()))
    return excluded,reasons,floor
