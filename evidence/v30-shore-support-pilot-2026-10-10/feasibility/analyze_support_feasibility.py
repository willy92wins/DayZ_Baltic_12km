"""Local P/F contour-preserving DOF test for three EV82 profile vertices.

Offline and read-only with respect to terrain. Writes only this report folder.
"""
from pathlib import Path
import hashlib, json, importlib.util
import numpy as np
from scipy.optimize import linprog

R=Path(r'E:/DayZ-Baltic-Build')
EV79=R/'v30-narva-dry-bank-relief-20261010'
EV80=R/'v30-mixed-bank-constrained-20261010'
B=R/'v30-mixed-bank-incremental-fixed-20261010'
OUT=R/'v30-bank-support-feasibility-20261010'
SRC=EV79/'candidate/terrain.npz'; REF=EV80/'candidate/terrain.npz'; CAND=B/'candidate/terrain.npz'
CONS=EV79/'constraints.npz'
VALLEY_MASKS=R/'v30-valley-smoothing-20261008/candidate-a/masks.npz'
PFILE=B/'candidate/plane.npy'; FFILE=B/'candidate/visible-field.npy'
EXPECTED_B='f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0'
EXPECTED_EV80='0a18c5623885eed274cfe7d296e02aba290ed491b835d317213fc7876b2fc45b'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_npz(p):
    with np.load(p,allow_pickle=False) as z: return {k:z[k] for k in z.files}
assert sha(CAND)==EXPECTED_B and sha(REF)==EXPECTED_EV80
assert sha(CONS)=='ad0cffd5f26fc942e17fc959236494287650b1528b728a15f4b1100da72f319c'
assert sha(PFILE)==sha(EV79/'candidate/plane.npy')==sha(EV80/'candidate/plane.npy')
assert sha(FFILE)==sha(EV79/'candidate/visible-field.npy')==sha(EV80/'candidate/visible-field.npy')
spec=importlib.util.spec_from_file_location('ev82_author',B/'author.py')
author=importlib.util.module_from_spec(spec); spec.loader.exec_module(author)
source=load_npz(SRC); ev80=load_npz(REF); cand=load_npz(CAND); con=load_npz(CONS)
valley_masks=load_npz(VALLEY_MASKS)
h79=source['heights'].astype(np.float64); h80=ev80['heights'].astype(np.float64); hB=cand['heights'].astype(np.float64)
P=np.load(PFILE,mmap_mode='r').astype(np.float64); F=np.load(FFILE,mmap_mode='r').astype(np.float64)
assert P.shape==(2047,2047) and F.shape==(2047,2047,4) and hB.shape==(2048,2048)
assert np.array_equal(h79[con['fixed']],h80[con['fixed']])
authoring=json.loads((B/'authoring.json').read_text(encoding='utf-8'))
decisions={(int(q['row']),int(q['col'])):q for q in authoring['node_decisions']}

TRIS=((0,1,3),(0,2,3)); CORNERS=((0,0),(0,1),(1,0),(1,1))
TOL=1e-10

def water_levels(cell_r,cell_c,mode):
    p=float(P[cell_r,cell_c])
    # Mirror the consumer: nominal P is max(P, sea=.85), including the sea-only fallback.
    p_level=max(.85,p) if np.isfinite(p) else .85
    levels={'P':[p_level]*4}
    if mode in ('P+F','topology-only'):
        # F is replaced by sea only when P is absent; otherwise preserve each actual visible
        # corner independently (including NaN, which the consumer comparison ignores).
        vals=F[cell_r,cell_c] if np.isfinite(p) else np.full(4,.85)
        levels['F']=[float(x) if np.isfinite(x) else None for x in vals]
    return levels

def classify_edge(d0,d1):
    if abs(d0)<=TOL and abs(d1)<=TOL: return 'coincident'
    if abs(d0)<=TOL: return 'endpoint0'
    if abs(d1)<=TOL: return 'endpoint1'
    if d0*d1<0: return 'crossing'
    return 'dry' if d0>0 else 'wet'

