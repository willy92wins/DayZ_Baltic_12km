"""Approved EV112 continuous-river PILOT, isolated outputs only.

Uses the pre-kit thalweg, not the cardinal lattice. Authors a curved bed and
water strip in <=12 m chunks, vanilla stream materials, water_ext roadway and
closed triangular-prism bed collision components. Terrain is a buried support,
not the visible narrow V. No production deployment or visual acceptance here.

Source anchors: streambed_kit_v31.site_axis/reach_axis/tri_h; native streambed
ODOL for water visual 0.25 m above water_ext, house property, material paths;
pond_author_v31 for MLOD authoring and origin + compiled bounding-centre rule.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
from scipy.ndimage import label, gaussian_filter, distance_transform_edt, minimum_filter1d, gaussian_filter1d
from scipy.interpolate import CubicSpline
from scipy.spatial import cKDTree
from scipy.optimize import minimize

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), 'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/py3d']
import py3d
import streambed_kit_v31 as kit
assert py3d.IS_DAYZ_FORK
PREFIX = 'baltic_stream_pilot'
WATER_TEX = r'dz\water\streams\data\streams_flowmap_ca.paa'
WATER_MAT = r'dz\water\streams\data\water_streambed.rvmat'
BED_TEX = r'dz\water\streambed\data\cp_stream_gravel_co.paa'
BED_MAT = r'dz\water\streambed\data\streambed_leaf_long_straight.rvmat'
WATER_ROAD = r'dz\surfaces\data\roadway\water_ext.paa'
BED_ROAD = r'dz\surfaces\data\roadway\gravel_small_ext.paa'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def model_config(instances):
    # P:/DZ/water/config.cpp:16-21: house models require Land_<stem>.
    classes=[]
    for inst in instances:
        model=inst['model'];stem=model.rsplit('\\',1)[-1].removesuffix('.p3d')
        classes.append('class Land_'+stem+': HouseNoDestruct { scope=1; model="\\'+model+'"; };')
    return ('class CfgPatches { class Baltic_Stream_Pilot { units[]={}; weapons[]={}; requiredVersion=0.1; requiredAddons[]={"DZ_Water","DZ_Surfaces"}; }; };\n'
            +'class CfgVehicles { class HouseNoDestruct;\n'+'\n'.join(classes)+'\n};\n')


def smoothstep(x):
    x=np.clip(x,0,1)
    return x*x*(3-2*x)


def fair_energy(H, prior, weight=.002):
    """Thin-plate energy and analytic gradient on the native sample grid."""
    dx=H[:,:-2]-2*H[:,1:-1]+H[:,2:]
    dz=H[:-2]-2*H[1:-1]+H[2:]
    cross=H[:-1,:-1]-H[1:,:-1]-H[:-1,1:]+H[1:,1:]
    g=weight*(H-prior)
    g[:,:-2]+=dx;g[:,1:-1]-=2*dx;g[:,2:]+=dx
    g[:-2]+=dz;g[1:-1]-=2*dz;g[2:]+=dz
    g[:-1,:-1]+=2*cross;g[1:,:-1]-=2*cross;g[:-1,1:]-=2*cross;g[1:,1:]+=2*cross
    return .5*(np.sum(dx*dx)+np.sum(dz*dz)+2*np.sum(cross*cross)+weight*np.sum((H-prior)**2)),g


def fair_support(current, prior, free, floor, ceiling):
    """One bounded solve; exact fixed vertices and explicit wet-support caps.

    This only authors the replacement model's local terrain support, not the
    later map-wide relief pass. Max 500 iterations. A feasible capped result
    may be inspected as a candidate; convergence is never visual acceptance.
    """
    free=free.copy();free[[0,-1],:]=False;free[:,[0,-1]]=False
    lo=np.asarray(floor)[free];hi=np.asarray(ceiling)[free]
    assert np.all(lo<=hi), 'water/support constraints conflict'
    def objective(x):
        h=current.copy();h[free]=x;value,gradient=fair_energy(h,prior)
        return value,gradient[free]
    initial=np.clip(current[free],lo,hi)
    result=minimize(objective,initial,method='L-BFGS-B',jac=True,bounds=list(zip(lo,hi)),
                    options={'maxiter':500,'ftol':1e-11,'gtol':1e-5,'maxls':30})
    report=dict(success=bool(result.success),message=str(result.message),iterations=int(result.nit),
                energy_before=float(objective(initial)[0]),energy_after=float(result.fun))
    report['bounds_satisfied']=bool(np.isfinite(result.x).all() and np.all(result.x>=lo) and np.all(result.x<=hi))
    assert report['bounds_satisfied'] and (result.success or (result.status==1 and result.nit==500)), report
    h=current.copy();h[free]=result.x
    return h,report


def add_mesh(lod, points, triangles, texture='', material='', upward_normal=False, uv=None, uv1=None):
    """Visual sheets use native stream winding (geometric normal down).
    Roadway keeps that winding and stores the native positive normal.
    """
    points = np.asarray(points, float)
    triangles = np.asarray(triangles, int).copy()
    normals = np.cross(points[triangles[:,1]]-points[triangles[:,0]], points[triangles[:,2]]-points[triangles[:,0]])
    flip = normals[:,1] > 0
    triangles[flip] = triangles[flip][:,::-1]
    normals[flip] *= -1
    size = np.linalg.norm(normals, axis=1)
    assert np.all(size > 1e-9), 'degenerate surface triangle'
    normals /= size[:,None]
    accumulated = np.zeros_like(points)
    for j in range(3): np.add.at(accumulated, triangles[:,j], normals)
    nlen = np.linalg.norm(accumulated, axis=1)
    accumulated[nlen > 0] /= nlen[nlen > 0,None]
    if upward_normal: accumulated *= -1
    offset, noffset = len(lod.points), len(lod.facenormals)
    for xyz,n in zip(points, accumulated):
        p=py3d.Point(); p.coords=tuple(xyz); p.mass=None; lod.points.append(p)
        lod.facenormals.append(tuple(n))
    for tri in triangles:
        f=py3d.Face(lod.points,lod.facenormals); f.texture=texture; f.material=material
        for ix in tri:
            v=py3d.Vertex(lod.points,lod.facenormals)
            v.point_index=int(offset+ix);v.normal_index=int(noffset+ix)
            v.uv=tuple(uv[ix]) if uv is not None else (points[ix,0]/4,points[ix,2]/4)
            if uv1 is not None: v.uv_sets[1]=tuple(uv1[ix])
            f.vertices.append(v)
        lod.faces.append(f)


def add_prism(lod, top, index, depth=180/512):
    top=np.asarray(top,float)
    pts=np.vstack((top, top-[0,depth,0]))
    faces=[[0,1,2],[5,4,3],[0,3,4],[0,4,1],[1,4,5],[1,5,2],[2,5,3],[2,3,0]]
    centre=pts.mean(0); offset=len(lod.points)
    for xyz in pts:
        p=py3d.Point();p.coords=tuple(xyz);p.mass=1;lod.points.append(p)
    selection=py3d.Selection(lod.points,lod.faces)
    volume=0.
    for ids in faces:
        t=pts[ids];n=np.cross(t[1]-t[0],t[2]-t[0])
        if n@(t.mean(0)-centre)>0: ids=ids[::-1];t=pts[ids];n=-n
        norm=np.linalg.norm(n);assert norm>1e-9
        n/=norm;ni=len(lod.facenormals);lod.facenormals.append(tuple(n))
        f=py3d.Face(lod.points,lod.facenormals)
        for ix in ids:
            v=py3d.Vertex(lod.points,lod.facenormals);v.point_index=offset+ix;v.normal_index=ni;v.uv=(0.,0.)
            f.vertices.append(v);selection.points[lod.points[offset+ix]]=1
        lod.faces.append(f);selection.faces[f]=1
        volume+=np.dot(t[0]-centre,np.cross(t[1]-centre,t[2]-centre))/6
    assert volume < -1e-9, ('collision winding',volume)
    lod.selections[f'Component{index:04d}']=selection
    return volume


def strip_faces(n, m):
    return np.array([(a,b,c) for i in range(n-1) for j in range(m-1)
                     for a,b,c in ((i*m+j,(i+1)*m+j,(i+1)*m+j+1),
                                   (i*m+j,(i+1)*m+j+1,i*m+j+1))], int)


def axis_for(site, vp, wet, lab):
    if site.get('mode','component')=='component':
        body,_,P,s,W=kit.site_axis(site,vp,wet,lab)
        # Recover the exact unsampled source terminal from the same component.
        sr,sc=np.argwhere(body)[0];raw=kit.path_between(body,kit.path_between(body,(int(sr),int(sc)))[0])
        if vp[raw[0]]<vp[raw[-1]]:raw=raw[::-1]
        raw=np.array([kit.xz(*v) for v in raw])
    else:
        P,s,W=kit.reach_axis(site,vp)
        raw=np.array([kit.xz(*v) for v in site['stem']])
        assert not site.get('extend'), 'pilot currently limited to natural ends'
    # Fit the coarse smoothed source vertices. Fitting a spline to the dense
    # piecewise-linear resample concentrates its original kinks into <1 m.
    coarse=kit.smooth(raw)
    arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(coarse,axis=0),axis=1))]
    cs=CubicSpline(arc,coarse,axis=0,bc_type='natural')
    # Uniform spacing avoids a final 0.011m sliver on 65.0-0. A fairing
    # surface with metre-spaced rows otherwise changes height over that tiny
    # leftover segment, creating a visible transverse crease (pilot O).
    stations=np.linspace(0,arc[-1],int(np.ceil(arc[-1]))+1)
    centre=cs(stations);tangent=cs(stations,1);tangent/=np.linalg.norm(tangent,axis=1)[:,None]
    normal=np.c_[-tangent[:,1],tangent[:,0]]
    levels=np.interp(stations/arc[-1]*s[-1],s,W)
    # Source endpoints are wet native vertices, not the dry bank boundary.
    # Preserve them inside the wet strip and terminate over the next native cell.
    lead=np.arange(-6.,0.)
    tail=np.arange(1.,7.)
    centre=np.vstack((centre[0]+lead[:,None]*tangent[0],centre,centre[-1]+tail[:,None]*tangent[-1]))
    stations=np.r_[lead,stations,stations[-1]+tail]+6.
    levels=np.r_[np.full(6,levels[0]),levels,np.full(6,levels[-1])]
    normal=np.vstack((np.repeat(normal[:1],6,axis=0),normal,np.repeat(normal[-1:],6,axis=0)))
    return centre,stations,levels,normal,raw


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('build');ap.add_argument('out')
    ap.add_argument('--sites',nargs='+',default=['kit-118','65.0-0'])
    args=ap.parse_args();B=Path(args.build);out=Path(args.out)
    out.mkdir(parents=True,exist_ok=False);src=out/'source'/PREFIX;src.mkdir(parents=True)
    provenance=out/'provenance';provenance.mkdir()
    for source in (__file__,kit.__file__,py3d.__file__):
        path=Path(source);(provenance/path.name).write_bytes(path.read_bytes())
    tp=B/'water-fix-b/terrain.npz';fp=B/'water-fix-b/bury-work/fp0/footprint.npz'
    assert sha(tp)=='07054c46ebf2861bc905fe2d68fb3b734d7b8e9ad1d538c73a7ee745edd56d62'
    assert sha(fp)=='49ee2a69db85f047425f8e1d31a964f92771ceb19b203c42570b04c3c6207de5'
    for resource in (WATER_TEX,WATER_MAT,BED_TEX,BED_MAT,WATER_ROAD,BED_ROAD):
        assert (Path('P:/')/resource).is_file(), resource
    old=np.load(tp);arrays={k:old[k] for k in old.files};H0=arrays['heights'].astype(float);H=H0.copy()
    refpath=B.parent/'bridges/terrain-ev107.npz';ref=np.load(refpath)['heights'].astype(float)
    pl=np.load(B.parent/'bridges/fp-ev107/footprint.npz')['plane'];vp=kit.c2v_max(np.where(np.isfinite(pl),pl,-np.inf))
    wet=np.isfinite(vp)&(ref<vp);lab,_=label(wet,np.array([[1,1,0],[1,1,1],[0,1,1]]))
    sites=json.loads((B.parent/'ev112-ot1-20261018/sites-d.json').read_text())
    oldrecords=json.loads((B/'water-fix-b/kit/kit-records.json').read_text())
    frozen=arrays['reserve']|arrays['platform']|arrays['narva']|arrays['v31_bridge_cut']|arrays['v31_bridge_fill']|arrays['v31_dam']|arrays['v31_causeway']|arrays['v31_shore_ramp']
    current_fp=np.load(fp);current_pond=np.isfinite(current_fp['plane'])
    env=np.load(B/'dam/envelope-dam.npy').copy();cover=np.load(B/'dam/cover-dam.npy').copy()
    env0=env.copy();cover0=cover.copy()
    # Entire current pond-cell planes stay exact, not just wet corners.
    protected=frozen|kit.c2v(current_pond)
    rr,cc=np.mgrid[:2048,:2048];X=cc*6.;Z=12282-rr*6.
    protected |= np.hypot(X-10397.4,Z-9421.9)<=60
    instances=[];reports=[];edited=np.zeros_like(H,bool)
    for name in args.sites:
        site=next(s for s in sites if s['id']==name)
        P,s,W,N,raw=axis_for(site,vp,wet,lab)
        tree=cKDTree(P);r0=max(0,int((12282-P[:,1].max()-42)//6));r1=min(2048,int((12282-P[:,1].min()+42)//6)+2)
        c0=max(0,int((P[:,0].min()-42)//6));c1=min(2048,int((P[:,0].max()+42)//6)+2);sl=np.s_[r0:r1,c0:c1]
        q=np.c_[X[sl].ravel(),Z[sl].ravel()];dist,ix=tree.query(q)
        foreign=[r for r in oldrecords if r['site']!=name and tree.query([r['matrix'][9],r['matrix'][11]])[0]<42]
        assert not foreign, ('adjacent kit needs combined design',name)
        dist=dist.reshape(H[sl].shape);ix=ix.reshape(H[sl].shape)
        # An unused pond envelope follows the old lattice, not the new bed.
        # Retire ONLY inactive cells inside this pilot corridor. Every actual
        # current pond cell is retained, including closure cells. This prevents
        # the broad support excavation creating a second, grid-shaped pond.
        esl=np.s_[r0:min(r1,2047),c0:min(c1,2047)]
        ex=X[esl]+3;ez=Z[esl]-3
        edist=tree.query(np.c_[ex.ravel(),ez.ravel()])[0].reshape(ex.shape)
        retire=(edist<42)&~current_pond[esl]
        env[esl][retire]=np.nan;cover[esl][retire]=np.nan
        env_vp=kit.c2v_max(np.where(np.isfinite(env),env,-np.inf))
        env_protected=np.isfinite(env_vp)&(H0<env_vp+.35)
        height_floor=np.maximum(1.,np.minimum(H0,env_vp+.35))
        free=~(protected[sl]|env_protected[sl])
        fixed_distance=distance_transform_edt(~(protected|env_protected))[sl]*6
        blend=smoothstep((36-dist)/12)*smoothstep(fixed_distance/12)
        base=gaussian_filter(ref[sl],2,mode='nearest')
        # Restore the old kit's broad land deformation with a 12 m transition.
        target=H0[sl]+blend*(base-H0[sl])
        target=np.maximum(target,1.)
        # Broad buried support; exact bed and water banks are in the new mesh.
        support=W[ix]-.95 + np.maximum(dist-7,0)*.18
        burrow=smoothstep((24-dist)/17)
        # Keep the inner water support low while approaching fixed platforms
        # continuously. Cutting all free vertices to the same low shelf left
        # a one-cell cliff at the exact protected boundary (pilot J evidence).
        burrow*=smoothstep(fixed_distance/np.maximum(fixed_distance+np.maximum(dist-4,0),1e-9))
        # Do not excavate bowls beyond the two natural ends.
        along=np.minimum(s[ix],s[-1]-s[ix])
        burrow*=smoothstep(along/6)
        target=target+burrow*(np.minimum(target,support)-target)
        target=np.maximum(target,height_floor[sl])
        take=free&(blend>0)
        initial=H0[sl].copy();initial[take]=target[take]
        ceiling=np.full_like(target,np.inf)
        wet_support=(dist<8)&(along>=4)
        assert not np.any(wet_support&~free), ('wet support meets protected geometry',name)
        ceiling[wet_support]=W[ix][wet_support]-.85
        fair,solver=fair_support(initial,base,take,height_floor[sl],ceiling)
        H[sl][take]=fair[take];edited[sl]|=take
        assert np.isfinite(H[sl]).all(), 'nonfinite support terrain'
        # A bed cross-section smoothly meets the terrain over its outer 6 m.
        qs=np.unique(np.r_[np.arange(-18,19,dtype=float),-2.25,2.25])
        # Offset ribbons fold if an outer bank exceeds the local bend radius.
        # Narrow only the dry outer apron; the approved stream width stays 4.5m.
        curvature=np.linalg.norm(np.gradient(N,s,axis=0),axis=1)
        apron_limit=np.minimum(18.,.65/np.maximum(curvature,1e-9))
        apron=np.minimum(apron_limit,gaussian_filter1d(minimum_filter1d(apron_limit,17,mode='nearest'),3,mode='nearest'))
        assert apron.min()>4.,('bend too tight for pilot cross-section',name,float(apron.min()))
        qactual=np.sign(qs)[None,:]*np.where(np.abs(qs)[None,:]<=4,np.abs(qs)[None,:],
                    4+(np.abs(qs)[None,:]-4)*(apron[:,None]-4)/14)
        xy=P[:,None,:]+N[:,None,:]*qactual[:,:,None]
        ground=kit.tri_h(H,xy[...,0],xy[...,1])
        # Ends close against land over 4 m; water tapers to a small rounded cap.
        cap=smoothstep(np.minimum(s,s[-1]-s)/6)
        cross=np.interp(np.abs(qs),[0,1,2.25,4,7,10,14,18],[-.65,-.6,0,.4,.8,1.05,1.2,1.3])
        by=W[:,None]+cross[None,:]
        # Lift each submerged offset by its own depth at the natural cap.
        # Adding a uniform .65m made q=2m protrude above the water while the
        # q=2.25m bank stayed at W, producing a narrow artificial peak.
        by=W[:,None]+np.where(cross[None,:]<0,cross[None,:]*cap[:,None],cross[None,:])
        by=by*cap[:,None]+(ground-.03)*(1-cap[:,None])
        outer=smoothstep((np.abs(qs)-4)/14)[None,:]
        by=by*(1-outer)+(ground-.03)*outer
        # The bed must cover the saw-tooth support near fixed platforms. A
        # low fixed cross-section allowed native 6m triangles to protrude.
        # Fair the dry bank above the actual terrain, keeping the wet profile,
        # outer burial edge and protected platform elevations (within 2cm).
        bed_free=np.broadcast_to((np.abs(qs)>4)&(np.abs(qs)<18),by.shape).copy()
        bed_floor=np.where(bed_free,ground+.02,-np.inf)
        bed_ceiling=np.full_like(by,np.inf)
        fixed_surface=kit.tri_h(protected.astype(float),xy[...,0],xy[...,1])>.99999
        bed_ceiling[fixed_surface&bed_free]=ground[fixed_surface&bed_free]+.02
        by=np.maximum(by,bed_floor)
        by,bank_solver=fair_support(by,by,bed_free,bed_floor,bed_ceiling)
        bed=np.stack((xy[...,0],by,xy[...,1]),-1)
        # Water kept 4.5m wide through the body, tapered only at natural ends.
        half=2.25*np.maximum(cap,.015)
        wx=P[:,None,:]+N[:,None,:]*np.c_[-half,half][...,None]
        water=np.stack((wx[...,0],np.broadcast_to(W[:,None],wx.shape[:2]),wx[...,1]),-1)
        # Binarize recentres around (bbox_min+bbox_max)/2, then WRP stores
        # origin+centre as float32. At x>8192, WRP spacing is 1/1024m.
        # Quantize endpoints to twice that spacing so even a half-grid bbox
        # centre is representable. Validate this against the packed ODOL.
        bed=np.round(bed*512)/512;water=np.round(water*512)/512
        # Reject protected obstacles instead of silently lifting water over them.
        centre_ground=kit.tri_h(H,P[:,0],P[:,1]);core=(s>=6)&(s<=s[-1]-6)
        margin=float(np.min(W[core]-.25-centre_ground[core]))
        if margin<.10:
            bad=np.flatnonzero(core&(W-.25-centre_ground<.10))
            detail=dict(site=name,blocked=[dict(station=float(s[j]),xz=P[j].tolist(),water_road=float(W[j]-.25),terrain=float(centre_ground[j])) for j in bad[:20]],raw_endpoints=raw[[0,-1]].tolist())
            (out/'blocked-water.json').write_text(json.dumps(detail,indent=2),encoding='utf-8')
            raise ValueError(('terrain blocks water',name,margin,detail))
        np.savez_compressed(out/(name+'-surfaces.npz'),bed=bed,water=water,axis=P,station=s,level=W,raw=raw)
        # Exact 1m collision triangles, bounded selection-table cost per chunk.
        # Long 48m chunks made selection tags quadratic and needlessly enormous.
        for start in range(0,len(s)-1,12):
            stop=min(start+12,len(s)-1);b=bed[start:stop+1];w=water[start:stop+1]
            bst=s[start:stop+1];bq=qactual[start:stop+1]
            # Bury the entire end of the dry apron rather than leave a cut wall.
            if start==0:
                tangent=np.array([N[0,1],-N[0,0]])
                distances=np.arange(8,0,-1.)
                capxz=bed[0,:,[0,2]].T[None]-tangent[None,None,:]*distances[:,None,None]
                capground=kit.tri_h(H,capxz[...,0],capxz[...,1])-.03
                mix=smoothstep(distances/8)[:,None]
                capy=bed[0,:,1][None]*(1-mix)+capground*mix
                capbed=np.stack((capxz[...,0],capy,capxz[...,1]),-1)
                b=np.concatenate((capbed,b));bst=np.r_[s[start]-distances,bst];bq=np.vstack((np.repeat(bq[:1],8,axis=0),bq))
            if stop==len(s)-1:
                tangent=np.array([N[-1,1],-N[-1,0]])
                distances=np.arange(1,9.)
                capxz=bed[-1,:,[0,2]].T[None]+tangent[None,None,:]*distances[:,None,None]
                capground=kit.tri_h(H,capxz[...,0],capxz[...,1])-.03
                mix=smoothstep(distances/8)[:,None]
                capy=bed[-1,:,1][None]*(1-mix)+capground*mix
                capbed=np.stack((capxz[...,0],capy,capxz[...,1]),-1)
                b=np.concatenate((b,capbed));bst=np.r_[bst,s[stop]+distances];bq=np.vstack((bq,np.repeat(bq[-1:],8,axis=0)))
            b=np.round(b*512)/512
            origin=np.rint([P[(start+stop)//2,0],W[(start+stop)//2],P[(start+stop)//2,1]])
            bflat=b.reshape(-1,3)-origin;wflat=w.reshape(-1,3)-origin
            bt=strip_faces(len(b),len(qs));wt=strip_faces(len(w),2)
            model=py3d.P3D();visual=py3d.LOD();visual.resolution=0;visual.properties['lodnoshadow']='1'
            # UV0 tiles gravel/leaves; UV1 addresses the native multi mask.
            # Read from the actual streambed leaf ODOL: 1/14 cross, -1/24 along.
            buv=np.stack((bq/4.7,np.broadcast_to(-bst[:,None]/4.7,b.shape[:2])),-1).reshape(-1,2)
            maskuv=np.stack((np.clip(.5+bq/14,.002,.998),np.broadcast_to(-bst[:,None]/24,b.shape[:2])),-1).reshape(-1,2)
            add_mesh(visual,bflat,bt,BED_TEX,BED_MAT,uv=buv,uv1=maskuv)
            # Flowmap UV follows station, not cardinal axes.
            uv=np.c_[np.tile([0.,1.],len(w)),np.repeat(s[start:stop+1]/24,2)]
            add_mesh(visual,wflat,wt,WATER_TEX,WATER_MAT,uv=uv);model.lods.append(visual)
            geo=py3d.LOD();geo.resolution=1e13;geo.properties.update({'class':'house','damage':'no'})
            vols=[add_prism(geo,bflat[t],i+1) for i,t in enumerate(bt)];model.lods.append(geo)
            memory=py3d.LOD();memory.resolution=1e15
            for xyz in (np.min(bflat,0),np.max(bflat,0)):
                point=py3d.Point();point.coords=tuple(xyz);memory.points.append(point)
            model.lods.append(memory)
            road=py3d.LOD();road.resolution=3e15
            add_mesh(road,bflat,bt,BED_ROAD,upward_normal=True)
            add_mesh(road,wflat-[0,.25,0],wt,WATER_ROAD,upward_normal=True);model.lods.append(road)
            stem='cs_'+name.replace('.','p').replace('-','_')+f'_{start:04d}'
            path=src/(stem+'.p3d');model.save(str(path))
            instances.append(dict(site=name,model=PREFIX+'\\'+stem+'.p3d',origin=origin.tolist(),
                                  station=[float(s[start]),float(s[stop])],sha256=sha(path),
                                  visual_triangles=len(bt)+len(wt),collision_components=len(vols),
                                  signed_collision_volume=float(sum(vols))))
        tangent=np.diff(P,axis=0);heading=np.unwrap(np.arctan2(tangent[:,0],tangent[:,1]))
        reports.append(dict(site=name,length_m=float(s[-1]),endpoints=P[[0,-1]].tolist(),
                            original_raw_endpoints=raw[[0,-1]].tolist(),water_levels=W[[0,-1]].tolist(),
                            max_turn_per_m_deg=float(np.max(np.abs(np.diff(heading)))*180/np.pi),
                            water_road_to_terrain_min_m=margin,chunk_count=sum(i['site']==name for i in instances),
                            support_solver=solver,
                            dry_bank_solver=bank_solver,
                            ends='natural; inherited from component or source reach',
                            geometry_status='CANDIDATE; independent verification and engine test pending'))
    arrays['heights']=H.astype(np.float32);arrays['v31_continuous_pilot']=arrays['heights']!=arrays['heights'].dtype.type(H0)
    assert np.array_equal(arrays['heights'][protected],H0.astype(np.float32)[protected])
    np.savez_compressed(out/'terrain.npz',**arrays)
    np.save(out/'envelope.npy',env);np.save(out/'cover.npy',cover)
    (src/'$PBOPREFIX$').write_text(PREFIX,encoding='ascii')
    (src/'config.cpp').write_text(model_config(instances),encoding='ascii')
    result=dict(schema='continuous-stream-pilot-v1',author_source_sha256=sha(__file__),terrain_input_sha256=sha(tp),footprint_sha256=sha(fp),
                reference_terrain_sha256=sha(refpath),terrain_sha256=sha(out/'terrain.npz'),
                sites=reports,instances=instances,removed_sites=args.sites,
                changed_vertices=int(arrays['v31_continuous_pilot'].sum()),
                retired_inactive_envelope_cells=int((np.isfinite(env0)&~np.isfinite(env)).sum()),
                retired_inactive_cover_cells=int((np.isfinite(cover0)&~np.isfinite(cover)).sum()),
                protected_vertices_unchanged=True,production_deployed=False,
                limitations=['Mesh self-consistency is not engine water, walking collision or visual acceptance.',
                             'The material is vanilla; geometry and terrain support are new.',
                             'Forest support and full footprint regeneration required before integration.'])
    (out/'author-report.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='instances'},indent=2))


if __name__=='__main__': main()
