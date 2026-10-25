"""EV83 two-node shoreline pilot. Writes only inside this pilot directory."""
from pathlib import Path
import hashlib, importlib.util, json, math, shutil
import numpy as np
from scipy.ndimage import distance_transform_edt
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(r'E:/DayZ-Baltic-Build')
B=ROOT/'v30-mixed-bank-incremental-fixed-20261010'
EV79=ROOT/'v30-narva-dry-bank-relief-20261010'
OUT=ROOT/'v30-wet-support-shore-pilot-20261010'
SRC=B/'candidate/terrain.npz'; ORIGINAL=EV79/'candidate/terrain.npz'
CONS=EV79/'constraints.npz'; PRIOR=ROOT/'v30-remaining-exact-dry-support-20261009/constraints.npz'
VALLEY=ROOT/'v30-valley-smoothing-20261008/candidate-a/masks.npz'
P_SRC=B/'candidate/plane.npy'; F_SRC=B/'candidate/visible-field.npy'
REPORT=B/'review-luna/report.json'; AUTHOR=B/'author.py'; CONSUMER=B/'review-luna/verify.py'
EXPECTED_B='f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0'
EXPECTED_EV79='dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c'
EXPECTED_CONS='ad0cffd5f26fc942e17fc959236494287650b1528b728a15f4b1100da72f319c'
EXPECTED_CONSUMER='b0d364de439c2ff0404394295cdeb0c660c4deee91d7a1b5063ca8c5c0e11a37'
TARGETS=[(1880,191),(1785,366)]  # (x,z)=(1146,1002),(2196,1572)
HEIGHT_TOL=1e-8; ANGLE_TOL=2e-8; CLASS_TOL=1e-4; MAX_SHIFT_M=1.0
TRIS=((0,1,3),(0,2,3)); CORNERS=((0,0),(0,1),(1,0),(1,1))

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_npz(p):
    with np.load(p,allow_pickle=False) as z: return {k:z[k] for k in z.files}
def json_default(x): return x.item() if isinstance(x,np.generic) else str(x)

def p_level(p): return max(.85,float(p)) if np.isfinite(p) else .85
def f_level(p,f,corner):
    if not np.isfinite(p): return .85
    x=float(f[corner])
    return x if np.isfinite(x) else None

def local_shore_bounds(r,c,h,P,F):
    """Intersect exact sign/topology and <=1m crossing motion over every incident face edge."""
    lo,hi=-np.inf,np.inf; crossings=[]; signs=[]; zero=[]
    v=(r,c)
    for cr in (r-1,r):
      for cc in (c-1,c):
        if not (0<=cr<2047 and 0<=cc<2047): continue
        pv=float(P[cr,cc]); levels={'P':[p_level(pv)]*4}
        fv=F[cr,cc]
        levels['F']=[f_level(pv,fv,k) for k in range(4)]
        verts=[(cr+dr,cc+dc) for dr,dc in CORNERS]
        for tri_i,tri in enumerate(TRIS):
          if v not in [verts[k] for k in tri]: continue
          edges=((tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0]))
          for surface,lv in levels.items():
            for ia,ib in edges:
              if lv[ia] is None or lv[ib] is None: continue
              va,vb=verts[ia],verts[ib]
              if v not in (va,vb): continue
              la,lb=float(lv[ia]),float(lv[ib])
              ha,hb=float(h[va]),float(h[vb]); d0,d1=ha-la,hb-lb
              k=0 if va==v else 1; dv=d0 if k==0 else d1; do=d1 if k==0 else d0
              meta={'surface':surface,'cell':[cr,cc],'triangle':tri_i,'edge':[list(va),list(vb)],
                    'target_endpoint':k,'target_clearance_before_m':dv,'other_clearance_before_m':do}
              if abs(dv)<=1e-12:
                lo=max(lo,0.0); hi=min(hi,0.0); zero.append(meta); continue
              # Strictly retain target endpoint sign. The final float32 check repeats it directly.
              sign_bound=-dv
              if dv>0: lo=max(lo,float(np.nextafter(sign_bound,np.inf)))
              else: hi=min(hi,float(np.nextafter(sign_bound,-np.inf)))
              if dv*do<0:
                length=6.0*math.sqrt((va[0]-vb[0])**2+(va[1]-vb[1])**2)
                t0=-d0/(d1-d0); dt=MAX_SHIFT_M/length
                ta=max(0.0,t0-dt); tb=min(1.0,t0+dt)
                def height_at_t(t):
                    if k==0:
                        if t>=1.0: return math.inf if d1<0 else -math.inf
                        return la-(t/(1.0-t))*d1
                    if t<=0.0: return math.inf if d0<0 else -math.inf
                    return lb-((1.0-t)/t)*d0
                hvals=(height_at_t(ta),height_at_t(tb))
                low_h=min(hvals); high_h=max(hvals)
                lo=max(lo,low_h-ha if k==0 else low_h-hb)
                hi=min(hi,high_h-ha if k==0 else high_h-hb)
                crossings.append({**meta,'t_before':t0,'edge_length_m':length,'t_bounds':[ta,tb],
                    'allowed_height_bounds_m':[low_h,high_h]})
              else:
                signs.append(meta)
    return (float(lo),float(hi)),{'crossings':crossings,'same_sign_edges':signs,'zero_endpoint_edges':zero}