def build_constraints(r0,c0,mode,lock_mask,lower_delta,upper_delta,h_patch):
    """7x7 patch; equality rows preserve crossings, inequalities preserve no-cross signs."""
    n=49; eq_rows=[]; eq_meta=[]; ub_rows=[]; ub_rhs=[]; ub_meta=[]
    surfaces=('P',) if mode=='P' else (('P','F') if mode=='P+F' else ('P','F'))
    exact=(mode!='topology-only')
    edge_seen=set(); surface_counts={s:{'crossing_edges':0,'no_cross_edges':0,'coincident_edges':0} for s in surfaces}
    def index(rc): return (rc[0]-r0)*7+(rc[1]-c0)
    def add_eq(row,meta): eq_rows.append(row); eq_meta.append(meta)
    def add_sign(v,d,surface,state,edge,cell,tri):
        row=np.zeros(n)
        if abs(d)<=TOL:
            row[index(v)]=1.0; add_eq(row,{'surface':surface,'state':'zero_endpoint_locked_for_topology',
                'edge':[list(edge[0]),list(edge[1])],'vertex':list(v),'cell':cell,'triangle':tri})
        elif d>0:
            row[index(v)]=-1.0; ub_rows.append(row); ub_rhs.append(float(d))
            ub_meta.append({'surface':surface,'state':'dry_endpoint_sign','vertex':list(v),'clearance_m':float(d)})
        else:
            row[index(v)]=1.0; ub_rows.append(row); ub_rhs.append(float(-d))
            ub_meta.append({'surface':surface,'state':'wet_endpoint_sign','vertex':list(v),'clearance_m':float(-d)})
    for cr in range(r0,r0+6):
      for cc in range(c0,c0+6):
        levels=water_levels(cr,cc,mode)
        verts=[(cr+dr,cc+dc) for dr,dc in CORNERS]
        for ti,tri in enumerate(TRIS):
          for a,b in ((tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])):
            va,vb=verts[a],verts[b]
            for surface in surfaces:
                if surface not in levels or levels[surface][a] is None or levels[surface][b] is None: continue
                la,lb=levels[surface][a],levels[surface][b]
                ha,hb=float(hB[va]),float(hB[vb]); d0,d1=ha-la,hb-lb
                state=classify_edge(d0,d1)
                # Identical edge/surface equations across adjacent triangles are deduplicated.
                key=(surface,tuple(sorted((va,vb))),round(la,9),round(lb,9))
                if va>vb: key=(surface,tuple(sorted((va,vb))),round(lb,9),round(la,9))
                if state in ('crossing','endpoint0','endpoint1','coincident') and exact:
                    if key in edge_seen: continue
                    edge_seen.add(key)
                    surface_counts[surface]['coincident_edges' if state=='coincident' else 'crossing_edges']+=1
                    if state=='coincident':
                        for v in (va,vb):
                            row=np.zeros(n); row[index(v)]=1.0
                            add_eq(row,{'surface':surface,'state':state,'edge':[list(va),list(vb)],'vertex':list(v)})
                    else:
                        t=0.0 if state=='endpoint0' else (1.0 if state=='endpoint1' else -d0/(d1-d0))
                        row=np.zeros(n); row[index(va)]=1.0-t; row[index(vb)]=t
                        add_eq(row,{'surface':surface,'state':state,'edge':[list(va),list(vb)],'t_from_first_vertex':float(t),'cell':[cr,cc],'triangle':ti})
                    if state=='coincident':
                        pass  # both endpoints were fixed to the surface above
                    else:
                        add_sign(va,d0,surface,state,(va,vb),[cr,cc],ti)
                        add_sign(vb,d1,surface,state,(va,vb),[cr,cc],ti)
                elif state in ('crossing','endpoint0','endpoint1','coincident'):
                    # Topology-only mode: no exact crossing equation, but every endpoint sign
                    # is retained; equality endpoints stay on the surface.
                    surface_counts[surface]['coincident_edges' if state=='coincident' else 'crossing_edges']+=1
                    add_sign(va,d0,surface,state,(va,vb),[cr,cc],ti)
                    add_sign(vb,d1,surface,state,(va,vb),[cr,cc],ti)
                elif state in ('dry','wet'):
                    surface_counts[surface]['no_cross_edges']+=1
                    # Keep both endpoint signs. This preserves vertex wet/dry topology,
                    # but deliberately does not preserve the exact contour location.
                    for v,d in ((va,d0),(vb,d1)):
                        row=np.zeros(n); row[index(v)]=1.0 if state=='wet' else -1.0
                        rhs=-d if state=='wet' else d
                        ub_rows.append(row); ub_rhs.append(rhs)
                        ub_meta.append({'surface':surface,'state':state,'vertex':list(v),'clearance_m':float(abs(d))})
                else:
                    if state=='coincident': surface_counts[surface]['coincident_edges']+=1
    # Lock the patch perimeter and all original fixed masks except wet_support.
    for ir in range(7):
      for ic in range(7):
        rr,cc=r0+ir,c0+ic
        if lock_mask[ir,ic]:
            row=np.zeros(n); row[ir*7+ic]=1.0
            add_eq(row,{'surface':'fixed','state':'locked','vertex':[rr,cc]})
    A=np.asarray(eq_rows,dtype=np.float64).reshape((-1,n)) if eq_rows else np.zeros((0,n))
    Aub=np.asarray(ub_rows,dtype=np.float64).reshape((-1,n)) if ub_rows else np.zeros((0,n))
    # Numerical rank on normalized nonzero equalities. Zero rows are harmless.
    nonzero=np.linalg.norm(A,axis=1)>1e-14 if len(A) else np.zeros(0,dtype=bool)
    An=A[nonzero]
    singular=np.linalg.svd(An,compute_uv=False) if len(An) else np.asarray([])
    threshold=(max(An.shape)*np.finfo(float).eps*singular[0]) if len(An) and singular[0] else 0.0
    rank=int(np.count_nonzero(singular>threshold)); nullity=n-rank
    return {'Aeq':A,'Aub':Aub,'bub':np.asarray(ub_rhs,dtype=np.float64),
      'eq_meta':eq_meta,'ub_meta':ub_meta,'surface_counts':surface_counts,
      'rank':rank,'nullity':nullity,'singular_values':singular.tolist(),'rank_tolerance':float(threshold),
      'nonzero_equality_rows':int(nonzero.sum())}

