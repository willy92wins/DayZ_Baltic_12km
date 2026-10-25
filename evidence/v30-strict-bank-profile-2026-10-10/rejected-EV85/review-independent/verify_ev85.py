#!/usr/bin/env python
"""Independent EV85 39-node geometry and compiled-water coverage gate.

This verifier does not import EV83 authoring code. It reads EV79/B inputs,
P/F fields, serialized WRP transforms, and the actual compiled ODOL models.
"""
from __future__ import annotations
import argparse, hashlib, json, math, sys, time, traceback
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt
from shapely.geometry import Polygon
from shapely.ops import unary_union

ROOT = Path(r'E:/DayZ-Baltic-Build')
EV79 = ROOT / 'v30-narva-dry-bank-relief-20261010'
B = ROOT / 'v30-mixed-bank-incremental-fixed-20261010'
EV80 = ROOT / 'v30-mixed-bank-constrained-20261010'
PILOT = ROOT / 'v30-coupled-shore-pilot-20261010'
EV83 = ROOT / 'v30-wet-support-shore-pilot-20261010'
W = Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
MODEL_DIR = ROOT / 'v30-native-terminal-finish-20261009/package/water/temp/baltic_water_v30'
BOUNDS_JSON = ROOT / 'v30-low-water-components-20261009/compiled-instance-bounds.json'
SOURCE_SHA = 'dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c'
B_SHA = 'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0'
EV80_SHA = '0a18c5623885eed274cfe7d296e02aba290ed491b835d317213fc7876b2fc45b'
P_SHA = '768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0'
F_SHA = 'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c'
EV79_CONSTRAINTS_SHA = 'ad0cffd5f26fc942e17fc959236494287650b1528b728a15f4b1100da72f319c'
PRIOR_CONSTRAINTS_SHA = '18a3639907a68a8ceda37fe2a402884c2c4bc111fe8c7775d0a7d07dac02d370'
EV83_CANDIDATE_SHA = 'f0e977d8bc2e11529aedc3851bb1d456b45ffee0e2b974af89db6a26fab087f9'
B_STAGE_WPR_SHA = '3071395e2d1830f1c5c28bd84346761b5c517710e9d5f1f4ac19cd3fc1eff1f6'
B_DEPLOY_WORLD_SHA = 'b11c825b6c14ecc5649ac668b40c7dc6c9f52c64c26ddfa748983c04b340c36c'
B_DEPLOY_WATER_SHA = '3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14'
BOUNDS_WORLD_SHA = 'a845bee973c2db1c94acf39758358dfcfb5967770e3879263ecf1a1bc4f66fd2'
N, CELL, Z0 = 2048, 6.0, 12282.0
SEA, ANG_TOL, HEIGHT_TOL = 0.85, 1e-4, 1e-6
FOCI = ((1146, 1002), (2196, 1572)) # world (x,z) metres
FOCI_CR = tuple((int(x//CELL),int((Z0-z)//CELL)) for x,z in FOCI)
THIRD_WET=(2196,1566)
THIRD_WET_CR=(int((Z0-THIRD_WET[1])//CELL),int(THIRD_WET[0]//CELL))
PATCH_RADIUS = 3
EXPECTED_ELIGIBLE_COUNTS = (21,18)
EXPECTED_MUTABLE_NODES = (
    ((1878,189),(1878,190),(1878,191),(1878,192),(1878,193),
     (1879,189),(1879,190),(1879,191),(1879,192),(1879,193),
     (1880,189),(1880,190),(1880,191),(1880,192),(1880,193),
     (1881,189),(1881,190),(1881,191),(1882,189),(1882,190),(1882,193)),
    ((1783,364),(1783,365),(1783,366),(1783,367),(1783,368),
     (1784,364),(1784,365),(1784,366),(1784,367),(1784,368),
     (1785,364),(1785,365),(1785,366),(1785,367),
     (1787,365),(1787,366),(1787,367),(1787,368)),
)
TRIS = ((0, 1, 3), (0, 2, 3))      # NW,NE,SW,SE; split along NW-SE
CORNER_OFFSETS = ((0,0),(0,1),(1,0),(1,1))

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''): h.update(b)
    return h.hexdigest()

def load_npz(p):
    with np.load(p,allow_pickle=False) as z: return {k:z[k] for k in z.files}

def equal(a,b): return np.array_equal(a,b,equal_nan=True)

def signs_for(h, p, f):
    """Separate P and F sign arrays at their actual per-cell corner samples."""
    corners=[h[dr:dr+N-1,dc:dc+N-1] for dr,dc in CORNER_OFFSETS]
    out={}
    for name,levels in [('P',[p]*4),('F',[f[:,:,i] for i in range(4)]),('SEA',[np.full_like(p,SEA,dtype=np.float64)]*4)]:
        wet=[]
        for i,level in enumerate(levels):
            valid=np.isfinite(level)
            if name=='SEA': valid[:]=True
            wet.append(valid & (level>corners[i]))
        out[name]=wet
    return out

def native_face_masks(signs,f=None):
    result={}
    for name,s in signs.items():
        result[name]=[]
        for ti,tri in enumerate(TRIS):
            wet=np.logical_or.reduce([s[i] for i in tri])
            if name=='F': wet &= np.logical_and.reduce([np.isfinite(f[:,:,i]) for i in tri])
            result[name].append(wet)
    return result

def support_vertices(face_masks):
    out=np.zeros((N,N),dtype=bool)
    for masks in face_masks.values():
        for wet,tri in zip(masks,TRIS):
            for i in tri:
                dr,dc=CORNER_OFFSETS[i]
                out[dr:dr+N-1,dc:dc+N-1] |= wet
    return out

def local_component_frontier(face_masks,row,col,radius=3):
    r0,r1=max(0,row-radius),min(N-1,row+radius+1)
    c0,c1=max(0,col-radius),min(N-1,col+radius+1)
    result={}; offsets=((0,0),(0,1),(1,0),(1,1))
    for name,masks in face_masks.items():
        nodes=[]; owners=defaultdict(list)
        for ti,mask in enumerate(masks):
            for rr,cc in np.argwhere(mask[r0:r1,c0:c1]):
                rr=int(rr+r0);cc=int(cc+c0);node=(ti,rr,cc);nodes.append(node)
                vertices=[(rr+offsets[i][0],cc+offsets[i][1]) for i in TRIS[ti]]
                for a,b in ((0,1),(1,2),(2,0)):
                    owners[tuple(sorted((vertices[a],vertices[b])))].append(node)
        parent={n:n for n in nodes}
        def find(x):
            while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
            return x
        for group in owners.values():
            for n in group[1:]:
                a,b=find(group[0]),find(n)
                if a!=b:parent[b]=a
        result[name]={'window_cells':[r0,r1,c0,c1],'wet_triangles':len(nodes),
                      'components':len({find(n) for n in nodes}),
                      'frontier_edges':sum(len(v)==1 for v in owners.values())}
    return result

def cardinal_shape(h,row,col):
    center=float(h[row,col]);n={'north':float(h[row-1,col]),'south':float(h[row+1,col]),
                                 'west':float(h[row,col-1]),'east':float(h[row,col+1])}
    return {'center_m':center,'cardinal_neighbours_m':n,
            'strict_cardinal_maximum':center>max(n.values()),'strict_cardinal_minimum':center<min(n.values()),
            'east_west_curvature_m':2*center-n['east']-n['west'],
            'north_south_curvature_m':2*center-n['north']-n['south']}

def eligible_patches(b,cons,prior,h,p,f):
    """Reconstruct the EV85 interior domain from source semantics, not the optimizer."""
    patches=[]; mask=np.zeros((N,N),dtype=bool); details=[]
    for (x,z),(fc,fr),expected in zip(FOCI,FOCI_CR,EXPECTED_MUTABLE_NODES):
        nodes=[]
        for r in range(fr-PATCH_RADIUS+1,fr+PATCH_RADIUS):
            for c in range(fc-PATCH_RADIUS+1,fc+PATCH_RADIUS):
                levels=[SEA]
                for cr in (r-1,r):
                    for cc in (c-1,c):
                        pv=float(p[cr,cc])
                        if math.isfinite(pv): levels.append(max(pv,SEA))
                        k=(0 if r==cr else 2)+(0 if c==cc else 1)
                        fv=float(f[cr,cc,k])
                        if math.isfinite(fv): levels.append(fv)
                checks={
                    'dry_at_B_against_every_finite_incident_P_F_and_sea':all(float(h[r,c])>level for level in levels),
                    'class0':int(b['cls'][r,c])==0,
                    'other_fixed_false':not bool(cons['other_fixed'][r,c]),
                    'engineering_halo_false':not bool(cons['engineering_halo'][r,c]),
                    'large_lake_banks_false':not bool(prior['large_lake_banks'][r,c]),
                }
                details.append({'row':r,'col':c,'x_m':c*CELL,'z_m':Z0-r*CELL,
                                'wet_support_is_not_a_veto':bool(cons['wet_support'][r,c]),
                                'incident_water_levels_m':levels,'eligible':all(checks.values()),'checks':checks})
                if all(checks.values()): nodes.append((r,c));mask[r,c]=True
        nodes=tuple(sorted(nodes)); patches.append(nodes)
        assert len(nodes)==len(expected), f'EV85 eligible node count changed at focus {(x,z)}: {len(nodes)}'
        assert nodes==expected, f'EV85 eligible node identities changed at focus {(x,z)}'
        assert (fr,fc) in nodes, f'focus {(x,z)} is no longer eligible'
    return patches,mask,details

def canonical_touched_edges(nodes):
    edges=set(); node_set=set(nodes)
    for r,c in node_set:
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                if not (dr or dc): continue
                q=(r+dr,c+dc)
                if 0<=q[0]<N and 0<=q[1]<N:
                    edges.add(tuple(sorted(((r,c),q))))
    return tuple(sorted(edges))

def edge_order_violations(before,after,edges):
    bad=[]
    for (r0,c0),(r1,c1) in edges:
        d0=float(before[r0,c0])-float(before[r1,c1])
        d1=float(after[r0,c0])-float(after[r1,c1])
        if (d0>0 and d1<0) or (d0<0 and d1>0) or (d0==0 and d1!=0):
            bad.append({'edge':[[r0,c0],[r1,c1]],'before_delta_m':d0,'after_delta_m':d1})
    return bad

def axial_extrema(patch):
    """Weak axial extrema (ties with at least one strict side count as extrema)."""
    out=set(); n=patch.shape[0]
    for r in range(1,n-1):
        for c in range(1,n-1):
            v=patch[r,c]
            for axis,a,b in [('EW',patch[r,c-1],patch[r,c+1]),('NS',patch[r-1,c],patch[r+1,c])]:
                if v>=a and v>=b and (v>a or v>b):out.add((r,c,axis,'max'))
                if v<=a and v<=b and (v<a or v<b):out.add((r,c,axis,'min'))
    return out

def new_axial_extrema(before,after):
    old,new=axial_extrema(before),axial_extrema(after)
    return sorted(new-old),sorted(old),sorted(new)

def axial_extrema_window(h,row,col,radius=3):
    out=set()
    for r in range(row-radius,row+radius+1):
        for c in range(col-radius,col+radius+1):
            v=float(h[r,c])
            for axis,a,b in [('EW',float(h[r,c-1]),float(h[r,c+1])),('NS',float(h[r-1,c]),float(h[r+1,c]))]:
                if v>=a and v>=b and (v>a or v>b):out.add((r,c,axis,'max'))
                if v<=a and v<=b and (v<a or v<b):out.add((r,c,axis,'min'))
    return out

def new_axial_extrema_window(before,after,row,col,radius=3):
    old=axial_extrema_window(before,row,col,radius);new=axial_extrema_window(after,row,col,radius)
    return sorted(new-old),sorted(old),sorted(new)

def patch_profile(h,row,col):
    return {'row':row,'col':col,'center_x_m':col*CELL,'center_z_m':Z0-row*CELL,
            'x_profile_rows':[int(row)],'x_profile_x_m':[int((col+k)*CELL) for k in range(-3,4)],
            'x_profile_heights_m':[float(h[row,col+k]) for k in range(-3,4)],
            'z_profile_rows':[int(row+k) for k in range(-3,4)],
            'z_profile_z_m':[float(Z0-(row+k)*CELL) for k in range(-3,4)],
            'z_profile_heights_m':[float(h[row+k,col]) for k in range(-3,4)]}

def corner_values(h,r,c):
    return np.asarray([h[r,c],h[r,c+1],h[r+1,c],h[r+1,c+1]],dtype=np.float64)

def sign_topology(h,p,f):
    signs=signs_for(h,p,f)
    # Per-surface/per-corner checks preserve signs, not just unioned wet support.
    return signs,native_face_masks(signs,f)

def vertex_levels(p,f):
    """Per-vertex max water bound from every incident cell-corner sample."""
    out=np.full((N,N),SEA,dtype=np.float64)
    for i,(dr,dc) in enumerate(CORNER_OFFSETS):
        pv=np.nan_to_num(p.astype(np.float64),nan=SEA)
        fv=np.nan_to_num(f[:,:,i].astype(np.float64),nan=SEA)
        level=np.maximum(SEA,np.maximum(pv,fv))
        dst=out[dr:dr+N-1,dc:dc+N-1]
        np.maximum(dst,level,out=dst)
    return out

def triangle_normals(h):
    nw,ne,sw,se=h[:-1,:-1],h[:-1,1:],h[1:,:-1],h[1:,1:]
    one=np.ones_like(nw)
    a=np.cross(np.stack((6*one,ne-nw,np.zeros_like(nw)),axis=-1),np.stack((6*one,se-nw,-6*one),axis=-1))
    b=np.cross(np.stack((6*one,se-nw,-6*one),axis=-1),np.stack((np.zeros_like(nw),sw-nw,-6*one),axis=-1))
    a/=np.linalg.norm(a,axis=-1)[...,None]; b/=np.linalg.norm(b,axis=-1)[...,None]
    return a,b

def slopes(h):
    out=[]
    for n in triangle_normals(h): out.append(np.degrees(np.arctan2(np.hypot(n[...,0],n[...,2]),np.abs(n[...,1]))))
    return out

def edge_angles(h):
    a,b=triangle_normals(h)
    for k,x,y in [('diag',a,b),('vertical',a[:,:-1],b[:,1:]),('horizontal',b[:-1,:],a[1:,:])]:
        yield k,np.degrees(np.arctan2(np.linalg.norm(np.cross(x,y),axis=-1),np.einsum('ijk,ijk->ij',x,y)))

def edge_vertex_slices(mask,kind):
    if kind=='diag': return (mask[:-1,:-1],mask[:-1,1:],mask[1:,:-1],mask[1:,1:])
    if kind=='vertical': return (mask[:-1,:-2],mask[:-1,1:-1],mask[1:,1:-1],mask[1:,2:])
    return (mask[:-2,:-1],mask[1:-1,:-1],mask[1:-1,1:],mask[2:,1:])

def incident_any(changed,kind): return np.logical_or.reduce(edge_vertex_slices(changed,kind))

def summaries(parts):
    a=np.concatenate(parts) if parts else np.empty(0)
    if not len(a): return {'n':0,'p99':None,'max':None,'above30':0,'mean_square':None}
    return {'n':int(a.size),'p99':float(np.percentile(a,99)),'max':float(a.max()),
            'above30':int(np.count_nonzero(a>30.0)),'mean_square':float(np.mean(a*a))}

def clip_triangle(xyz, signed):
    return clip_polygon(xyz,signed)

def clip_polygon(xyz,signed):
    """Clip a convex XY polygon by an affine signed field >=0."""
    poly=[(np.asarray(xy,dtype=np.float64),float(d)) for xy,d in zip(xyz,signed)]
    out=[]
    for i,(a,da) in enumerate(poly):
        b,db=poly[(i+1)%len(poly)]
        ina=da>0.0; inb=db>0.0
        if ina: out.append(a)
        if ina!=inb:
            den=da-db
            if abs(den)>1e-15: out.append(a+(b-a)*(da/den))
    if len(out)<3:return Polygon()
    q=np.asarray(out); g=Polygon(q)
    return g if g.is_valid and g.area>1e-12 else g.buffer(0)

def cell_xy(r,c):
    return np.asarray([[c*CELL,Z0-r*CELL],[(c+1)*CELL,Z0-r*CELL],
                       [c*CELL,Z0-(r+1)*CELL],[(c+1)*CELL,Z0-(r+1)*CELL]],dtype=np.float64)

def designed_water(r,c,h,p,f,field):
    """Per-cell P or F footprint clipped against each native affine triangle."""
    xy=cell_xy(r,c); gh=corner_values(h,r,c); polys=[]
    if field=='P': levels=np.full(4,float(p[r,c])) if np.isfinite(p[r,c]) else None
    else: levels=np.asarray(f[r,c],dtype=np.float64)
    if levels is None:return Polygon()
    for tri in TRIS:
        ids=np.asarray(tri)
        if field=='F' and not np.isfinite(levels[ids]).all(): continue
        poly=clip_triangle(xy[ids],levels[ids]-gh[ids])
        if not poly.is_empty:polys.append(poly)
    return unary_union(polys) if polys else Polygon()

def area(poly): return 0.0 if poly.is_empty else float(poly.area)

def affine_coeff(xy,values):
    return np.linalg.solve(np.column_stack((xy[:,0],xy[:,1],np.ones(len(xy)))),np.asarray(values,dtype=np.float64))

def eval_affine(coeff,xy):return np.asarray(xy)@coeff[:2]+coeff[2]

def odol_visible_in_native_tri(face_xy,surface_coeff,cell_xy_values,cell_heights,tri):
    ids=np.asarray(tri); native_xy=cell_xy_values[ids]
    native_poly=Polygon(native_xy)
    overlap=Polygon(face_xy).intersection(native_poly)
    if overlap.is_empty:return Polygon()
    ground_coeff=affine_coeff(native_xy,cell_heights[ids])
    geoms=list(overlap.geoms) if hasattr(overlap,'geoms') else [overlap]
    pieces=[]
    for geom in geoms:
        if geom.is_empty or geom.area<=1e-12:continue
        ring=np.asarray(geom.exterior.coords[:-1],dtype=np.float64)
        signed=eval_affine(surface_coeff,ring)-eval_affine(ground_coeff,ring)
        clipped=clip_polygon(ring,signed)
        if not clipped.is_empty:
            piece=clipped.intersection(geom)
            if not piece.is_empty and piece.area>1e-12:pieces.append(piece)
    return unary_union(pieces) if pieces else Polygon()

def crossing_records(h,p,f,rs,cs):
    records=[]
    for r,c in zip(rs,cs):
        xy=cell_xy(int(r),int(c)); gh=corner_values(h,int(r),int(c))
        fields=[('P',np.full(4,float(p[r,c])) if np.isfinite(p[r,c]) else None),
                ('F',np.asarray(f[r,c],dtype=np.float64))]
        for tri in TRIS:
            ids=np.asarray(tri)
            for name,lev in fields:
                if lev is None:continue
                if name=='F' and not np.isfinite(lev[list(tri)]).all():continue
                for i,j in ((tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])):
                    d0=float(lev[i]-gh[i]);d1=float(lev[j]-gh[j])
                    if (d0>0)==(d1>0):continue
                    den=d0-d1
                    if abs(den)<1e-15:continue
                    t=float(d0/den)
                    records.append((name,int(r),int(c),tuple(sorted((i,j))),t,float(np.linalg.norm(xy[i]-xy[j]))))
    return records

def poly_check(old,new):
    return not ((old.area>0) != (new.area>0))

def verify_controls():
    # Positive and negative contracts use independent scalar/polygon/angle predicates.
    assert abs(crossing_shift(0.25,0.30))<=1.0
    assert abs(crossing_shift(0.25,0.45))>1.0
    assert same_signs([1,-1],[1,1]) is False
    assert new_over30(30.0,30.01) is True
    target=Polygon([(0,0),(2,0),(2,2),(0,2)])
    good=Polygon([(0,0),(2,0),(2,2),(0,2)])
    hole=Polygon([(0,0),(1,0),(1,2),(0,2)])
    assert coverage_uncovered(target,good)<=0.002
    assert coverage_uncovered(target,hole)>0.002
    giant=Polygon([(-6,12270),(12,12270),(12,12288),(-6,12288)])
    cell=cell_xy(0,0); heights=np.asarray([0.0,0.0,0.0,6.0]); surface=np.asarray([3.0,3.0,3.0])
    surface_coeff=affine_coeff(np.asarray([[-6,12270],[12,12270],[12,12288]],dtype=np.float64),surface)
    visible=unary_union([odol_visible_in_native_tri(np.asarray(giant.exterior.coords[:-1]),surface_coeff,cell,heights,tri) for tri in TRIS])
    assert abs(visible.area-27.0)<1e-9
    # A fixed neighbor lexicographically before a mutable node must still be gated.
    before=np.zeros((3,3),dtype=np.float64);before[1,1]=2;before[0,1]=1;after=before.copy();after[1,1]=0.5
    edge=canonical_touched_edges(((1,1),));assert ((0,1),(1,1)) in edge
    assert edge_order_violations(before,after,edge)
    # A B plateau is equality-locked; moving one tied endpoint is rejected.
    plateau=np.zeros((3,3),dtype=np.float64);plateau[1,0]=1;plateau[1,1]=2;plateau[1,2]=2;plateau[0,1]=3;plateau[2,1]=0
    plateau_bad=plateau.copy();plateau_bad[1,2]=2.0001
    assert not edge_order_violations(plateau,plateau,canonical_touched_edges(((1,1),)))
    assert edge_order_violations(plateau,plateau_bad,canonical_touched_edges(((1,1),)))
    # Frozen EV83 is a real regression fixture: the second focus became a new E-W valley.
    old=load_npz(B/'candidate/terrain.npz');ev83=EV83/'candidate/terrain.npz'
    assert sha(ev83)==EV83_CANDIDATE_SHA,'EV83 negative fixture identity mismatch'
    old_h=old['heights'];bad_h=load_npz(ev83)['heights'];c,r=FOCI_CR[1]
    new_extrema,_,_=new_axial_extrema_window(old_h,bad_h,r,c)
    assert any(q[2]=='EW' and q[3]=='min' for q in new_extrema),'EV83 V fixture not detected'
    return {'crossing_le_1m_pass':True,'crossing_over_1m_fail':True,'sign_inversion_fail':True,
            'new_over30_fail':True,'coverage_hole_fail':True,'large_ODOL_face_native_split_area_27m2':True,
            'fixed_lexicographically_previous_neighbor_inversion_fail':True,
            'identity_plateau_pass_and_tie_break_fail':True,'EV83_new_EW_valley_negative_detected':True}

def crossing_shift(t0,t1):return CELL*abs(float(t1)-float(t0))
def same_signs(a,b):return np.array_equal(np.sign(a),np.sign(b))
def new_over30(before,after):return before<=30+ANG_TOL and after>30+ANG_TOL
def coverage_uncovered(designed,compiled):return area(designed.difference(compiled))

def load_wrp_api(path,workspace):
    sys.path.insert(0,str(workspace/'tools/terrain'))
    import wrp0wzd
    return wrp0wzd.read(path)

def compiled_objects(wrp_path,workspace,selected_cells,model_dir,bounds_path):
    sys.path.insert(0,str(workspace/'tools/water'))
    from engine_water_model import ODOL
    wrp=load_wrp_api(wrp_path,workspace)
    inv=json.loads(Path(bounds_path).read_text(encoding='utf-8'))
    assert inv['world_sha256']==BOUNDS_WORLD_SHA and inv['water_sha256']==B_DEPLOY_WATER_SHA
    bounds={int(o['id']):o['bounds'] for o in inv['objects']}
    water=[o for o in wrp['objects'] if 'baltic_water_v30' in o['name'].replace('\\','/').lower()]
    assert len(water)==18024 and len(bounds)==18024
    rmin=min(r for r,c in selected_cells);rmax=max(r for r,c in selected_cells)
    cmin=min(c for r,c in selected_cells);cmax=max(c for r,c in selected_cells)
    x0,x1=cmin*CELL,(cmax+1)*CELL;z1=Z0-rmin*CELL;z0=Z0-(rmax+1)*CELL
    chosen=[]
    for o in water:
        bb=bounds.get(int(o['id']))
        if bb is None:continue
        bx0,bz0,bx1,bz1=bb
        if bx1<x0 or bx0>x1 or bz1<z0 or bz0>z1:continue
        m=np.asarray(o['matrix'],dtype=np.float64)
        if not np.array_equal(m[:9].reshape(3,3),np.eye(3)):raise AssertionError('non-translation water transform')
        chosen.append((o,m,bounds[int(o['id'])]))
    models={}
    model_hashes={}
    for o,m,bb in chosen:
        name=o['name'].replace('\\','/').split('/')[-1]
        if name not in models:
            path=Path(model_dir)/name
            assert path.is_file(),f'missing compiled ODOL {path}'
            expected=inv.get('models',{}).get(name,{}).get('sha256')
            assert expected and sha(path)==expected,f'compiled model hash mismatch: {name}'
            model_hashes[name]=expected
            models[name]=ODOL.from_file(str(path))
    return wrp,chosen,models,model_hashes

def compiled_exposure(heights,selected_cells,wrp_path,workspace,model_dir,bounds_path):
    wrp,objects,models,model_hashes=compiled_objects(wrp_path,workspace,selected_cells,model_dir,bounds_path)
    sums={kind:{cell:[] for cell in selected_cells} for kind in ('physical','visible')}
    target={'physical':3e15,'visible':1}
    face_count={'physical':0,'visible':0}
    for o,m,_ in objects:
        model=models[o['name'].replace('\\','/').split('/')[-1]]
        tx,ty,tz=float(m[9]),float(m[10]),float(m[11])
        for kind,res in target.items():
            expected_resolution=float(np.float32(res))
            exact=[l for l in model.lods if l.resolution==expected_resolution]
            if len(exact)!=1:raise AssertionError(f'{kind} LOD identity missing/nonunique for {o["name"]}: expected float32 {expected_resolution}, choices={[x.resolution for x in model.lods]}')
            lod=exact[0]
            vertices=np.asarray([(v.x+tx,v.y+ty,v.z+tz) for v in lod.vertices],dtype=np.float64)
            for face in lod.faces:
                inds=face.vertex_indices
                if len(inds)!=3:raise AssertionError('non-triangle ODOL face')
                q=vertices[inds]; xy=q[:,[0,2]]
                if Polygon(xy).area<=1e-12:continue
                xmin,zmin=xy.min(axis=0);xmax,zmax=xy.max(axis=0)
                cr0=max(0,int(math.floor(xmin/CELL)));cr1=min(N-2,int(math.floor(np.nextafter(xmax,-math.inf)/CELL)))
                rr0=max(0,int(math.floor((Z0-zmax)/CELL)));rr1=min(N-2,int(math.floor(np.floor((Z0-zmin)/CELL))))
                for r in range(rr0,rr1+1):
                    for c in range(cr0,cr1+1):
                        if (r,c) not in sums[kind]:continue
                        xyc=cell_xy(r,c)
                        gh=corner_values(heights,r,c)
                        try: surface_coeff=affine_coeff(xy,q[:,1])
                        except np.linalg.LinAlgError:continue
                        for tri in TRIS:
                            clipped=odol_visible_in_native_tri(xy,surface_coeff,xyc,gh,tri)
                            if not clipped.is_empty:sums[kind][(r,c)].append(clipped)
                face_count[kind]+=1
    unioned={k:{cell:(unary_union(polys) if polys else Polygon()) for cell,polys in cells.items()} for k,cells in sums.items()}
    return unioned,{'objects':len(objects),'models':len(models),'model_hashes':model_hashes,
                    'faces_by_lod':face_count,'wrp_objects':len(wrp['objects'])}

def pbo_guard(deploy_path,wrp_path):
    d=json.loads(Path(deploy_path).read_text(encoding='utf-8'))
    addon=Path(d['mod'])/'Addons'
    sys.path.insert(0,str(W/'tools/playtest'))
    from attach_navmesh import read_pbo
    _,_,entries=read_pbo(addon/'narva_trial.pbo')
    actual_oprw=entries.get('baltic_trial.wrp',b'')
    oprw_sha=hashlib.sha256(actual_oprw).hexdigest()
    staged_sha=sha(wrp_path)
    return {'deploy_status':d.get('status'),'deployed_world_sha256':d.get('files',{}).get('narva_trial.pbo'),
            'deployed_water_sha256':d.get('files',{}).get('baltic_water_v30.pbo'),
            'expected_world_exact':sha(addon/'narva_trial.pbo')==B_DEPLOY_WORLD_SHA==d.get('files',{}).get('narva_trial.pbo'),
            'expected_water_exact':sha(addon/'baltic_water_v30.pbo')==B_DEPLOY_WATER_SHA==d.get('files',{}).get('baltic_water_v30.pbo'),
            'compiled_wrp_payload_sha256':d.get('compiled_wrp_sha256'),
            'deployed_oprw_entry_sha256':oprw_sha,
            'deployed_oprw_matches_manifest':oprw_sha==d.get('compiled_wrp_sha256'),
            'staged_wrp_sha256':staged_sha,
            'staged_source_wrp_identity_exact':staged_sha==B_STAGE_WPR_SHA,
            'source_and_compiled_payload_are_distinct_artifacts':staged_sha!=oprw_sha}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--candidate',type=Path,default=PILOT/'candidate/terrain.npz')
    ap.add_argument('--expected-candidate-sha')
    ap.add_argument('--source',type=Path,default=EV79/'candidate/terrain.npz')
    ap.add_argument('--source-constraints',type=Path,default=EV79/'constraints.npz')
    ap.add_argument('--prior-constraints',type=Path,default=ROOT/'v30-remaining-exact-dry-support-20261009/constraints.npz')
    ap.add_argument('--b-reference',type=Path,default=B/'candidate/terrain.npz')
    ap.add_argument('--plane',type=Path,default=EV79/'candidate/plane.npy')
    ap.add_argument('--visible-field',type=Path,default=EV79/'candidate/visible-field.npy')
    ap.add_argument('--wrp',type=Path,default=B/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp')
    ap.add_argument('--deploy',type=Path,default=B/'deploy.json')
    ap.add_argument('--bounds',type=Path,default=BOUNDS_JSON)
    ap.add_argument('--models',type=Path,default=MODEL_DIR)
    ap.add_argument('--workspace',type=Path,default=W)
    ap.add_argument('--report',type=Path,default=PILOT/'review-independent/ev85-review.json')
    ap.add_argument('--self-test',action='store_true')
    ap.add_argument('--diagnostic-vector',action='store_true',help='inspect a frozen rejected heights+delta vector; never classify it as a candidate')
    args=ap.parse_args(); start=time.time(); report={'status':'ERROR_EV85_REVIEW','verifier':'independent EV85 geometry/PF/compiled-ODOL coverage','inputs':{},'gates':{}}
    try:
        if args.self_test:
            report.update(status='PASS_EV85_VERIFIER_FIXTURES',fixtures=verify_controls())
        else:
            assert args.expected_candidate_sha and len(args.expected_candidate_sha)==64,'--expected-candidate-sha must pin the EV85 candidate'
            b_plane=B/'candidate/plane.npy';b_field=B/'candidate/visible-field.npy'
            paths=[args.candidate,args.source,args.source_constraints,args.prior_constraints,args.b_reference,args.plane,args.visible_field,b_plane,b_field,args.wrp,args.deploy,args.bounds]
            report['inputs']={str(p):sha(p) for p in paths}
            assert sha(args.source)==SOURCE_SHA,'EV79 source identity mismatch'
            assert sha(args.b_reference)==B_SHA,'EV82-B reference identity mismatch'
            assert sha(args.source_constraints)==EV79_CONSTRAINTS_SHA,'EV79 constraints identity mismatch'
            assert sha(args.prior_constraints)==PRIOR_CONSTRAINTS_SHA,'prior large-lake protection constraints identity mismatch'
            assert sha(args.plane)==P_SHA,'P field identity mismatch'
            assert sha(args.visible_field)==F_SHA,'F field identity mismatch'
            assert sha(b_plane)==P_SHA and sha(b_field)==F_SHA,'B P/F field identity mismatch'
            assert sha(args.candidate)==args.expected_candidate_sha,'candidate identity mismatch'
            assert sha(EV83/'candidate/terrain.npz')==EV83_CANDIDATE_SHA,'EV83 negative fixture identity mismatch'
            assert sha(args.wrp)==B_STAGE_WPR_SHA,'EV82-B staged WRP identity mismatch'
            source=load_npz(args.source); raw_cand=load_npz(args.candidate); base=load_npz(args.b_reference); cons=load_npz(args.source_constraints); prior=load_npz(args.prior_constraints)
            diagnostic_delta=None
            if args.diagnostic_vector:
                assert set(raw_cand)=={'heights','delta'},'rejected diagnostic must contain only heights and delta'
                diagnostic_delta=raw_cand['delta']
                assert diagnostic_delta.shape==(N,N) and diagnostic_delta.dtype==np.float64 and np.isfinite(diagnostic_delta).all(),'diagnostic delta must be finite float64 map'
                cand=dict(source);cand['heights']=raw_cand['heights']
            else:
                cand=raw_cand
            h0=source['heights'].astype(np.float64); hb=base['heights'].astype(np.float64); hc=cand['heights'].astype(np.float64)
            p=np.load(args.plane,allow_pickle=False).astype(np.float64); f=np.load(args.visible_field,allow_pickle=False).astype(np.float64)
            assert h0.shape==hb.shape==hc.shape==(N,N) and p.shape==(N-1,N-1) and f.shape==(N-1,N-1,4)
            assert source['heights'].dtype==base['heights'].dtype==cand['heights'].dtype==np.float32,'terrain heights must be read back as float32'
            if args.diagnostic_vector:
                assert np.array_equal(diagnostic_delta,hc-hb),'diagnostic delta does not equal quantized heights minus B'
            else:
                assert set(source)==set(cand) and all(equal(source[k],cand[k]) for k in source if k!='heights'),'candidate metadata changed'
            assert set(source)==set(base) and all(equal(source[k],base[k]) for k in source if k!='heights'),'EV82-B metadata differs from EV79'
            assert np.isfinite(h0).all() and np.isfinite(hb).all() and np.isfinite(hc).all(),'nonfinite terrain heights'
            patches,allowed,domain_detail=eligible_patches(base,cons,prior,hb,p,f)
            domain_nodes=tuple(sorted(node for patch in patches for node in patch))
            assert len(domain_nodes)==39 and len(set(domain_nodes))==39
            order_edges=canonical_touched_edges(domain_nodes)
            assert len(order_edges)==220,'EV85 complete 8-neighbor edge count changed'
            changed=hc!=hb
            delta_b=hc-hb; delta79=hc-h0
            lower=np.maximum.reduce((h0-2.0,np.minimum(h0,1.8),np.minimum(h0,vertex_levels(p,f)+1e-4)))
            upper=np.minimum(hb,h0+2.0)
            floor_margin=hc-lower; budget_margin=upper-hc
            gates={
                'all_terrain_metadata_exact':not args.diagnostic_vector,
                'diagnostic_metadata_not_supplied':bool(args.diagnostic_vector),
                'exact_39_node_two_patch_domain':True,
                'only_authorized_heights_changed':bool(np.all(~changed|allowed)),
                'both_focus_descend_at_least_0_1m':all(delta_b[r,c]<=-0.1 for c,r in FOCI_CR),
                'no_height_raise_vs_B':bool(np.all(delta_b<=0.0)),
                'cumulative_EV79_budget_and_B_cap_all_domain_nodes':bool(np.all(delta79[allowed]>=-2.0) and np.all(budget_margin[allowed]>=0.0)),
                'EV79_floor_and_water_protection_all_domain_nodes':bool(np.all(floor_margin[allowed]>=0.0)),
                'P_bytes_identity':sha(args.plane)==P_SHA,
                'F_bytes_identity':sha(args.visible_field)==F_SHA,
                'B_P_F_byte_identity':sha(b_plane)==P_SHA and sha(b_field)==F_SHA,
                'EV79_constraints_identity':sha(args.source_constraints)==EV79_CONSTRAINTS_SHA,
            }
            third=THIRD_WET_CR
            gates['third_wet_support_point_unchanged']=(not bool(allowed[third]) and not bool(changed[third]))
            focus_detail=[]
            for i,((x,z),(c,r)) in enumerate(zip(FOCI,FOCI_CR)):
                focus_detail.append({'row':r,'col':c,'x_m':x,'z_m':z,'eligible_nodes':len(patches[i]),
                    'wet_support_true_eligible_nodes':sum(bool(cons['wet_support'][rr,cc]) for rr,cc in patches[i]),
                    'candidate_delta_vs_B_m':float(delta_b[r,c]),'candidate_delta_vs_EV79_m':float(delta79[r,c]),
                    'focus_lower_margin_m':float(floor_margin[r,c]),'focus_upper_margin_m':float(budget_margin[r,c])})
            sb,mb=sign_topology(hb,p,f); sc,mc=sign_topology(hc,p,f)
            gates['P_F_SEA_corner_signs_unchanged']=all(np.array_equal(sb[k][i],sc[k][i]) for k in sb for i in range(4))
            gates['P_F_SEA_wet_face_masks_unchanged']=all(np.array_equal(mb[k][i],mc[k][i]) for k in mb for i in range(2))
            support_b=support_vertices(mb); support_c=support_vertices(mc)
            local_components=[]
            for c,r in FOCI_CR:
                q0=local_component_frontier(mb,r,c);q1=local_component_frontier(mc,r,c)
                local_components.append({'row':r,'col':c,'B':q0,'candidate':q1,'unchanged':q0==q1})
            gates['wet_support_and_local_components_frontiers_unchanged']=(np.array_equal(support_b,support_c)
                and all(x['unchanged'] for x in local_components))
            crossing_cells={(r+dr,c+dc) for r,c in domain_nodes for dr in (-1,0) for dc in (-1,0)
                            if 0<=r+dr<N-1 and 0<=c+dc<N-1}
            cross_rows=[r for r,c in sorted(crossing_cells)];cross_cols=[c for r,c in sorted(crossing_cells)]
            cross_b=crossing_records(hb,p,f,cross_rows,cross_cols)
            cross_c=crossing_records(hc,p,f,cross_rows,cross_cols)
            # compare by surface/cell/edge, including duplicate triangle appearances only once
            def cross_map(rows):return {(n,r,c,e):(t,length) for n,r,c,e,t,length in rows}
            cb,cc=cross_map(cross_b),cross_map(cross_c)
            cross_deltas=[abs(cb[k][0]-cc[k][0])*cb[k][1] for k in cb.keys() & cc.keys()]
            gates['crossing_topology_identical']=cb.keys()==cc.keys()
            gates['every_P_and_F_crossing_moves_at_most_1m']=bool(cross_deltas) and max(cross_deltas,default=0.0)<=1.0+1e-8
            order_bad=edge_order_violations(hb,hc,order_edges)
            gates['all_220_touched_8_neighbor_orders_preserved']=not order_bad
            axial_report=[]; new_axial=[]
            for c,r in FOCI_CR:
                added,old_extrema,new_extrema=new_axial_extrema_window(hb,hc,r,c)
                axial_report.append({'row':r,'col':c,'before_extrema':[list(x) for x in old_extrema],
                    'candidate_extrema':[list(x) for x in new_extrema],'new_extrema':[list(x) for x in added]})
                new_axial.extend({'focus':[r,c],'patch_extremum':list(x)} for x in added)
            gates['no_new_axial_minima_or_maxima_in_either_7x7_patch']=not new_axial
            # Angular gates against B, including whole-map distributions and incident sectors.
            slope_b, slope_c=slopes(hb),slopes(hc)
            slope_bad=sum(int(np.count_nonzero(y>np.maximum(x,35.0)+ANG_TOL)) for x,y in zip(slope_b,slope_c))
            gates['native_slopes_at_most_max35_or_B']=slope_bad==0
            angular_b=dict(edge_angles(hb)); angular_c=dict(edge_angles(hc)); new30=[]; changed_sector={}
            incident=changed
            for kind,a in angular_b.items():
                mask=incident_any(incident,kind); z=angular_c[kind]
                for r,c in np.argwhere((a<=30+ANG_TOL)&(z>30+ANG_TOL)):
                    new30.append({'kind':kind,'row':int(r),'col':int(c),'before_deg':float(a[r,c]),'after_deg':float(z[r,c])})
                for r,c in np.argwhere(mask):
                    sec=(int(r)//64,int(c)//64); rec=changed_sector.setdefault(sec,[[],[]]);rec[0].append(float(a[r,c]));rec[1].append(float(z[r,c]))
            gates['no_new_hinges_over30deg']=len(new30)==0
            sector_report=[]
            for (sr,sc0),(old,new) in sorted(changed_sector.items()):
                sector_report.append({'row':sr,'col':sc0,'before_max':max(old),'after_max':max(new),'no_max_regression':max(new)<=max(old)+ANG_TOL})
            gates['no_changed_sector_max_regression']=all(x['no_max_regression'] for x in sector_report)
            # Match the frozen EV82-B full-map bank/interior population exactly:
            # source cls0, not EV79 wet_support, not reserve/platform. Do not
            # substitute current P/F wet topology or extra water/beach masks.
            dry=(base['cls']==0)&~cons['wet_support'].astype(bool)&~base['reserve'].astype(bool)&~base['platform'].astype(bool)
            bank=dry&(distance_transform_edt(~np.isin(base['cls'],(3,5,6)),sampling=CELL)<=96.0+1e-9)
            dist_stats={}
            for name,mask in [('bank',bank),('interior',dry&~bank)]:
                oldp=[];newp=[]
                for k,a in angular_b.items():
                    # Hinges are counted only where all four incident vertices belong to this population.
                    vs=edge_vertex_slices(mask,k); full=np.logical_and.reduce(vs)
                    oldp.append(a[full]);newp.append(angular_c[k][full])
                s0,s1=summaries(oldp),summaries(newp)
                dist_stats[name]={'B':s0,'candidate':s1}
            gates['bank_p99_and_count_nonworse']=dist_stats['bank']['candidate']['p99']<=dist_stats['bank']['B']['p99']+ANG_TOL and dist_stats['bank']['candidate']['above30']<=dist_stats['bank']['B']['above30']
            gates['interior_p99_and_count_nonworse']=dist_stats['interior']['candidate']['p99']<=dist_stats['interior']['B']['p99']+ANG_TOL and dist_stats['interior']['candidate']['above30']<=dist_stats['interior']['B']['above30']
            incident_b=[];incident_c=[]
            for k,a in angular_b.items():
                m=incident_any(changed,k);incident_b.append(a[m]);incident_c.append(angular_c[k][m])
            eb=sum(float(a@a) for a in incident_b);ec=sum(float(a@a) for a in incident_c)
            global_reduction=0.0 if eb<=1e-18 else 1-ec/eb
            focus_energy=[]
            for c,r in FOCI_CR:
                # Exact hinges whose shared edge/diagonal contains the target vertex.
                vals=[]; hinge_counts={}
                for k,a in angular_b.items():
                    node=np.zeros((N,N),dtype=bool);node[r,c]=True
                    m=incident_any(node,k);hinge_counts[k]=int(m.sum())
                    vals.append((a[m],angular_c[k][m]))
                old=np.concatenate([x.ravel() for x,y in vals]);new=np.concatenate([y.ravel() for x,y in vals])
                reduction=1-float(new@new)/max(float(old@old),1e-18)
                focus_energy.append({'row':r,'col':c,'hinges':hinge_counts,'before_energy':float(old@old),'after_energy':float(new@new),'reduction':reduction,'max_before':float(old.max()),'max_after':float(new.max())})
            gates['exactly_12_unique_incident_hinges_per_focus']=all(sum(x['hinges'].values())==12 and set(x['hinges'].values())=={4} for x in focus_energy)
            gates['each_focus_incident_energy_reduction_ge_1pct']=all(x['reduction']>=0.01 for x in focus_energy)
            gates['changed_incident_angular_energy_reduced']=global_reduction>0
            # Use frozen B transforms and compiled ODOLs over both complete 7x7-vertex patches,
            # including cells whose vertices are all fixed/ineligible.
            cells=set()
            for (fc,fr) in FOCI_CR:
                for r in range(fr-PATCH_RADIUS,fr+PATCH_RADIUS):
                    for c in range(fc-PATCH_RADIUS,fc+PATCH_RADIUS):cells.add((r,c))
            cells={(r,c) for r,c in cells if 0<=r<N-1 and 0<=c<N-1}
            assert len(cells)==72,'EV85 exposure scope must include 36 native cells per patch'
            deploy_check=pbo_guard(args.deploy,args.wrp)
            assert deploy_check['expected_world_exact'] and deploy_check['expected_water_exact'] and deploy_check['deployed_oprw_matches_manifest'] and deploy_check['staged_source_wrp_identity_exact'],'deployed EV82-B PBO/OPRW/source-WRP identity changed'
            comp_b,meta_b=compiled_exposure(hb,cells,args.wrp,args.workspace,args.models,args.bounds)
            comp_c,meta_c=compiled_exposure(hc,cells,args.wrp,args.workspace,args.models,args.bounds)
            designed={name:{(r,c):designed_water(r,c,h,p,f,name) for r,c in cells} for name,h in [('B',hb),('candidate',hc)]}
            coverage={}; max_uncovered={}; no_field_gain=[];dry_face_gain=[]; outside_increase={}
            for typ in ('physical','visible'):
                des_p_c={cell:designed['candidate'][cell] for cell in cells}
                des_f_c={cell:designed['candidate'][cell] for cell in cells}
                # For physical P and visible F, keep comparisons explicitly independent.
                design_for={'physical':'P','visible':'F'}[typ]
                unc=[];unc_b=[];gains=[];losses=[];outside_gains=[];outside_losses=[];cell_rows=[]
                for cell in cells:
                    bpoly=comp_b[typ][cell]; cpoly=comp_c[typ][cell]
                    dpoly=designed_water(*cell,hc,p,f,design_for)
                    unc.append(coverage_uncovered(dpoly,cpoly))
                    old_design=designed_water(*cell,hb,p,f,design_for)
                    unc_b.append(coverage_uncovered(old_design,bpoly))
                    gain=area(cpoly.difference(bpoly));loss=area(bpoly.difference(cpoly));gains.append(gain);losses.append(loss)
                    old_out=bpoly.difference(old_design);new_out=cpoly.difference(dpoly)
                    outside_gain=area(new_out.difference(old_out));outside_loss=area(old_out.difference(new_out))
                    outside_gains.append(outside_gain);outside_losses.append(outside_loss)
                    cell_rows.append({'row':cell[0],'col':cell[1],'candidate_design_m2':area(dpoly),
                        'B_compiled_m2':area(bpoly),'candidate_compiled_m2':area(cpoly),
                        'B_design_uncovered_m2':unc_b[-1],'design_uncovered_m2':unc[-1],
                        'compiled_gain_m2':gain,'compiled_loss_m2':loss,
                        'B_outside_design_m2':area(old_out),'candidate_outside_design_m2':area(new_out),
                        'outside_design_growth_m2':outside_gain,'outside_design_loss_m2':outside_loss})
                    # all design fields absent in a cell => absolutely no newly exposed ODOL area
                    other='F' if design_for=='P' else 'P'
                    pfield=designed_water(*cell,hc,p,f,'P');ffield=designed_water(*cell,hc,p,f,'F')
                    if pfield.is_empty and ffield.is_empty and gain>1e-8:no_field_gain.append({'type':typ,'cell':cell,'gain_m2':gain})
                    # Native face that had no compiled exposure may not gain any in candidate.
                    tri_xy=cell_xy(*cell)
                    for ti,tri in enumerate(TRIS):
                        tri_poly=Polygon(tri_xy[list(tri)])
                        if bpoly.intersection(tri_poly).area<=1e-8 and cpoly.intersection(tri_poly).area>1e-8:
                            dry_face_gain.append({'type':typ,'cell':cell,'triangle':ti,'gain_m2':float(cpoly.intersection(tri_poly).area)})
                max_uncovered[typ]=max(unc,default=0.0)
                outside_increase[typ]=sum(outside_gains)
                coverage[typ]={'design_minus_compiled_m2':sum(unc),'max_cell_design_minus_compiled_m2':max_uncovered[typ],
                               'B_design_minus_compiled_m2':sum(unc_b),'max_cell_B_design_minus_compiled_m2':max(unc_b,default=0.0),
                               'compiled_gain_vs_B_m2':sum(gains),'compiled_loss_vs_B_m2':sum(losses),
                               'outside_design_growth_m2':sum(outside_gains),'outside_design_loss_m2':sum(outside_losses),'cells':cell_rows}
            gates['physical_P_design_coverage_le_0_002m2']=(max_uncovered['physical']<=0.002 and coverage['physical']['design_minus_compiled_m2']<=0.002
                and coverage['physical']['B_design_minus_compiled_m2']<=0.002)
            gates['visible_F_design_coverage_le_0_002m2']=(max_uncovered['visible']<=0.002 and coverage['visible']['design_minus_compiled_m2']<=0.002
                and coverage['visible']['B_design_minus_compiled_m2']<=0.002)
            gates['compiled_outside_design_increase_le_0_002m2']=all(v<=0.002 for v in outside_increase.values())
            gates['no_new_compiled_gain_without_P_or_F']=not no_field_gain
            gates['no_compiled_exposure_in_previously_dry_faces']=not dry_face_gain
            shape_report=[];profile_report=[]
            for c,r in FOCI_CR:
                before=cardinal_shape(hb,r,c);after=cardinal_shape(hc,r,c)
                shape_report.append({'row':r,'col':c,'x_m':c*CELL,'z_m':Z0-r*CELL,'B':before,'candidate':after,
                    'new_strict_cardinal_minimum':after['strict_cardinal_minimum'] and not before['strict_cardinal_minimum'],
                    'new_east_west_local_minimum':(after['center_m']<after['cardinal_neighbours_m']['east'] and
                        after['center_m']<after['cardinal_neighbours_m']['west'] and
                        not (before['center_m']<before['cardinal_neighbours_m']['east'] and
                             before['center_m']<before['cardinal_neighbours_m']['west']))})
            ev83h=load_npz(EV83/'candidate/terrain.npz')['heights']
            for c,r in FOCI_CR:
                profile_report.append({'B':patch_profile(hb,r,c),'EV83':patch_profile(ev83h,r,c),'candidate':patch_profile(hc,r,c)})
            review_status=('REJECTED_DIAGNOSTIC_REVIEW' if args.diagnostic_vector else ('PASS_EV85_REVIEW' if all(gates.values()) else 'FAIL_EV85_REVIEW'))
            report.update(status=review_status,artifact_class=('author-rejected diagnostic vector' if args.diagnostic_vector else 'candidate'),gates=gates,
                focus=focus_detail,eligible_node_counts=[len(x) for x in patches],authorized_node_count=len(domain_nodes),
                authorized_nodes=[list(x) for x in domain_nodes],eligibility_review=domain_detail,
                third_wet_support_point={'world_xz':list(THIRD_WET),'row_col':list(THIRD_WET_CR),'height_B_m':float(hb[THIRD_WET_CR]),'height_candidate_m':float(hc[THIRD_WET_CR])},
                changed_heights=int(changed.sum()),
                crossings={'B':len(cb),'candidate':len(cc),'max_displacement_m':max(cross_deltas,default=None),'cells':len(crossing_cells)},
                touched_8_neighbor_edges=len(order_edges),order_violations=order_bad,
                wet_face_topology_local=local_components,axial_extrema=axial_report,new_axial_extrema=new_axial,
                cardinal_morphology=shape_report,profiles_36m_1to1=profile_report,
                floor={'minimum_margin_over_domain_m':float(floor_margin[allowed].min()),
                       'minimum_budget_margin_over_domain_m':float(budget_margin[allowed].min()),
                       'focus_margins_m':[float(floor_margin[r,c]) for c,r in FOCI_CR]},
                angular={'new_over30':new30,'sectors':sector_report,'B_vs_candidate_distributions':dist_stats,
                         'changed_incident_energy_B':eb,'changed_incident_energy_candidate':ec,'reduction':global_reduction,'focus':focus_energy},
                compiled={'coverage':coverage,'outside_design_increase_m2':outside_increase,'no_field_gain':no_field_gain,
                          'previously_dry_face_gain':dry_face_gain,'B_inventory':meta_b,'candidate_inventory':meta_c,
                          'B_nonempty_cell_unions':{k:sum(not v.is_empty for v in x.values()) for k,x in comp_b.items()},
                          'candidate_nonempty_cell_unions':{k:sum(not v.is_empty for v in x.values()) for k,x in comp_c.items()},
                          'deployed_B_identity':deploy_check},fixtures=verify_controls(),
                limits=['Offline analysis only; no DayZ/render/material acceptance.',
                        'P and F are evaluated separately at their native cell-corner samples; F is not interpolated as a global vertex raster.',
                        'ODOL triangles are tested against translated 0WZD source transforms hash-linked to the staged/deployed OPRW; these are not engine readback transforms.',
                        'No package or deployment is produced by this verifier.'])
    except Exception as e:
        report.update(status='ERROR_EV85_REVIEW',error=repr(e),traceback=traceback.format_exc())
    report['runtime_seconds']=round(time.time()-start,3)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'gates':report.get('gates'),'error':report.get('error'),'report':str(args.report)},indent=2))
    if report['status'] not in ('PASS_EV85_VERIFIER_FIXTURES','PASS_EV85_REVIEW'):raise SystemExit(1)

if __name__=='__main__':main()