def consumer_wet_faces(h,p,f):
    nominal=np.fmax(p,.85); visible=np.where(np.isfinite(p)[:,:,None],f,.85)
    hv=[h[dr:dr+2047,dc:dc+2047] for dr,dc in CORNERS]; out=[]
    for tri in TRIS:
        wet=np.zeros(p.shape,dtype=bool)
        for i in tri: wet|=(nominal>hv[i])|(visible[:,:,i]>hv[i])
        out.append(wet)
    return out

def contour_check(r,c,before,after,P,F):
    records=[]; maxmove=0.0; failures=[]
    for cr in (r-1,r):
      for cc in (c-1,c):
        if not (0<=cr<2047 and 0<=cc<2047): continue
        pv=float(P[cr,cc]); levels={'P':[p_level(pv)]*4}
        levels['F']=[f_level(pv,F[cr,cc],k) for k in range(4)]
        verts=[(cr+dr,cc+dc) for dr,dc in CORNERS]
        for tri_i,tri in enumerate(TRIS):
          if (r,c) not in [verts[k] for k in tri]: continue
          for surface,lv in levels.items():
            for ia,ib in ((tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])):
              va,vb=verts[ia],verts[ib]
              if (r,c) not in (va,vb) or lv[ia] is None or lv[ib] is None: continue
              la,lb=float(lv[ia]),float(lv[ib])
              d0=float(before[va])-la; d1=float(before[vb])-lb
              e0=float(after[va])-la; e1=float(after[vb])-lb
              s0=np.sign(d0); s1=np.sign(d1); q0=np.sign(e0); q1=np.sign(e1)
              if (s0,s1)!=(q0,q1): failures.append({'reason':'endpoint_sign_changed','surface':surface,'edge':[list(va),list(vb)],'cell':[cr,cc],'triangle':tri_i,'before':[d0,d1],'after':[e0,e1]})
              rec={'surface':surface,'edge':[list(va),list(vb)],'cell':[cr,cc],'triangle':tri_i,
                   'signs_before':[int(s0),int(s1)],'signs_after':[int(q0),int(q1)]}
              if d0*d1<0:
                t0=-d0/(d1-d0); t1=-e0/(e1-e0)
                shift=abs(t1-t0)*6*math.hypot(va[0]-vb[0],va[1]-vb[1]); maxmove=max(maxmove,shift)
                rec.update(t_before=t0,t_after=t1,crossing_shift_m=shift)
                if shift>MAX_SHIFT_M+1e-10: failures.append({'reason':'crossing_shift_gt_1m','surface':surface,'edge':[list(va),list(vb)],'cell':[cr,cc],'triangle':tri_i,'shift_m':shift})
              records.append(rec)
    return {'records':records,'max_crossing_shift_m':maxmove,'failures':failures}

def eligibility(r,c,source,cons,prior,valley):
    reasons={
      'cls0':int(source['cls'][r,c])==0,'source_water_false':not bool(source['water'][r,c]),
      'beach_false':not bool(source['beach'][r,c]),'reserve_false':not bool(source['reserve'][r,c]),
      'platform_false':not bool(source['platform'][r,c]),'wet_support_true':bool(cons['wet_support'][r,c]),
      'other_fixed_false':not bool(cons['other_fixed'][r,c]),'engineering_halo_false':not bool(cons['engineering_halo'][r,c]),
      'large_lake_banks_false':not bool(prior['large_lake_banks'][r,c]),
      'corridor24m_false':not bool(valley['corridor'][r,c]),'summit_false':not bool(valley['summits'][r,c])}
    return {'row':r,'col':c,'x_m':6*c,'z_m':12282-6*r,'checks':reasons,'eligible':all(reasons.values())}