def surface_values_for_floor(rr,cc):
    vals=[]
    for cr in (rr-1,rr):
      for cc0 in (cc-1,cc):
        if not (0<=cr<2047 and 0<=cc0<2047): continue
        p=float(P[cr,cc0]); corner=(rr-cr)*2+(cc-cc0)
        # corner indices NW,NE,SW,SE => 0,1,2,3
        if np.isfinite(p):
            vals.append(max(.85,p))
            f=float(F[cr,cc0,corner])
            if np.isfinite(f): vals.append(f)
        else:
            vals.append(.85)
    return vals or [.85]

def patch_analysis(name,targets,center):
    r0,c0=center[0]-3,center[1]-3
    hpatch=hB[r0:r0+7,c0:c0+7]
    assert hpatch.shape==(7,7)
    lock=np.zeros((7,7),dtype=bool)
    for i in range(7):
      for j in range(7):
        rr,cc=r0+i,c0+j
        boundary=i in (0,6) or j in (0,6)
        wet=bool(con['wet_support'][rr,cc])
        other=bool(con['other_fixed'][rr,cc])
        eng=bool(con['engineering_halo'][rr,cc])
        fixed=bool(con['fixed'][rr,cc])
        lock[i,j]=boundary or other or eng or (fixed and not wet)
    bounds=[]
    floors=[]
    for i in range(7):
      for j in range(7):
        rr,cc=r0+i,c0+j; base=float(h79[rr,cc]); cur=float(hB[rr,cc])
        level=max(surface_values_for_floor(rr,cc))
        water_floor=min(base,level+1e-4)
        lower=max(base-2.0,water_floor,min(base,1.8)); upper=base+2.0
        floors.append({'row':rr,'col':cc,'water_floor_m':water_floor,'lower_m':lower,'upper_m':upper})
        bounds.append((lower-cur,upper-cur))
        # Any already submerged P/F corner keeps or increases its current clearance.
        for lv in surface_values_for_floor(rr,cc):
            if cur<lv-TOL:
                # delta <= 0 keeps depth from decreasing; actual class/water fixed nodes are locked above.
                row=np.zeros(49); row[i*7+j]=1.0
                # Append below after constraints are made; store patch-local clearance.
                bounds[-1]=(bounds[-1][0],min(bounds[-1][1],0.0))
    summaries={}
    for mode in ('P','P+F','topology-only'):
        q=build_constraints(r0,c0,mode,lock,bounds,None,hpatch)
        A,Aub,bub=q['Aeq'],q['Aub'],q['bub']
        fixed_zero=np.zeros(len(A),dtype=np.float64)
        # LP separately minimizes/maximizes each target; equations and sign inequalities are shared.
        per_target=[]
        for tr,tc in targets:
            idx=(tr-r0)*7+(tc-c0)
            if not (0<=idx<49): raise AssertionError('target not inside local patch')
            clearances=[float(level-hB[tr,tc]) for level in surface_values_for_floor(tr,tc)]
            node_floor=floors[idx]
            direct_crossings=[]
            for meta in q['eq_meta']:
                if meta.get('surface')!='P' or meta.get('state')!='crossing' or 'edge' not in meta:
                    continue
                ea,eb=(tuple(v) for v in meta['edge'])
                if (tr,tc) not in (ea,eb): continue
                other=eb if ea==(tr,tc) else ea
                t=float(meta['t_from_first_vertex'])
                target_coefficient=(1.0-t) if ea==(tr,tc) else t
                other_coefficient=t if ea==(tr,tc) else (1.0-t)
                orow,ocol=other
                direct_crossings.append({'edge':[list(ea),list(eb)],'cell':meta['cell'],'triangle':meta['triangle'],
                  't_from_first_vertex':t,'target_coefficient':target_coefficient,'neighbor_coefficient':other_coefficient,
                  'neighbor':[orow,ocol],'neighbor_locked_in_this_analysis':bool(lock[orow-r0,ocol-c0]),
                  'neighbor_height_B_m':float(hB[orow,ocol]),'neighbor_cls':int(source['cls'][orow,ocol]),
                  'neighbor_source_water':bool(source['water'][orow,ocol]),
                  'neighbor_other_fixed':bool(con['other_fixed'][orow,ocol]),
                  'neighbor_engineering_halo':bool(con['engineering_halo'][orow,ocol])})
            objective=np.zeros(49); objective[idx]=1.0
            def run(obj):
                return linprog(obj,A_ub=Aub if len(Aub) else None,b_ub=bub if len(Aub) else None,
                    A_eq=A if len(A) else None,b_eq=fixed_zero if len(A) else None,
                    bounds=bounds,method='highs')
            lores=run(objective); hires=run(-objective)
            def result(res):
                return {'success':bool(res.success),'status':int(res.status),'message':str(res.message),
                  'delta_m':float(res.x[idx]) if res.success else None,
                  'height_after_m':float(hB[tr,tc]+res.x[idx]) if res.success else None,
                  'full_delta_7x7':res.x.reshape(7,7).tolist() if res.success else None}
            per_target.append({'row':tr,'col':tc,'x_m':6*tc,'z_m':12282-6*tr,
              'height_B_m':float(hB[tr,tc]),'height_EV79_m':float(h79[tr,tc]),
              'incident_surface_clearance_m':clearances,
              'submerged_at_any_incident_sample':any(v>0 for v in clearances),
              'min_incident_clearance_m':min(clearances),'max_incident_clearance_m':max(clearances),
              'clearance_0_95_m_satisfied_at_all_incident_samples':all(v>=.95 for v in clearances),
              'navigable_corridor_24m_source_mask':bool(valley_masks['corridor'][tr,tc]),
              'calado_0_95_rule_applicable_here':bool(valley_masks['corridor'][tr,tc]),
              'EV79_height_floor_m':node_floor['lower_m'],'EV79_height_cap_m':node_floor['upper_m'],
              'allowed_delta_from_B_m':[bounds[idx][0],bounds[idx][1]],
              'direct_exact_P_crossings_to_neighbors':direct_crossings,
              'selector':(tr,tc) in decisions,'original_fixed':bool(con['fixed'][tr,tc]),
              'wet_support':bool(con['wet_support'][tr,tc]),'other_fixed':bool(con['other_fixed'][tr,tc]),
              'engineering_halo':bool(con['engineering_halo'][tr,tc]),
              'target_delta_range':{'min':result(lores),'max':result(hires)}})
        summaries[mode]={'constraint_kind':'exact P crossings + P sign topology' if mode=='P' else ('exact P and F crossings + sign topology' if mode=='P+F' else 'sign topology only; crossing locations and area not fixed'),
          'crossings_and_no_cross_edges_by_surface':q['surface_counts'],'equality_rank_in_49_deltas':q['rank'],
          'nullspace_dimension_before_inequality_bounds':q['nullity'],'equality_rows_nonzero':q['nonzero_equality_rows'],
          'inequality_count_no_cross_signs':len(q['Aub']),'singular_values':q['singular_values'],
          'target_results':per_target}
    patch_masks=[]
    for i in range(7):
      for j in range(7):
        rr,cc=r0+i,c0+j
        if con['wet_support'][rr,cc] and not con['other_fixed'][rr,cc] and not con['engineering_halo'][rr,cc] and i not in (0,6) and j not in (0,6):
            patch_masks.append({'row':rr,'col':cc,'x_m':6*cc,'z_m':12282-6*rr,'hB_m':float(hB[rr,cc]),
                'selector':(rr,cc) in decisions,'class':int(source['cls'][rr,cc]),'source_water':bool(source['water'][rr,cc]),
                'wet_support_relaxed_for_analysis':True})
    pwin=P[r0:r0+6,c0:c0+6]; fwin=F[r0:r0+6,c0:c0+6]
    finite=np.isfinite(pwin)[:,:,None]&np.isfinite(fwin)
    pdiff=np.abs(fwin-np.maximum(.85,np.where(np.isfinite(pwin),pwin,.85))[:,:,None])
    same_pf=int(np.count_nonzero(finite&(pdiff>1e-10)))==0
    return {'patch_name':name,'bounds_rows_cols':[r0,r0+6,c0,c0+6],
      'local_P_F_comparison':{'finite_P_cells':int(np.isfinite(pwin).sum()),
        'finite_F_corner_samples_with_finite_P':int(finite.sum()),'samples_F_not_equal_to_nominal_P_over_1e_10':int(np.count_nonzero(finite&(pdiff>1e-10))),
        'all_F_samples_equal_nominal_P':same_pf},
      'target_points':[{'row':r,'col':c,'x_m':6*c,'z_m':12282-6*r} for r,c in targets],
      'boundary_and_protection_lock_count':int(lock.sum()),'wet_support_only_nodes_unlocked_in_analysis':patch_masks,
      'ev79_bound_and_calado_method':'height delta bounded by author EV79 total ±2m and exact max(P,F,0.85)+1e-4 lower floor; for already submerged samples, δ<=0 so bed may deepen but not reduce current local water clearance. Other fixed and engineering halo remain zero; patch border zero.',
      'modes':summaries}

def fixtures():
    # Independent two-node edge algebra: h=(0,4); P=1 gives t=.25; F=3 gives t=.75.
    hp=np.array([0.0,4.0]); levels=(1.0,3.0)
    def t_at(level,h): return (level-h[0])/(h[1]-h[0])
    tp,tf=t_at(levels[0],hp),t_at(levels[1],hp)
    Ap=np.array([[1-tp,tp]]); Af=np.array([[1-tf,tf]])
    d=np.array([.1,-.3]); moved=hp+d
    p_after=t_at(levels[0],moved); f_after=t_at(levels[1],moved)
    rankp=int(np.linalg.matrix_rank(Ap)); rankpf=int(np.linalg.matrix_rank(np.vstack((Ap,Af))))
    # Current non-crossing edges must remain unconstrained by exact-contour rows.
    dry_h=np.array([2.0,4.0]); dry_levels=(1.0,.5); dry_d=np.array([-.1,-.1])
    wet_h=np.array([0.0,.5]); wet_levels=(1.0,1.5); wet_d=np.array([-.1,-.1])
    inverted_dry_delta=np.array([-1.2,0.0])
    def no_cross(h,lv,dv): return all((h[i]-lv[j])*(h[i]+dv[i]-lv[j])>=0 and (h[i+1]-lv[j])*(h[i+1]+dv[i+1]-lv[j])>=0 for i,j in ((0,0),(0,1)))
    out={'positive_single_P_crossing':{'h':[0,4],'P':1,'t_P_before':tp,'t_P_after_under_delta_0.1_-0.3':p_after,
       'equation':Ap[0].tolist(),'one_constraint_rank':rankp,'P_only_nullity':1,'movement_preserves_P':abs(tp-p_after)<1e-12},
      'negative_second_surface_pins_edge':{'F':3,'t_F_before':tf,'t_F_after_under_P_preserving_delta':f_after,
       'F_equation':Af[0].tolist(),'P_plus_F_rank':rankpf,'P_plus_F_nullity':2-rankpf,
       'movement_preserves_F':abs(tf-f_after)<1e-12,'combined_zero_motion_only':rankpf==2},
      'dry_no_cross_control':{'heights':dry_h.tolist(),'levels':list(dry_levels),'movement':dry_d.tolist(),
       'no_exact_crossing_equation_expected':all((dry_h[0]-lv)*(dry_h[1]-lv)>0 for lv in dry_levels),
       'movement_keeps_same_signs':all((dry_h[0]+dry_d[0]-lv)*(dry_h[1]+dry_d[1]-lv)>0 for lv in dry_levels)},
      'wet_no_cross_control':{'heights':wet_h.tolist(),'levels':list(wet_levels),'movement':wet_d.tolist(),
       'no_exact_crossing_equation_expected':all((wet_h[0]-lv)*(wet_h[1]-lv)>0 for lv in wet_levels),
       'movement_keeps_same_signs':all((wet_h[0]+wet_d[0]-lv)*(wet_h[1]+wet_d[1]-lv)>0 for lv in wet_levels)},
      'negative_sign_inversion_rejected':{'dry_heights':[2.0,4.0],'level':1.0,'proposed_delta':inverted_dry_delta.tolist(),
       'original_signs':[1,1],'new_signs':[int(np.sign(2.0+inverted_dry_delta[0]-1.0)),int(np.sign(4.0+inverted_dry_delta[1]-1.0))],
       'inequality_row':[-1.0,0.0],'rhs_m':1.0,'proposal_satisfies_sign_constraint':bool(-inverted_dry_delta[0]<=1.0)}}
    assert out['positive_single_P_crossing']['movement_preserves_P']
    assert out['negative_second_surface_pins_edge']['combined_zero_motion_only']
    assert out['dry_no_cross_control']['movement_keeps_same_signs'] and out['wet_no_cross_control']['movement_keeps_same_signs']
    assert not out['negative_sign_inversion_rejected']['proposal_satisfies_sign_constraint']
    return out