def main():
    if sha(SRC)!=EXPECTED_B or sha(ORIGINAL)!=EXPECTED_EV79 or sha(CONS)!=EXPECTED_CONS or sha(CONSUMER)!=EXPECTED_CONSUMER:
        raise RuntimeError('Input identity guard failed')
    if (OUT/'candidate').exists() or (OUT/'authoring.json').exists(): raise RuntimeError('Refusing to overwrite pilot output')
    ev79=load_npz(ORIGINAL); b=load_npz(SRC); cons=load_npz(CONS); prior=load_npz(PRIOR); valley=load_npz(VALLEY)
    h0=b['heights'].astype(np.float64); original=ev79['heights'].astype(np.float64)
    P=np.load(P_SRC,mmap_mode='r'); F=np.load(F_SRC,mmap_mode='r')
    assert P.shape==(2047,2047) and F.shape==(2047,2047,4)
    spec=importlib.util.spec_from_file_location('ev82_author',AUTHOR); author=importlib.util.module_from_spec(spec); spec.loader.exec_module(author)
    report=json.loads(REPORT.read_text(encoding='utf-8'))
    p99_bank=float(report['angles']['stats']['bank']['source']['p99']); p99_interior=float(report['angles']['stats']['interior']['source']['p99'])
    cls=ev79['cls']; engineering=ev79['reserve'].astype(bool)|ev79['platform'].astype(bool)
    distance=distance_transform_edt(~np.isin(cls,(3,5,6)),sampling=6.0)
    water_floor=author.incident_water_floor(original,np.asarray(P),np.asarray(F))
    target_info=[]; shore={}; chosen=[]; decisions=[]
    original_interval=author.original_budget_interval
    for r,c in TARGETS:
        elig=eligibility(r,c,ev79,cons,prior,valley)
        if not elig['eligible']: raise RuntimeError(f'Ineligible target: {elig}')
        (slo,shi),shore_info=local_shore_bounds(r,c,h0,P,F)
        base_lo,base_hi=original_interval(original[r,c],h0[r,c],water_floor[r,c],2.0)
        # Exact pilot contract: cumulative EV79 budget, no rise from B, endpoint signs,
        # and each measured P/F crossing within one metre.
        lo=max(base_lo,slo); hi=min(base_hi,shi,0.0)
        if lo>hi+1e-10: raise RuntimeError(f'Empty shore/budget interval at {(r,c)}: {[lo,hi]}')
        shore[(r,c)]=(lo,hi); target_info.append({'eligibility':elig,'shore_interval_delta_m':[slo,shi],
          'EV79_budget_floor_interval_delta_m':[base_lo,base_hi],'solver_interval_delta_m':[lo,hi],
          'crossing_samples':len(shore_info['crossings']),'noncrossing_sign_samples':len(shore_info['same_sign_edges']),
          'zero_endpoint_samples':len(shore_info['zero_endpoint_edges']),'shore_geometry':shore_info})
    # Reuse the verified EV82 angular optimizer with its interval function intersected by
    # the independently derived shoreline interval and the no-rise condition.
    def pilot_interval(orig_h,current_h,floor,max_delta=2.0):
        lo0,hi0=original_interval(orig_h,current_h,floor,max_delta)
        # node mapping comes from the current solver call, set by the loop below
        lo_s,hi_s=current_shore['bounds']
        return max(lo0,lo_s),min(hi0,hi_s,0.0)
    author.original_budget_interval=pilot_interval
    try:
      for (r,c),info in zip(TARGETS,target_info):
        current_shore={'bounds':shore[(r,c)]}
        proposal,reason=author.solve_node(r,c,h0,original,h0,cls,cons['fixed'],cons['wet_support'],engineering,
            distance,water_floor,p99_bank,p99_interior,max_delta=2.0,decision_trace=decisions)
        if proposal is None: raise RuntimeError(f'Angular solver rejected focus {(r,c)}: {reason}')
        d=float(proposal)-float(h0[r,c])
        if d>1e-8 or d>shore[(r,c)][1]+1e-8 or d<shore[(r,c)][0]-1e-8:
            raise RuntimeError(f'Solver proposal outside pilot interval at {(r,c)}: delta={d}, interval={shore[(r,c)]}')
        chosen.append(float(np.float32(proposal)))
        info.update(proposed_height_m=float(proposal),accepted_float32_height_m=float(np.float32(proposal)),
            delta_from_B_m=float(np.float32(proposal))-float(h0[r,c]),solver_reason=reason)
    finally:
      author.original_budget_interval=original_interval
    h1=h0.copy()
    for (r,c),v in zip(TARGETS,chosen): h1[r,c]=np.float32(v)
    # Focus energy and 1D exact crossing invariants on final float32 values.
    p99_fails=[]
    for (r,c),info in zip(TARGETS,target_info):
        patch0=author.local_patch(h0,r,c).astype(np.float64,copy=True)
        patch1=author.local_patch(h1,r,c).astype(np.float64,copy=True)
        pairs0=author.norm_coeffs(patch0); pairs1=author.norm_coeffs(patch1)
        energy0=sum(author.hinge_deg(pairs0,ta,tb)**2 for _e,(ta,tb) in author.HINGES)
        energy1=sum(author.hinge_deg(pairs1,ta,tb)**2 for _e,(ta,tb) in author.HINGES)
        reduction=(energy0-energy1)/energy0 if energy0 else 0.0
        shore_result=contour_check(r,c,h0,h1,P,F)
        info.update(hinge_energy_before=energy0,hinge_energy_after=energy1,hinge_energy_reduction_fraction=reduction,
            contour_verification=shore_result)
        slope_rows=[]; hinge_rows=[]; local_sector={}; dry_domain_hits=0
        for tri_i in author.INCIDENT:
            slope0=author.face_slope_deg(pairs0[tri_i]); slope1=author.face_slope_deg(pairs1[tri_i])
            cap=max(35.0,slope0)
            slope_rows.append({'triangle':int(tri_i),'before_deg':float(slope0),'after_deg':float(slope1),'cap_deg':float(cap),
                'pass':bool(slope1<=cap+ANGLE_TOL)})
        for hi,(_edge,(ta,tb)) in enumerate(author.HINGES):
            a0=author.hinge_deg(pairs0,ta,tb); a1=author.hinge_deg(pairs1,ta,tb)
            sec=author.edge_sector(author.HINGES[hi][0],r,c)
            g=local_sector.setdefault(sec,{'before':[],'after':[]})
            g['before'].append(a0); g['after'].append(a1)
            verts=set(author.TRIANGLES[ta]+author.TRIANGLES[tb])
            ids=[(r+dr,c+dc) for dr,dc in verts]
            is_bank=all(cls[rr,cc]==0 and not cons['wet_support'][rr,cc] and not engineering[rr,cc] and distance[rr,cc]<=96.0+1e-9 for rr,cc in ids)
            is_interior=all(cls[rr,cc]==0 and not cons['wet_support'][rr,cc] and not engineering[rr,cc] and distance[rr,cc]>96.0+1e-9 for rr,cc in ids)
            if is_bank or is_interior: dry_domain_hits+=1
            hinge_rows.append({'hinge_index':hi,'before_deg':float(a0),'after_deg':float(a1),'sector':[int(sec[0]),int(sec[1])],
                'new_over30':bool(a0<=30.0+CLASS_TOL and a1>30.0+CLASS_TOL)})
        for sec,g in local_sector.items():
            g['max_before_deg']=float(max(g['before'])); g['max_after_deg']=float(max(g['after']))
            g['nonincrease']=bool(g['max_after_deg']<=g['max_before_deg']+CLASS_TOL)
        info['angular_verification']={'face_slopes':slope_rows,'hinges':hinge_rows,
            'local_sector_maxima':{f'{k[0]},{k[1]}':v for k,v in local_sector.items()},
            'no_new_over30':not any(x['new_over30'] for x in hinge_rows),
            'no_local_sector_max_increase':all(v['nonincrease'] for v in local_sector.values()),
            'affected_hinges_in_dry_bank_or_interior_domains':dry_domain_hits,
            'bank_interior_p99_and_counts_unchanged_by_zero_domain_intersections':dry_domain_hits==0}
        if float(h1[r,c])>float(h0[r,c]) or float(h0[r,c])-float(h1[r,c])<.1-1e-7: p99_fails.append(f'descent_gate:{r},{c}')
        if reduction<.01-1e-10: p99_fails.append(f'energy_gate:{r},{c}')
        if shore_result['failures']: p99_fails.append(f'water_contour_gate:{r},{c}')
    # Consumer's full-map wet-face predicate; unchanged masks imply unchanged topology/components.
    wet0=consumer_wet_faces(h0,np.asarray(P),np.asarray(F)); wet1=consumer_wet_faces(h1,np.asarray(P),np.asarray(F))
    wet_same=[bool(np.array_equal(a,b)) for a,b in zip(wet0,wet1)]
    changed=np.argwhere(h1!=h0)
    if changed.tolist()!=sorted([[r,c] for r,c in TARGETS]): raise RuntimeError(f'Unexpected changed vertex set: {changed[:20].tolist()}')
    cand_arrays={k:(h1.astype(b[k].dtype) if k=='heights' else b[k].copy()) for k in b}
    metadata_exact=all(np.array_equal(cand_arrays[k],b[k],equal_nan=True) for k in b if k!='heights')
    if any(not all(x['pass'] for x in t['angular_verification']['face_slopes']) or not t['angular_verification']['no_new_over30'] or not t['angular_verification']['no_local_sector_max_increase'] or not t['angular_verification']['bank_interior_p99_and_counts_unchanged_by_zero_domain_intersections'] for t in target_info):
        p99_fails.append('angular_sector_or_distribution_gate')
    if not all(wet_same) or not metadata_exact: p99_fails.append('global_metadata_or_wet_face_mismatch')
    if p99_fails: raise RuntimeError('Pilot hard gate failed; preserving no-candidate state: '+', '.join(p99_fails))
    # P99 bank/interior are unchanged because every changed node belongs to wet_support,
    # so no all-four-vertex dry bank/interior hinge can include it.
    if any(not x['checks']['wet_support_true'] or x['checks']['large_lake_banks_false'] is False for x in [i['eligibility'] for i in target_info]):
        raise RuntimeError('Unexpected support or lake mask at a focus')
    outdir=OUT/'candidate'; outdir.mkdir(parents=True,exist_ok=False)
    np.savez_compressed(outdir/'terrain.npz',**cand_arrays)
    shutil.copy2(P_SRC,outdir/'plane.npy'); shutil.copy2(F_SRC,outdir/'visible-field.npy')
    # True 1:1 section through the P crossing edge selected by first crossing record.
    profiles=[]
    for (r,c),info in zip(TARGETS,target_info):
        rec=next(x for x in info['shore_geometry']['crossings'] if x['surface']=='P')
        va,vb=[tuple(x) for x in rec['edge']]; target=(r,c); other=vb if va==target else va
        # Orient section from fixed water neighbor to mutable dry node.
        if h0[other]<h0[target]: start,end=other,target
        else: start,end=target,other
        dist_m=6*math.hypot(end[0]-start[0],end[1]-start[1]); xs=np.linspace(0,dist_m,101)
        hs0=np.linspace(h0[start],h0[end],101); hs1=np.linspace(h1[start],h1[end],101)
        cr,cc=rec['cell']; corners=[(cr,cc),(cr,cc+1),(cr+1,cc),(cr+1,cc+1)]
        ids=[corners.index(start),corners.index(end)]; level0=p_level(float(P[cr,cc]))
        f0=f_level(float(P[cr,cc]),F[cr,cc],ids[0]); f1=f_level(float(P[cr,cc]),F[cr,cc],ids[1])
        fig,ax=plt.subplots(figsize=(7,4.2))
        ax.plot(xs,hs0,label='EV82-B terreno',color='#596579',lw=2)
        ax.plot(xs,hs1,label='Piloto float32',color='#b34a4a',lw=2)
        ax.plot(xs,[level0]*len(xs),label='P nominal',color='#2d83ba',ls='--')
        if f0 is not None and f1 is not None: ax.plot(xs,np.linspace(f0,f1,len(xs)),label='F visible (por extremos de esta celda)',color='#37a57a',ls=':')
        ax.scatter([0,dist_m],[h1[start],h1[end]],color='#b34a4a',s=24,zorder=5)
        ax.set_title(f'EV83 sección local {6*c},{12282-6*r} m — offline, no captura DayZ')
        ax.set_xlabel('distancia sobre arista (m)'); ax.set_ylabel('altura (m)'); ax.set_aspect('equal',adjustable='box')
        ax.grid(True,alpha=.25); ax.legend(loc='best',fontsize=8); fig.tight_layout()
        png=OUT/f'profile-{6*c}-{12282-6*r}.png'; fig.savefig(png,dpi=150); plt.close(fig)
        profiles.append({'path':str(png),'edge_start':list(start),'edge_end':list(end),'edge_length_m':dist_m,
          'aspect_equal_1_to_1':True,'P_level':level0,'F_endpoint_levels':[f0,f1]})
    report_out={'status':'EV83_LOCAL_AUTHORING_PILOT_CANDIDATE_READY_FOR_INDEPENDENT_CONSUMER',
      'scope':'exactly two eligible dry vertices; no engine/package; all other terrain vertices and metadata equal B',
      'provenance':{'B_terrain_sha256':sha(SRC),'EV79_terrain_sha256':sha(ORIGINAL),'EV79_constraints_sha256':sha(CONS),
        'large_lake_prior_sha256':sha(PRIOR),'valley_masks_sha256':sha(VALLEY),'B_consumer_sha256':sha(CONSUMER),
        'B_author_sha256':sha(AUTHOR),'P_sha256':sha(P_SRC),'F_sha256':sha(F_SRC),
        'pilot_script_sha256':sha(Path(__file__)),
        'rule':'only wet_support is opened for these two nodes; explicit large_lake_banks false; exact endpoint signs and per-cell/per-triangle P/F edge shift <=1m'},
      'targets':target_info,'candidate':{'terrain_path':str(outdir/'terrain.npz'),'terrain_sha256':sha(outdir/'terrain.npz'),
        'plane_path':str(outdir/'plane.npy'),'plane_sha256':sha(outdir/'plane.npy'),
        'visible_field_path':str(outdir/'visible-field.npy'),'visible_field_sha256':sha(outdir/'visible-field.npy'),
        'P_F_byte_identical_to_B':sha(outdir/'plane.npy')==sha(P_SRC) and sha(outdir/'visible-field.npy')==sha(F_SRC),
        'changed_vertices':changed.tolist(),'metadata_arrays_exact_B':metadata_exact,'native_wet_faces_exact_B':wet_same,
        'candidate_surface_area_ODOL_consumer_pending':True},
      'profiles':profiles,'limits':'No ODOL coverage/exposure or engine/render acceptance has run; root/reviewer consumer owns those gates.'}
    (OUT/'authoring-report.json').write_text(json.dumps(report_out,indent=2,ensure_ascii=False,default=json_default)+'\n',encoding='utf-8')
    lines=['# EV83: piloto local de orilla','','Propuesta única desde EV82-B; exactamente dos vértices bajan. OFFLINE, sin PBO ni motor.','']
    for t in target_info:
        lines += [f"- ({t['eligibility']['x_m']},{t['eligibility']['z_m']})m: {t['accepted_float32_height_m']:.8f}m ({t['delta_from_B_m']:.8f}m); cruce máximo {t['contour_verification']['max_crossing_shift_m']:.6f}m; energía incidente reducida {100*t['hinge_energy_reduction_fraction']:.3f}%; wet_support=true, large_lake_banks=false; water signs preserved."]
    lines += ['',f"Terrain SHA256 `{report_out['candidate']['terrain_sha256']}`; P `{report_out['candidate']['plane_sha256']}`; F `{report_out['candidate']['visible_field_sha256']}`; script `{report_out['provenance']['pilot_script_sha256']}`.",'',
      'La firma de agua está comprobada analíticamente en muestras P/F por celda y triángulo y con las máscaras consumidoras nativas completas. La cobertura ODOL compilada es pendiente del revisor; este candidato no afirma PASS de cobertura, render ni motor.','']
    (OUT/'authoring-report.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({'status':report_out['status'],'targets':[{'row':t['eligibility']['row'],'col':t['eligibility']['col'],'height':t['accepted_float32_height_m'],'delta':t['delta_from_B_m'],'energy_reduction':t['hinge_energy_reduction_fraction'],'max_shift':t['contour_verification']['max_crossing_shift_m']} for t in target_info],
      'candidate_sha256':report_out['candidate']['terrain_sha256'],'plane_sha256':report_out['candidate']['plane_sha256'],'visible_sha256':report_out['candidate']['visible_field_sha256']},indent=2))

if __name__=='__main__': main()