def main():
    # Three requested points, two <=7x7 patches (the Narva pair shares one patch).
    points=[(1880,191),(1786,366),(1785,366)]
    patchA=patch_analysis('pico_(1146,1002)',[points[0]],points[0])
    patchB=patch_analysis('escalones_(2196,1566_y_1572)',points[1:],(1785,366))
    result={'status':'LOCAL_PF_CONTOUR_FEASIBILITY_DIAGNOSTIC_ONLY',
      'provenance':{'EV79_terrain_sha256':sha(SRC),'EV80_terrain_sha256':sha(REF),'EV82B_terrain_sha256':sha(CAND),
        'constraints_sha256':sha(CONS),'valley_masks_sha256':sha(VALLEY_MASKS),'P_sha256':sha(PFILE),'F_sha256':sha(FFILE),
        'P_F_byte_identical_EV79_EV80_EV82B':True,'producer_script_sha256':sha(Path(__file__)),
        'consumer_verify_sha256':sha(B/'review-luna/verify.py')},
      'source_contract':{'triangulation':'native 6 m vertices; each cell split NW-NE-SE and NW-SW-SE',
        'P':'one nominal physical/sea surface per cell; consumer compares max(P,0.85), using 0.85 if P is NaN',
        'F':'visible four-corner surface in [NW,NE,SW,SE] order, raw per-corner values when P is finite; consumer falls back to 0.85 when P is NaN',
        'crossing_equation':'For current d_i=h_i-L_i and d_j=h_j-L_j with t=-d_i/(d_j-d_i), preserve the edge crossing exactly with (1-t)*delta_i+t*delta_j=0. End-point/equal-edge cases are handled explicitly.',
        'noncrossing':'same endpoint signs encoded as linear half-spaces; these preserve wet/dry vertex topology but do not freeze the contour point or wetted area.',
        'fixed':'patch boundary and EV79 `other_fixed`, `engineering_halo`, roads/platform and all fixed reasons other than wet_support are held at zero; wet_support is relaxed only for this feasibility test.',
        'bounds':'EV79 total ±2m and exact lower floor formula from author.py; analysis additionally requires delta<=0 at already submerged samples. This extra no-shallower condition is not an asserted universal 0.95m rule. Class!=0/water nodes remain locked.',
        'area_topology':'Exact crossings preserve exact local contour and area. Topology-only mode retains endpoint signs but does not impose equal contour parameter or area.'},
      'patches':[patchA,patchB],'synthetic_fixtures':fixtures(),
      'source_paths':{
        'consumer_wet_faces':'E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010/review-luna/verify.py:40-53',
        'consumer_fixed_formula':'E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010/review-luna/verify.py:127-141',
        'consumer_lower_floor':'E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010/review-luna/verify.py:159-165',
        'source_24m_corridor_mask':'E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008/candidate-a/masks.npz:corridor',
        'EV79_original_budget_and_water_floor':'E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010/author.py:372-378,388-401',
        'native_cell_planes':'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290/tools/terrain/v30_common.py:88-105',
        'independent_projection_F_triangle_contract':'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290/evidence/v30-water-cause-investigation-2026-10-10/projection/analyze_spatial.py:150-181'}}
    (OUT/'support-feasibility.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,
        default=lambda x: x.item() if isinstance(x,np.generic) else str(x))+'\n',encoding='utf-8')
    lines=['# Libertad local con soporte de agua EV82-B','','Diagnóstico local; no modifica terreno ni candidato. P y F están byte-idénticos entre EV79, EV80 y B.','',
      f"Hashes: terrain EV79 `{result['provenance']['EV79_terrain_sha256']}`, EV80 `{result['provenance']['EV80_terrain_sha256']}`, B `{result['provenance']['EV82B_terrain_sha256']}`; P `{result['provenance']['P_sha256']}`; F `{result['provenance']['F_sha256']}`; constraints `{result['provenance']['constraints_sha256']}`; valley masks `{result['provenance']['valley_masks_sha256']}`.",'',
      '## Contrato usado','',
      'La celda nativa se divide en NW–NE–SE y NW–SW–SE. P aporta un plano físico por celda; el consumidor usa el nivel nominal `max(P,0.85)` y 0.85 si falta P. F aporta alturas visibles raw por esquina en orden NW, NE, SW, SE cuando P existe; cuando no, el consumidor sustituye mar 0.85. Ambos se intersectan por triángulo. Para una arista que cruza la superficie L, se calcula `t=-d_i/(d_j-d_i)`, `d=h-L`; congelar el punto de cruce requiere `(1-t)δ_i+tδ_j=0`. Los segmentos sin cruce conservan signos mediante desigualdades: eso conserva la topología mojado/seco en los extremos, no el lugar del contorno ni el área mojada.','',
      'En cada parche 7×7 se fija el anillo exterior y todas las protecciones EV79 salvo `wet_support`, que se relaja solo en el análisis. Las cotas usan el presupuesto total EV79 ±2m y su suelo implementado `max(h79-2, min(h79, max incident P/F/0.85 + 1e-4), min(h79,1.8))`; los puntos ya sumergidos no pueden elevar su fondo (`δ<=0`) como condición conservadora adicional del análisis. El 0.95m se informa contra la geometría vigente; no se atribuye al EV79 como regla universal. Los nodos class!=0 y demás `other_fixed` siguen inmóviles.','']
    for patch in (patchA,patchB):
      lines += [f"## {patch['patch_name']} · filas {patch['bounds_rows_cols'][0]}–{patch['bounds_rows_cols'][1]}, columnas {patch['bounds_rows_cols'][2]}–{patch['bounds_rows_cols'][3]}",
        f"Nodos bloqueados incluyendo borde: {patch['boundary_and_protection_lock_count']}/49. wet_support-only interiores temporalmente variables: {len(patch['wet_support_only_nodes_unlocked_in_analysis'])}.",
        f"P/F locales: {patch['local_P_F_comparison']['finite_P_cells']} celdas con P; {patch['local_P_F_comparison']['finite_F_corner_samples_with_finite_P']} esquinas F válidas; diferencias F vs P nominal >1e-10: {patch['local_P_F_comparison']['samples_F_not_equal_to_nominal_P_over_1e_10']}. P+F no añade aquí ecuaciones independientes a P.",'']
      for mode,q in patch['modes'].items():
        lines += [f"### {mode}: {q['constraint_kind']}",
          f"Rango igualdad {q['equality_rank_in_49_deltas']}/49; nullidad antes de inecuaciones {q['nullspace_dimension_before_inequality_bounds']}; desigualdades no-cruce {q['inequality_count_no_cross_signs']}.",
          f"Cruces/no-cruces por superficie: `{json.dumps(q['crossings_and_no_cross_edges_by_surface'],ensure_ascii=False)}`.",'']
        for t in q['target_results']:
          mn=t['target_delta_range']['min']; mx=t['target_delta_range']['max']
          lines.append(f"- ({t['x_m']},{t['z_m']}) m, B={t['height_B_m']:.6f}m, selector={t['selector']}, fixed original={t['original_fixed']}, wet_support={t['wet_support']}, other_fixed={t['other_fixed']}: δ admisible [{mn['delta_m']},{mx['delta_m']}] m. Min LP `{mn['message']}`; max LP `{mx['message']}`. EV79 floor/cap=[{t['EV79_height_floor_m']:.6f},{t['EV79_height_cap_m']:.6f}]m, delta bounds desde B={t['allowed_delta_from_B_m']}m.")
          lines.append(f"  Clearances incidentales de superficie=[{', '.join(f'{v:.4f}' for v in t['incident_surface_clearance_m'])}]m; rango [{t['min_incident_clearance_m']:.4f},{t['max_incident_clearance_m']:.4f}]m; corredor navegable 24m={t['navigable_corridor_24m_source_mask']}; ≥0.95m en todas={t['clearance_0_95_m_satisfied_at_all_incident_samples']} (aplica aquí={t['calado_0_95_rule_applicable_here']}).")
          if t['direct_exact_P_crossings_to_neighbors']:
            for e in t['direct_exact_P_crossings_to_neighbors']:
              lines.append(f"  Ecuación P directa: arista {e['edge']} en celda/tri {e['cell']}/{e['triangle']}, t={e['t_from_first_vertex']:.6f}; coeficiente del objetivo={e['target_coefficient']:.6f}, vecino {e['neighbor']} coef={e['neighbor_coefficient']:.6f}, vecino locked={e['neighbor_locked_in_this_analysis']} (cls={e['neighbor_cls']}, water={e['neighbor_source_water']}, other_fixed={e['neighbor_other_fixed']}). Un vecino fijado hace δobjetivo=0 porque su coeficiente es distinto de cero.")
        lines.append('')
    lines += ['## Fixtures algebraicos independientes','',
      f"P-only: h=(0,4), P=1 da t={fixtures()['positive_single_P_crossing']['t_P_before']:.2f} y una sola ecuación/rango 1; δ=(+0.1,−0.3) conserva P. Al agregar F=3, t=0.75 da una fila independiente, rango 2 y solo movimiento cero. Controles de aristas completamente secas y completamente mojadas permiten una pequeña traslación sin inventar ecuación de cruce; las aserciones están en el JSON.",'',
      'El control negativo propone cruzar un extremo seco a mojado; la desigualdad `−δ<=h−L` lo rechaza. La topología por signos no equivale a conservar el parámetro del cruce ni el área mojada.','',
      '## Mecanismo local de inmovilidad','',
      'En los dos objetivos secos (1146,1002) y (2196,1572), una arista P cruza hacia un vecino fuente de agua/clase 6 que permanece `other_fixed`. El vecino tiene δ=0 y el coeficiente del objetivo en `(1−t)δ_i+tδ_j=0` es no nulo; por eso la igualdad exacta fuerza δobjetivo=0 directamente. En (2196,1566) el propio nodo es class!=0/source-water y `other_fixed`; además el floor EV82-B colapsa su intervalo inferior a la altura base y la condición conservadora de no hacer más somero limita el extremo superior a cero. La fuente `other_fixed` ya lo bloquea por sí sola. La profundidad geométrica allí es 0.3772m respecto a los planos incidentes, pero el source corridor 24m es false; por tanto el umbral de 0.95m para corredor navegable no aplica a ese punto y este diagnóstico no lo clasifica como incumplimiento. Los tres puntos tienen corridor=false.','',
      '## Lectura limitada','',
      'El resultado se restringe a tres puntos y dos ventanas. “Nullspace” es el del sistema de igualdades más bloqueos; los rangos LP incorporan después cotas, signos/topología y fondo sumergido. Igualdad exacta P+F no se debe confundir con conservar solo área/clasificación: esta última condición admite desplazar el cruce y variar el área. No se resolvió una optimización de área ni se produjo una superficie candidata.','',
      'Fuentes exactas: el contrato consumidor P/F está en `verify.py:40-76`; composición de protecciones en `verify.py:127-141`; floor en `verify.py:159-165`; presupuesto y water-floor en `author.py:372-401`; máscara del corredor navegable en `v30-valley-smoothing-20261008/candidate-a/masks.npz:corridor`; regla de plano físico en `v30_common.py:88-105`. La triangulación y F por triángulo están verificadas en `analyze_spatial.py:150-181`.','',
      'No se modificó P/F, terreno, constraints, máscaras, motor ni paquete; se escribieron solo estos dos informes y el script en la carpeta de diagnóstico.']
    (OUT/'support-feasibility.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    compact=[]
    for p in (patchA,patchB):
        mode_summary={}
        for k,v in p['modes'].items():
            mode_summary[k]={'rank':v['equality_rank_in_49_deltas'],
              'nullity':v['nullspace_dimension_before_inequality_bounds'],
              'targets':[{'xz':[t['x_m'],t['z_m']],
                'range':[t['target_delta_range']['min']['delta_m'],t['target_delta_range']['max']['delta_m']]}
                for t in v['target_results']]}
        compact.append({'name':p['patch_name'],'locks':p['boundary_and_protection_lock_count'],
          'wet_relaxed':len(p['wet_support_only_nodes_unlocked_in_analysis']),'modes':mode_summary})
    print(json.dumps({'status':result['status'],'fixtures':result['synthetic_fixtures'],'patches':compact},indent=2,
        default=lambda x: x.item() if isinstance(x,np.generic) else str(x)))

if __name__=='__main__': main()
