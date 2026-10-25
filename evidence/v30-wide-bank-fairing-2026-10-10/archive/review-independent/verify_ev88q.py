#!/usr/bin/env python
"""Independent offline consumer for EV88-Q. Never imports pilot authoring code."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math, sys, traceback
from collections import defaultdict
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon, shape, box

ROOT = Path(r'E:/DayZ-Baltic-Build')
HERE = Path(__file__).resolve().parent
PLAN = HERE.parent / 'plan.md'
B_PATH = ROOT/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'
EV79_PATH = ROOT/'v30-narva-dry-bank-relief-20261010/candidate/terrain.npz'
P_PATH = ROOT/'v30-narva-dry-bank-relief-20261010/candidate/plane.npy'
F_PATH = ROOT/'v30-narva-dry-bank-relief-20261010/candidate/visible-field.npy'
CONS_PATH = ROOT/'v30-narva-dry-bank-relief-20261010/constraints.npz'
PRIOR_PATH = ROOT/'v30-remaining-exact-dry-support-20261009/constraints.npz'
CORRIDOR_PATH = ROOT/'v30-v11/06-evidence/corridors.geojson'
W = Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
DECISION_PATH = W/'evidence/v30-navigation-contract-2026-10-08/decision.json'
EV87 = ROOT/'v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py'
COVERAGE = ROOT/'v30-global-strict-bank-relief-20261010/review-independent/verify_coverage_contract.py'
MODEL_DIR = ROOT/'v30-native-terminal-finish-20261009/package/water/temp/baltic_water_v30'
BOUNDS = ROOT/'v30-low-water-components-20261009/compiled-instance-bounds.json'
B_DEPLOY = ROOT/'v30-mixed-bank-incremental-fixed-20261010/deploy.json'
B_WRP = ROOT/'v30-mixed-bank-incremental-fixed-20261010/package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
B_SHA = 'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0'
EV79_SHA = 'dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c'
P_SHA = '768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0'
F_SHA = 'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c'
CONS_SHA = 'ad0cffd5f26fc942e17fc959236494287650b1528b728a15f4b1100da72f319c'
PRIOR_SHA = '18a3639907a68a8ceda37fe2a402884c2c4bc111fe8c7775d0a7d07dac02d370'
CORRIDORS_SHA = '28866a8cf6ff57f2f825228046164ef939bc22bca9948eb96fe2463da46af343'
DECISION_SHA = 'd510af67cc4016a0ba7192aa01c070d314b9bc7e49b6256ca6ffaf64fc05b843'
DECISION = {'width_m':24.0, 'nominal_corridor_min_depth_m':0.95, 'high_navigable_bed_floor_m':1.0}
EV88_PREFLIGHT = ROOT/'v30-wide-bank-fairing-pilot-20261010/author/preflight'
EV88_CANDIDATE = ROOT/'v30-wide-bank-fairing-pilot-20261010/candidate-terrain.npz'
EV88_RECEIPT = ROOT/'v30-wide-bank-fairing-pilot-20261010/authoring.json'
EV87_SHA = '964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27'
CV_SHA = '214f0eddda08d84ce18c921fcdbE01298f608c9a5c19b7e5246bb9e71df5dc2b'.lower()
CV_HELPER_SHA = EV87_SHA
CV_POLICY_SHA = '6964ca97226512764720eb1a25f41ab65e191cfda318ea07ad39bb1f4c0b6463'
DEPENDENCIES = (W/'tools/water/engine_water_model.py',W/'tools/terrain/wrp0wzd.py',
  W/'tools/playtest/attach_navmesh.py',Path(r'C:/Users/guill/.claude/skills/dayz-p3d-debinarizer/scripts/odol_reader.py'))
NARVA_CENTER_XZ = (2417.1428225906,6889.8850822322)
NARVA_EXCLUSION_M = 620.0
ROW, COL = 840, 370
N, CELL, Z0 = 2048, 6.0, 12282.0
SEA, TAU_FLAT = 0.85, 0.024040603637695314
TRIS = ((0,1,3),(0,2,3))
OFFSETS = ((0,0),(0,1),(1,0),(1,1))
CORE = (ROW-6, ROW+7, COL-6, COL+7)
WINDOW = (ROW-8, ROW+9, COL-8, COL+9)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''): h.update(block)
    return h.hexdigest()


def load_npz(path):
    with np.load(path, allow_pickle=False) as z: return {k:z[k] for k in z.files}


def canonical_sha(value):
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def checked_sources():
    expected={B_PATH:B_SHA,EV79_PATH:EV79_SHA,P_PATH:P_SHA,F_PATH:F_SHA,
              CONS_PATH:CONS_SHA,PRIOR_PATH:PRIOR_SHA,CORRIDOR_PATH:CORRIDORS_SHA,
              DECISION_PATH:DECISION_SHA}
    actual={str(path):sha(path) for path in expected}
    bad={str(path):{'expected':want,'actual':actual[str(path)]} for path,want in expected.items() if actual[str(path)]!=want}
    if bad:raise AssertionError(f'EV88 pinned source identity mismatch: {bad}')
    decision=json.loads(DECISION_PATH.read_text(encoding='utf-8'))
    if decision.get('authority')!='Direct user reply in this chat' or decision.get('nominal_corridor_min_depth_m')!=.95 or decision.get('high_navigable_bed_floor_m')!=1.0 or decision.get('width_m')!=24.0:
        raise AssertionError('user navigation decision does not match .95m/1m/24m contract')
    geo=json.loads(CORRIDOR_PATH.read_text(encoding='utf-8'))
    if len(geo.get('features',[]))!=19:raise AssertionError('approved corridor geometry no longer has 19 features')
    b=load_npz(B_PATH);ev79=load_npz(EV79_PATH)
    p=np.load(P_PATH,allow_pickle=False);f=np.load(F_PATH,allow_pickle=False)
    con=load_npz(CONS_PATH);prior=load_npz(PRIOR_PATH)
    if b['heights'].shape!=(N,N) or ev79['heights'].shape!=(N,N) or p.shape!=(N-1,N-1) or f.shape!=(N-1,N-1,4):
        raise AssertionError('unexpected B/EV79/P/F array shape')
    if np.isinf(p).any() or np.isinf(f).any():raise AssertionError('P/F infinities are not an absence encoding')
    return {'hashes':actual,'decision':decision,'corridors':geo,'B':b,'EV79':ev79,'P':p,'F':f,
            'constraints':con,'prior':prior}


def verify_preflight(bundle):
    """Rebuild the frozen author preflight before looking at candidate values."""
    pre_path=EV88_PREFLIGHT/'preflight.json';domain_path=EV88_PREFLIGHT/'domain-diagnostic.json'
    stencils_path=EV88_PREFLIGHT/'frozen-stencils.json';cross_path=EV88_PREFLIGHT/'crossing-bounds.json'
    fixtures_path=EV88_PREFLIGHT/'fixtures.json';schema_path=EV88_PREFLIGHT/'receipt-schema.json'
    expected={
      str(PLAN):'50a94dac1a15580c6299426678399ca80caf49835ba98a79946ded688a8a47ad',
      str(pre_path):'2c1540007d858e0c57b4b823baefdf0d7cf7edbccccb210701fdf1a322b8da65',
      str(domain_path):'3b93e5a4d18854de40e3d50aa746d06a9f27d9bcc2a8c2a99a993a782ca4a924',
      str(stencils_path):'82fe0abdaf6c6b1fd2a6fce5c42b609f3c4c0a5051ff1f333bab46f4fba57c6d',
      str(cross_path):'db9fb25b8a2f513e6ae5f348d42636b2e76bb8c4598c5a604522d94833cf93e7',
      str(fixtures_path):'8b2825f2be392f063c3ecc270e1d8156987e7a6295128bd227256c5232e18804',
      str(schema_path):'54ab7ab43f63e8f1d368b90de6c262b5531ae2b36256f51f4f70feb07b4fc89f'}
    actual={p:sha(p) for p in expected}
    if actual!=expected:raise AssertionError(f'EV88 frozen preflight/plan identity mismatch: {actual}')
    pre=json.loads(pre_path.read_text(encoding='utf-8'))
    if pre.get('status')!='PREFLIGHT_READY_SOLVER_NOT_RUN' or pre.get('solver_invoked') is not False:
        raise AssertionError('preflight is not the pinned pre-solver state')
    domain=reconstruct_domain(bundle);cross=reconstruct_crossings(bundle,domain)
    checks={
      'mutable_count':len(domain['variables'])==pre['mutable_count']==98,
      'mutable_digest':domain['variables_sha256_le_i32']==pre['mutable_nodes_sha256_le_i32'],
      'stencil_count':len(domain['stencils'])==pre['frozen_stencils']==397,
      'stencil_digest':domain['stencil_sha256']==pre['stencil_sha256_canonical_json'],
      'collar_count':len(domain['collar_stencils'])==pre['collar_impact_stencils']==123,
      'collar_digest':domain['collar_stencil_sha256']==pre['collar_stencil_sha256_canonical_json'],
      'cross_count':len(cross['records'])==pre['crossing_records']==116,
      'cross_digest':cross['sha256']==pre['crossing_records_sha256'],
      'nearflat_tau':domain['nearflat_tau_m']==pre['near_flat_threshold_m']==TAU_FLAT,
      'no_partial_F':len(domain['partial_F_cells'])==pre['partial_F_cells_touching_window']==0,
    }
    if not all(checks.values()):raise AssertionError(f'independent EV88 preflight reconstruction mismatch: {checks}')
    return {'status':'PREFLIGHT_RECONSTRUCTED_EXACTLY','hashes':actual,'checks':checks,
      'domain':domain,'crossings':cross,'preflight':pre}


def candidate_clearance(hb,hh,p,f,changed_rc):
    """Diagnostic only: dry-margin movement against each real P/F sample and SEA."""
    rows=[];layer_stats={name:{'samples':0,'near_dry_B_lt_0_25m':0,'min_clearance_B_m':None,
      'min_clearance_H_m':None,'new_nonpositive_H':0,'max_clearance_loss_m':0.0} for name in ('P','F','SEA')}
    for r,c in changed_rc:
        samples={'SEA':[SEA]}
        for cr,cc,k in ((r,c,0),(r,c-1,1),(r-1,c,2),(r-1,c-1,3)):
            if cr<0 or cc<0 or cr>=p.shape[0] or cc>=p.shape[1]:continue
            pv=float(p[cr,cc])
            if math.isfinite(pv):samples.setdefault('P',[]).append(pv)
            fv=float(f[cr,cc,k])
            if math.isfinite(fv):samples.setdefault('F',[]).append(fv)
        per={}
        for name,levels in samples.items():
            vals=[(float(hb[r,c])-lev,float(hh[r,c])-lev) for lev in levels]
            bmin=min(x[0] for x in vals);hmin=min(x[1] for x in vals);loss=max(x[0]-x[1] for x in vals)
            s=layer_stats[name];s['samples']+=len(vals);s['near_dry_B_lt_0_25m']+=sum(0.0<=x[0]<0.25 for x in vals)
            s['min_clearance_B_m']=bmin if s['min_clearance_B_m'] is None else min(s['min_clearance_B_m'],bmin)
            s['min_clearance_H_m']=hmin if s['min_clearance_H_m'] is None else min(s['min_clearance_H_m'],hmin)
            s['new_nonpositive_H']+=sum(x[0]>0.0 and x[1]<=0.0 for x in vals)
            s['max_clearance_loss_m']=max(s['max_clearance_loss_m'],loss);per[name]={'min_B_m':bmin,'min_H_m':hmin,'max_loss_m':loss,'sample_count':len(vals)}
        rows.append({'row':int(r),'col':int(c),'B_m':float(hb[r,c]),'H_m':float(hh[r,c]),'delta_H_m':float(hh[r,c]-hb[r,c]),'layers':per})
    return {'purpose':'diagnostic only; no post-hoc dry-margin gate','changed_vertices':len(changed_rc),
            'by_layer':layer_stats,'examples':rows}


def topology_check(ev,hb,hh,p,f,cells):
    """Per-cell/corner sign and per-edge crossing checks over all changed support cells."""
    sign_bad=[];cross_rows=[];max_shift=0.0
    corner=((0,0),(0,1),(1,0),(1,1))
    for r,c in sorted(cells):
        for name,levels in (('P',[float(p[r,c])]*4),('F',[float(x) for x in f[r,c]]),('SEA',[SEA]*4)):
            for ti,tri in enumerate(TRIS):
                if name=='P' and not math.isfinite(levels[0]):continue
                if name=='F' and not all(math.isfinite(levels[i]) for i in tri):continue
                for i in tri:
                    rr,cc=r+corner[i][0],c+corner[i][1]
                    db=float(hb[rr,cc])-levels[i];dh=float(hh[rr,cc])-levels[i]
                    if (db>0)!=(dh>0) or (db==0)!=(dh==0):
                        sign_bad.append({'layer':name,'cell':[r,c],'triangle':ti,'corner':i,'B_signed_m':db,'H_signed_m':dh})
        # Compute only original edge crossings; their endpoint signs must remain strict and the shift <=1m.
        for tri in TRIS:
          for name,levels in (('P',[float(p[r,c])]*4 if math.isfinite(float(p[r,c])) else None),
                              ('F',[float(x) for x in f[r,c]]),('SEA',[SEA]*4)):
            if levels is None or (name=='F' and not all(math.isfinite(levels[i]) for i in tri)):continue
            for ia,ib in ((tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])):
                va=(r+corner[ia][0],c+corner[ia][1]);vb=(r+corner[ib][0],c+corner[ib][1])
                ga=float(hb[va]-levels[ia]);gb=float(hb[vb]-levels[ib])
                if ga*gb>=0:continue
                try:
                    t0,t1=baseline_oriented_crossings(levels[ia],hb[va],levels[ib],hb[vb],hh[va],hh[vb])
                except ValueError:
                    cross_rows.append({'layer':name,'cell':[r,c],'triangle':TRIS.index(tri),'edge':[list(va),list(vb)],'valid_H_crossing':False});continue
                length=CELL*(math.sqrt(2.0) if va[0]!=vb[0] and va[1]!=vb[1] else 1.0)
                shift=abs(t1-t0)*length;max_shift=max(max_shift,shift)
                cross_rows.append({'layer':name,'cell':[r,c],'triangle':TRIS.index(tri),'edge':[list(va),list(vb)],'t_B':t0,'t_H':t1,'shift_m':shift,'valid_H_crossing':True})
    return {'signs_preserved':not sign_bad,'sign_violations':sign_bad[:100],'sign_violation_count':len(sign_bad),
            'original_crossings_count':len(cross_rows),'crossings_valid_and_within_1m':all(x.get('valid_H_crossing',False) and x.get('shift_m',0)<=1.0+1e-9 for x in cross_rows),
            'max_crossing_shift_m':max_shift,'crossing_examples':cross_rows[:100]}


def local_sector_stats(ev,hb,hh,changed_rc):
    """Global slope/hinge contracts, with exact full-map baseline distributions."""
    slope_b=ev.slopes(hb);slope_h=ev.slopes(hh)
    slope_bad=sum(int(np.count_nonzero(y>np.maximum(x,35.0)+1e-4)) for x,y in zip(slope_b,slope_h))
    angles_b=dict(ev.edge_angles(hb));angles_h=dict(ev.edge_angles(hh))
    new30=[];new30_count=0;sector_set=set()
    changed=np.zeros(hb.shape,dtype=bool)
    for r,c in changed_rc:changed[r,c]=True
    for kind,bv in angles_b.items():
        hv=angles_h[kind]
        mask=ev.incident_any(changed,kind)
        rr,cc=np.nonzero(mask)
        sector_set.update((int(r)//64,int(c)//64) for r,c in zip(rr,cc))
        newly=(bv<=30.0+1e-4)&(hv>30.0+1e-4)
        rr2,cc2=np.nonzero(newly)
        new30_count+=len(rr2)
        new30.extend({'kind':kind,'row':int(r),'col':int(c),'B_deg':float(bv[r,c]),'H_deg':float(hv[r,c])} for r,c in zip(rr2[:100],cc2[:100]))
    sectors=[]
    for sr,sc in sorted(sector_set):
        r0,c0=sr*64,sc*64;r1=min(angles_b['diag'].shape[0],r0+64);c1=min(angles_b['diag'].shape[1],c0+64)
        bmax=max(float(np.max(v[r0:min(r1,v.shape[0]),c0:min(c1,v.shape[1])])) for v in angles_b.values())
        hmax=max(float(np.max(v[r0:min(r1,v.shape[0]),c0:min(c1,v.shape[1])])) for v in angles_h.values())
        sectors.append({'sector_rc64':[sr,sc],'B_max_deg':bmax,'H_max_deg':hmax,'nonworse':hmax<=bmax+1e-4})
    return {'slope_violation_count_global':slope_bad,'slopes_le_max35_or_B':slope_bad==0,
      'new_over30_count_touched':new30_count,
      'new_over30_examples_touched':new30[:100],'no_new_hinges_over_30_touched':new30_count==0,
      'affected_sector_count':len(sectors),'sectors':sectors,'affected_sector_max_nonworse':all(x['nonworse'] for x in sectors),
      'angles_b':angles_b,'angles_h':angles_h}


def p99_population_gate(ev,angles_b,angles_h,bundle):
    populations=ev._ev87_populations(bundle['B'],bundle['constraints'])
    result={}
    gates=[]
    for name,pop in populations.items():
        old=[];new=[]
        for kind in angles_b:
            mask=np.logical_and.reduce(ev.edge_vertex_slices(pop,kind))
            old.append(np.asarray(angles_b[kind][mask],dtype=np.float64))
            new.append(np.asarray(angles_h[kind][mask],dtype=np.float64))
        ov=np.concatenate(old);nv=np.concatenate(new);thr=ev._ev87_thresholds(ov)
        old_counts=[int(np.count_nonzero(ov<=thr['q0'])),int(np.count_nonzero(ov<=thr['q1']))]
        new_counts=[int(np.count_nonzero(nv<=thr['q0'])),int(np.count_nonzero(nv<=thr['q1']))]
        old_stats=ev.summaries(old);new_stats=ev.summaries(new)
        ok=(new_stats['p99']<=old_stats['p99']+1e-4 and new_stats['above30']<=old_stats['above30'] and
            all(n>=o for o,n in zip(old_counts,new_counts)))
        gates.append(ok)
        result[name]={'B':old_stats,'H':new_stats,'B_p99_brackets_deg':[thr['q0'],thr['q1']],
                      'B_bracket_counts':old_counts,'H_bracket_counts':new_counts,'nonworse':ok}
    return {'by_population':result,'pass':all(gates)}


def verify_authoring_receipt(receipt_path,candidate_path,preflight):
    expected_receipt_sha='cdb0b03fe5b4d041299fbaa3229e0d2d4645ef1991568c6c79776cc961627cbb'
    expected_candidate_sha='cce4cd0c2f71355c6d8a110804b52570644e496055ada9ef17d07b4cb60c455c'
    if sha(receipt_path)!=expected_receipt_sha:raise AssertionError('authoring receipt identity does not match the delivered EV88-Q run')
    if sha(candidate_path)!=expected_candidate_sha:raise AssertionError('candidate identity does not match the delivered EV88-Q run')
    rec=json.loads(Path(receipt_path).read_text(encoding='utf-8'))
    if rec.get('status')!='AUTHORED_PENDING_INDEPENDENT_CONSUMER' or rec.get('candidate_sha256')!=expected_candidate_sha:
        raise AssertionError('unexpected authoring receipt/candidate status or hash')
    if Path(rec.get('candidate_path','')).resolve()!=Path(candidate_path).resolve():raise AssertionError('receipt candidate path mismatch')
    solver=rec.get('solver',{})
    if not (solver.get('success') is True and solver.get('status')==1 and solver.get('method')=='scipy.optimize.lsq_linear/BVLS' and solver.get('scipy_version')=='1.18.1'):
        raise AssertionError(f'author solver receipt is not the planned successful BVLS call: {solver}')
    inpre=rec.get('input_sha256_pre_solver',{});inpost=rec.get('post_solver_input_sha256',{})
    if inpre!=inpost:raise AssertionError('authoring inputs changed during solve')
    wanted={'B':B_SHA,'EV79':EV79_SHA,'P':P_SHA,'F':F_SHA,'EV79_CONSTRAINTS':CONS_SHA,'PRIOR_CONSTRAINTS':PRIOR_SHA}
    if inpre!=wanted:raise AssertionError(f'authoring source hashes differ from frozen sources: {inpre}')
    if rec.get('plan_sha256_before')!=preflight['preflight']['plan_sha256'] or rec.get('plan_sha256_after')!=preflight['preflight']['plan_sha256']:
        raise AssertionError('plan SHA changed across solver')
    if rec.get('preflight_sha256')!=sha(EV88_PREFLIGHT/'preflight.json'):
        raise AssertionError('author receipt does not bind the exact frozen preflight')
    return rec


def coverage_and_compiled_gates(ev,cv,hb,hh,bundle,changed_rc,source_hashes):
    p=bundle['P'];f=bundle['F'];cells=ev._ev87_cells(changed_rc)
    unknown_masks,unknown_totals=cv.classify_unknown_f(hb,hh,f)
    scan_cells=cells|unknown_masks['changed_cells']
    bounds=cv.validate_bounds_inventory(B_WRP,BOUNDS,W)
    if not bounds['name_xz_rotation_bounds_exact']:raise AssertionError('compiled WRP water inventory differs from pinned bounds/names/XZ/rotation')
    exp_pair,support,meta,bad_pair,unknown_static=cv.exposed_pair_and_support(
      hb,hh,p,f,scan_cells,B_WRP,W,MODEL_DIR,BOUNDS,unknown_masks)
    pbo=ev.pbo_guard(B_DEPLOY,B_WRP)
    if not all(pbo[k] for k in ('expected_world_exact','expected_water_exact','deployed_oprw_matches_manifest',
       'staged_source_wrp_identity_exact','source_and_compiled_payload_are_distinct_artifacts')):
        raise AssertionError(f'compiled WRP/PBO identity guard failed: {pbo}')
    gates={};metrics={};designs={}
    changed_partial=int(unknown_totals.get('changed_partial',0))
    uncertain=int(unknown_static.get('with_contact_or_exposed_or_unproven_intersection',0))
    gates['no_changed_partial_F_triangles']=changed_partial==0
    gates['unknown_F_changed_faces_absent_or_buried_in_B_and_H']=uncertain==0
    for kind,field in (('physical','physical'),('visible','visible')):
        designB=cv.make_design(hb,p,f,cells,field);designH=cv.make_design(hh,p,f,cells,field)
        designs[kind]={'B':designB,'H':designH}
        holes={'B':[],'H':[]}
        for r,c in sorted(cells):
            support_poly=support[kind][(r,c)]
            if field=='visible':
                xy=cv.cell_xy(r,c);known=[]
                for tri in cv.TRIS:
                    if np.isfinite(f[r,c,np.asarray(tri,dtype=int)]).all():known.append(Polygon(xy[list(tri)]))
                from shapely.ops import unary_union
                domain=unary_union(known) if known else Polygon()
                dB=designB[(r,c)].intersection(domain);dH=designH[(r,c)].intersection(domain)
            else:dB=designB[(r,c)];dH=designH[(r,c)]
            holes['B'].append(float(dB.difference(support_poly).area));holes['H'].append(float(dH.difference(support_poly).area))
        holes_pass=cv.coverage_holes_pass(holes['B'],holes['H'])
        residualB=cv.design_and_residual(hb,p,f,cells,field,exp_pair['B'][kind],designB)
        residualH=cv.design_and_residual(hh,p,f,cells,field,exp_pair['candidate'][kind],designH)
        resid_pass=all(residualB[k]<=cv.AREA_LIMIT and residualH[k]<=cv.AREA_LIMIT for k in
          ('missing_outside_band_total_m2','missing_outside_band_max_cell_m2','growth_outside_band_total_m2','growth_outside_band_max_cell_m2'))
        bad_by_side={side:[x for x in violations if x['kind']==kind] for side,violations in bad_pair.items()}
        bad=[x for violations in bad_by_side.values() for x in violations]
        gates[f'{kind}_nominal_footprint_supported_le_1e_7m2']=holes_pass
        gates[f'{kind}_compiled_residual_outside_height_band_le_0_002m2']=resid_pass
        gates[f'{kind}_no_exposed_face_above_field_tolerance']=not bad
        metrics[kind]={'support_hole_total_m2':{'B':sum(holes['B']),'H':sum(holes['H'])},
          'support_hole_max_cell_m2':{'B':max(holes['B'],default=0.0),'H':max(holes['H'],default=0.0)},
          'exposure_residual_B':residualB,'exposure_residual_H':residualH,
          'height_violation_count':len(bad),'height_violation_count_by_side':{k:len(v) for k,v in bad_by_side.items()},
          'height_violation_examples':bad[:25]}
    gates['no_new_partial_or_unresolved_face_exposure']=changed_partial==0 and uncertain==0
    for model_name,digest in meta.get('model_hashes',{}).items():
        model_path=MODEL_DIR/model_name;actual=sha(model_path)
        if actual!=digest:raise AssertionError(f'compiled water model changed during ODOL scan: {model_name}')
        source_hashes[str(model_path)]=actual
    return {'gates':gates,'metrics':metrics,'unknown_F':unknown_totals,'unknown_face_intersections':unknown_static,
      'scanned_cells':len(scan_cells),'changed_support_cells':len(cells),'compiled':meta,'bounds_inventory':bounds,'pbo_guard':pbo}


def evaluate_candidate(candidate_path,receipt_path):
    consumer_path=Path(__file__).resolve();consumer_digest=sha(consumer_path)
    source_hashes={str(consumer_path):consumer_digest}
    bundle=checked_sources();source_hashes.update(bundle['hashes'])
    pre=verify_preflight(bundle);receipt=verify_authoring_receipt(receipt_path,candidate_path,pre)
    source_hashes.update(pre['hashes'])
    source_hashes[str(receipt_path)]=sha(receipt_path)
    source_hashes[str(candidate_path)]=sha(candidate_path)
    ev=import_file('ev88_frozen_ev87',EV87)
    cv=import_file('ev88_frozen_coverage_contract',COVERAGE);cv.ev=ev
    for path,want in ((EV87,EV87_SHA),(COVERAGE,CV_SHA),(Path(COVERAGE.parent/'../coverage-contract-proposal.md').resolve(),CV_POLICY_SHA)):
        got=sha(path);source_hashes[str(path)]=got
        if got!=want:raise AssertionError(f'frozen independent representation helper identity changed: {path} {got}')
    source_hashes[str(Path(COVERAGE.parent/'../coverage-contract-proposal.md').resolve())]=CV_POLICY_SHA
    if ev.HEIGHT_TOL>1e-6:raise AssertionError('unexpected inherited height tolerance')
    # Pin all B deployment inputs that connect this source surface to compiled ODOL and WRP.
    linked={B_DEPLOY:'3c98951f3488eef233d6972621648c84244f9e711c2ff419fd0b8013b427ec00',
      B_WRP:'3071395e2d1830f1c5c28bd84346761b5c517710e9d5f1f4ac19cd3fc1eff1f6',
      BOUNDS:'863e9539203e59fe77b9c7d4949da3a69b4991249941e15b887b60ff9e81ee62'}
    # The deployed PBOs are source-side artifacts; retain their exact paths and hashes.
    deploy=json.loads(B_DEPLOY.read_text(encoding='utf-8'));addon=Path(deploy['mod'])/'Addons'
    linked[addon/'narva_trial.pbo']='b11c825b6c14ecc5649ac668b40c7dc6c9f52c64c26ddfa748983c04b340c36c'
    linked[addon/'baltic_water_v30.pbo']='3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14'
    for path,want in linked.items():
        got=sha(path);source_hashes[str(path)]=got
        if got!=want:raise AssertionError(f'compiled representation source identity mismatch: {path}')
    for path in DEPENDENCIES:
        if not path.is_file():raise AssertionError(f'missing compiled representation code dependency: {path}')
        source_hashes[str(path)]=sha(path)
    b=np.asarray(bundle['B']['heights'],dtype=np.float64);ev79=np.asarray(bundle['EV79']['heights'],dtype=np.float64)
    can=load_npz(candidate_path);base=bundle['B']
    if set(can)!=set(base):raise AssertionError(f'candidate NPZ fields differ from B: {set(can)^set(base)}')
    hraw=np.asarray(can['heights']);h=np.asarray(hraw,dtype=np.float64)
    if h.shape!=(N,N) or hraw.dtype!=np.float32 or not np.isfinite(h).all():raise AssertionError('candidate heights must be finite float32 2048x2048')
    for key in set(base)-{'heights'}:
        if not np.array_equal(can[key],base[key],equal_nan=True):raise AssertionError(f'candidate altered non-height source field {key}')
    changed=np.asarray(hraw!=np.asarray(base['heights']),dtype=bool);changed_rc=[tuple(map(int,x)) for x in np.argwhere(changed)]
    domain=pre['domain'];cross=pre['crossings'];variables={tuple(map(int,x)) for x in domain['variables']}
    changed_outside=sorted(set(changed_rc)-variables)
    if changed_outside:raise AssertionError(f'changed vertices outside independently reconstructed mutable domain: {changed_outside[:20]}')
    # Nonmutable values, outer support, protected vertices and the frozen collar remain byte-exact B.
    mutable_mask=np.zeros((N,N),dtype=bool)
    for r,c in variables:mutable_mask[r,c]=True
    exact_nonmutable=bool(np.array_equal(hraw[~mutable_mask],np.asarray(base['heights'])[~mutable_mask],equal_nan=True))
    rr0,rr1,cc0,cc1=WINDOW;cr0,cr1,cc0c,cc1c=CORE
    collar_mask=np.ones((rr1-rr0,cc1-cc0),dtype=bool);collar_mask[cr0-rr0:cr1-rr0,cc0c-cc0:cc1c-cc0]=False
    collar_ok=bool(np.array_equal(hraw[rr0:rr1,cc0:cc1][collar_mask],np.asarray(base['heights'])[rr0:rr1,cc0:cc1][collar_mask]))
    lower=cross['lower'];upper=cross['upper'];candidate_core=h[cr0:cr1,cc0c:cc1c]
    bcore=b[cr0:cr1,cc0c:cc1c];e79core=ev79[cr0:cr1,cc0c:cc1c]
    var_core=np.zeros(candidate_core.shape,dtype=bool)
    for r,c in variables:var_core[r-cr0,c-cc0c]=True
    bounds_ok=bool(np.all(candidate_core[var_core]>=lower[var_core]-1e-7)&np.all(candidate_core[var_core]<=upper[var_core]+1e-7)&
      np.all(candidate_core[var_core]>=e79core[var_core]-2.0-1e-7)&np.all(candidate_core[var_core]<=e79core[var_core]+2.0+1e-7)&
      np.all(candidate_core[var_core]<=bcore[var_core]+0.50+1e-7))
    fixed_ok=exact_nonmutable and collar_ok
    topology=topology_check(ev,b,h,bundle['P'],bundle['F'],ev._ev87_cells(changed_rc))
    # Local objective/shape gates use the exact frozen B support, never reselect from H.
    stencils=domain['stencils'];energy_b,_=stencil_energy(b,stencils);energy_h,_=stencil_energy(h,stencils)
    collar_stencils=domain['collar_stencils'];collar_energy_b,_=stencil_energy(b,collar_stencils);collar_energy_h,_=stencil_energy(h,collar_stencils)
    fg=focus_gate(b,h)
    local_b=local_mesh_angles(b,(ROW,COL),radius=2);local_h=local_mesh_angles(h,(ROW,COL),radius=2)
    local_ang_ok=local_b['max_incident_hinge_deg']-local_h['max_incident_hinge_deg']>=2.0
    rp_b,cp_b=rowcol_peak_prominence(b,CORE);rp_h,cp_h=rowcol_peak_prominence(h,CORE)
    rowcol_ok=bool(np.all(rp_h<=rp_b+1e-9)&np.all(cp_h<=cp_b+1e-9))
    flat=new_flat_windows(b,h,CORE,TAU_FLAT)
    extrema=extrema_matching(b,h,CORE,1)
    local_mesh={}
    # All hinges touching the frozen two-node collar are compared, including those not incident to focus.
    tile_b=np.asarray(b[rr0:rr1,cc0:cc1],dtype=np.float64);tile_h=np.asarray(h[rr0:rr1,cc0:cc1],dtype=np.float64)
    collar_angles_b=dict(ev.edge_angles(tile_b));collar_angles_h=dict(ev.edge_angles(tile_h))
    collar_angles={}
    for kind in collar_angles_b:
        mask=ev.incident_any(collar_mask,kind)
        vb=collar_angles_b[kind][mask];vh=collar_angles_h[kind][mask]
        collar_angles[kind]={'count':int(vb.size),'B_max_deg':float(vb.max()) if vb.size else None,'H_max_deg':float(vh.max()) if vh.size else None,
          'nonworse':not vb.size or float(vh.max())<=float(vb.max())+1e-4}
    global_geom=local_sector_stats(ev,b,h,changed_rc)
    p99=p99_population_gate(ev,global_geom['angles_b'],global_geom['angles_h'],bundle)
    del global_geom['angles_b'];del global_geom['angles_h']
    corridor_b=corridor_depth_report(b,bundle['P'],bundle['corridors'],comparison=h);corridor_h=corridor_depth_report(h,bundle['P'],bundle['corridors'],comparison=b)
    bed_b=high_bed_floor_report(b,bundle['B']);bed_h=high_bed_floor_report(h,bundle['B'])
    clearance=candidate_clearance(b,h,bundle['P'],bundle['F'],changed_rc)
    # Read actual compiled physical/visible water faces for every native cell touched by changed heights.
    cv_result=coverage_and_compiled_gates(ev,cv,b,h,bundle,changed_rc,source_hashes)
    gates={
      'fixed_protected_outside_and_collar_exact_B':fixed_ok,
      'mutable_heights_within_EV79_B_and_physical_bounds':bounds_ok,
      'per_layer_native_signs_preserved':topology['signs_preserved'],
      'all_original_P_F_SEA_crossings_shift_le_1m':topology['crossings_valid_and_within_1m'],
      'focus_cardinal_prominence_reduced_at_least_25_percent':bool(fg['passed']),
      'focus_max_hinge_reduced_at_least_2deg':bool(local_ang_ok),
      'fixed_stencil_energy_reduced_at_least_25_percent':bool(energy_h<=0.75*energy_b),
      'collar_stencil_energy_nonworse':bool(collar_energy_h<=collar_energy_b+1e-12),
      'collar_hinge_maxima_nonworse':all(x['nonworse'] for x in collar_angles.values()),
      'no_new_nearflat_2x2_windows':len(flat)==0,
      'all_candidate_extrema_matched_one_to_one':bool(extrema['passed']),
      'row_and_column_peak_prominence_nonworse':rowcol_ok,
      'global_triangle_slopes_le_max35_or_B':global_geom['slopes_le_max35_or_B'],
      'no_new_touched_hinges_over_30_0001deg':global_geom['no_new_hinges_over_30_touched'],
      'affected_384m_sector_maxima_nonworse':global_geom['affected_sector_max_nonworse'],
      'bank_and_interior_p99_and_counts_nonworse':p99['pass'],
      'all_19_nominal_P_corridors_have_full_coverage_and_min_depth_0_95m':corridor_h['all_covered'] and corridor_h['meets_0_95_everywhere'],
      'high_navigable_bed_floor_1m':bed_h['high_bed_floor_1m_pass'],
    }
    gates.update(cv_result['gates'])
    all_pass=all(gates.values())
    # Rehash every consumed source and representation input after geometry/ODOL analysis.
    for path,digest in list(source_hashes.items()):
        if sha(path)!=digest:raise AssertionError(f'input changed during consumer run: {path}')
    if sha(candidate_path)!=receipt['candidate_sha256']:raise AssertionError('candidate changed during consumer run')
    if sha(receipt_path)!='cdb0b03fe5b4d041299fbaa3229e0d2d4645ef1991568c6c79776cc961627cbb':raise AssertionError('receipt changed during consumer run')
    report={'status':'PASS_EV88Q_OFFLINE_CONSUMER' if all_pass else 'FAIL_EV88Q_OFFLINE_CONSUMER',
      'gates':{k:bool(v) for k,v in gates.items()},'inputs':{**source_hashes,str(candidate_path):sha(candidate_path),str(receipt_path):sha(receipt_path),
        str(EV88_PREFLIGHT/'preflight.json'):sha(EV88_PREFLIGHT/'preflight.json')},
      'information':{'candidate_sha256':receipt['candidate_sha256'],'changed_vertex_count':len(changed_rc),
        'changed_vertices_rc':changed_rc,'mutable_vertex_count':len(variables),'protected_or_outer_exact_B':fixed_ok,
        'height_bounds':{'mutable_nodes':int(var_core.sum()),'lower_min_m':float(lower[var_core].min()),'upper_max_m':float(upper[var_core].max()),
          'max_bound_violation_m':float(max(np.max(lower[var_core]-candidate_core[var_core]),np.max(candidate_core[var_core]-upper[var_core]),0.0))},
        'stencil_energy':{'B':energy_b,'H':energy_h,'reduction_fraction':None if energy_b==0 else 1-energy_h/energy_b,
          'collar_B':collar_energy_b,'collar_H':collar_energy_h,'collar_records':len(collar_stencils)},
        'focus':fg,'focus_max_hinge_deg':{'B':local_b['max_incident_hinge_deg'],'H':local_h['max_incident_hinge_deg']},
        'row_prominence':{'B':rp_b.tolist(),'H':rp_h.tolist()},'column_prominence':{'B':cp_b.tolist(),'H':cp_h.tolist()},
        'new_flat_windows':flat,'extrema_matching':extrema,'collar_hinges':collar_angles,
        'topology':topology,'global_geometry':global_geom,'p99_population':p99,
        'corridor_nominal_geometry':{'B':corridor_b,'H':corridor_h},'high_bed_floor':{'B':bed_b,'H':bed_h},
        'dry_clearance_P_F_SEA_diagnostic':clearance,'compiled_representation':cv_result,
        'runtime_limit':'Offline source geometry/compiled ODOL only; no DayZ runtime, rendering, wave envelope, or visual acceptance.'}}
    return report


def reconstruct_domain(bundle):
    """Independent reconstruction of exact P/F/SEA dryness and semantic protections."""
    b=bundle['B'];e=bundle['EV79'];p=bundle['P'];f=bundle['F'];con=bundle['constraints'];prior=bundle['prior']
    r0,r1,c0,c1=WINDOW;cr0,cr1,cc0,cc1=CORE
    bh=np.asarray(b['heights'][r0:r1,c0:c1],dtype=np.float64)
    cls=np.asarray(b['cls'][r0:r1,c0:c1]);levels=np.full(bh.shape,SEA,dtype=np.float64)
    partial=set();
    for cell_r in range(r0-1,r1):
      for cell_c in range(c0-1,c1):
        if not (0<=cell_r<p.shape[0] and 0<=cell_c<p.shape[1]):continue
        fv=np.asarray(f[cell_r,cell_c],dtype=np.float64);finite=np.isfinite(fv)
        if 0<int(finite.sum())<4:partial.add((cell_r,cell_c))
        pv=float(p[cell_r,cell_c])
        for dr,dc,k in ((0,0,0),(0,1,1),(1,0,2),(1,1,3)):
            vr,vc=cell_r+dr,cell_c+dc
            if not (r0<=vr<r1 and c0<=vc<c1):continue
            ii,jj=vr-r0,vc-c0;samples=[SEA]
            if math.isfinite(pv):samples.append(pv)
            if finite[k]:samples.append(float(fv[k]))
            levels[ii,jj]=max(levels[ii,jj],max(samples))
    other=np.asarray(con['other_fixed'][r0:r1,c0:c1],dtype=bool)
    eng=np.asarray(con['engineering_halo'][r0:r1,c0:c1],dtype=bool)
    large=np.asarray(prior['large_lake_banks'][r0:r1,c0:c1],dtype=bool)
    reserve=np.asarray(b['reserve'][r0:r1,c0:c1],dtype=bool)
    platform=np.asarray(b['platform'][r0:r1,c0:c1],dtype=bool)
    wet=bh<=levels
    masks={'other_fixed':other,'engineering_halo':eng,'large_lake_banks':large,'reserve':reserve,
           'platform':platform,'class_nonzero':cls!=0,'actually_wet':wet}
    protected=np.logical_or.reduce(tuple(masks.values()))
    core_protected=protected[cr0-r0:cr1-r0,cc0-c0:cc1-c0]
    rr,cc=np.nonzero(~core_protected)
    variables=np.column_stack((rr+cr0,cc+cc0)).astype(np.int32)
    digest=hashlib.sha256(np.asarray(variables,dtype='<i4').tobytes()).hexdigest()
    ev79_local=np.asarray(e['heights'][cr0:cr1,cc0:cc1],dtype=np.float64)
    # Bounds reconstruct the frozen EV79 budget and the physical level floor, node by node.
    lev_core=levels[cr0-r0:cr1-r0,cc0-c0:cc1-c0]
    b_core=np.asarray(b['heights'][cr0:cr1,cc0:cc1],dtype=np.float64)
    lower=np.maximum(ev79_local-2.0,np.minimum(ev79_local,1.8))
    lower=np.maximum(lower,np.minimum(ev79_local,lev_core+1e-4))
    upper=np.minimum(ev79_local+2.0,b_core+0.50)
    records=stencil_records(variables=variables)
    collar={(r,c) for r in range(r0,r1) for c in range(c0,c1)
            if r<r0+2 or r>=r1-2 or c<c0+2 or c>=c1-2}
    collar_records=[x for x in records if x['collar']]
    tau_spans=np.maximum.reduce((bh[:-1,:-1],bh[1:,:-1],bh[:-1,1:],bh[1:,1:]))-np.minimum.reduce((bh[:-1,:-1],bh[1:,:-1],bh[:-1,1:],bh[1:,1:]))
    core_spans=tau_spans[cr0-r0:cr1-r0-1,cc0-c0:cc1-c0-1]
    tau=float(np.quantile(core_spans,.05,method='linear'))
    keyrows=[x['key'] for x in records];collarkeys=[x['key'] for x in collar_records]
    return {'bounds17':list(WINDOW),'bounds13':list(CORE),'B_local':bh,'level_local':levels,
            'masks':masks,'protected':protected,'partial_F_cells':sorted(partial),
            'variables':variables,'variables_sha256_le_i32':digest,'lower':lower,'upper':upper,
            'stencils':records,'stencil_keys':keyrows,'stencil_sha256':canonical_sha(keyrows),
            'collar_stencils':[x for x in records if x['collar']],
            'collar_stencil_keys':collarkeys,'collar_stencil_sha256':canonical_sha(collarkeys),
            'nearflat_tau_m':tau,'nearflat_spans_count':int(core_spans.size),
            'nearflat_count':int(np.count_nonzero(core_spans<=tau))}


def reconstruct_crossings(bundle, domain):
    """Rebuild the finite P/F/SEA edge-crossing set and scalar 1m limits independently."""
    p=bundle['P'];f=bundle['F'];h=domain['B_local'];r0,r1,c0,c1=WINDOW
    variables={tuple(map(int,x)) for x in domain['variables']}
    lower=domain['lower'].copy();upper=domain['upper'].copy();records=[]
    offsets=((0,0,0),(0,1,1),(1,0,2),(1,1,3))
    for cr in range(r0-1,r1):
      for cc in range(c0-1,c1):
        if not (0<=cr<p.shape[0] and 0<=cc<p.shape[1]):continue
        fv=np.asarray(f[cr,cc],dtype=np.float64);pv=float(p[cr,cc])
        layers=[('SEA',(SEA,)*4)]
        if math.isfinite(pv):layers.append(('P',(pv,)*4))
        if np.isfinite(fv).all():layers.append(('F',tuple(float(v) for v in fv)))
        for layer,levels in layers:
          for ti,tri in enumerate(TRIS):
            for ia,ib in ((tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])):
                va=(cr+offsets[ia][0],cc+offsets[ia][1]);vb=(cr+offsets[ib][0],cc+offsets[ib][1])
                if not (r0<=va[0]<r1 and c0<=va[1]<c1 and r0<=vb[0]<r1 and c0<=vb[1]<c1):continue
                va_local=(va[0]-r0,va[1]-c0);vb_local=(vb[0]-r0,vb[1]-c0)
                ga=float(h[va_local]-levels[ia]);gb=float(h[vb_local]-levels[ib])
                if ga*gb>=0:continue
                va_mut=va in variables;vb_mut=vb in variables
                if va_mut and vb_mut:raise AssertionError(f'crossing has two mutable endpoints {va},{vb},{layer}')
                if va_mut==vb_mut:continue
                dry,dry_i,wet,wet_i=(va,ia,vb,ib) if va_mut else (vb,ib,va,ia)
                gd=float(h[dry[0]-r0,dry[1]-c0]-levels[dry_i]);gw=float(h[wet[0]-r0,wet[1]-c0]-levels[wet_i])
                if not (gd>0 and gw<0):raise AssertionError('crossing endpoint wet/dry roles inconsistent')
                length=CELL if va[0]==vb[0] or va[1]==vb[1] else CELL*math.sqrt(2.0)
                lo,hi,t0,tlo,thi=crossing_interval(levels[wet_i],h[wet[0]-r0,wet[1]-c0],levels[dry_i],h[dry[0]-r0,dry[1]-c0],length)
                ir,ic=dry[0]-CORE[0],dry[1]-CORE[2]
                lower[ir,ic]=max(lower[ir,ic],lo);upper[ir,ic]=min(upper[ir,ic],hi)
                records.append({'layer':layer,'cell_rc':[cr,cc],'edge_rc':[list(va),list(vb)],
                   'dry_rc':list(dry),'wet_rc':list(wet),'t0':t0,'tlo':tlo,'thi':thi,
                   'edge_len_m':length,'max_shift_m':1.0,'lower_m':lo,
                   'upper_m':None if not math.isfinite(hi) else hi,'upper_unbounded':not math.isfinite(hi)})
    if np.any(lower>upper):raise AssertionError('independently reconstructed crossing intervals are empty')
    return {'records':records,'sha256':canonical_sha(records),'lower':lower,'upper':upper}


def import_file(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    if not spec or not spec.loader: raise RuntimeError(f'cannot import frozen helper {path}')
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod)
    return mod


def crossing_t(level_w, h_w, level_d, h_d):
    """Linear shoreline parameter measured from wet endpoint w toward dry endpoint d."""
    gw=float(h_w)-float(level_w); gd=float(h_d)-float(level_d)
    if not (gw < 0.0 < gd): raise ValueError('edge is not wet-to-dry')
    return -gw/(gd-gw)


def baseline_oriented_crossings(level_a, base_a, level_b, base_b, cand_a, cand_b):
    """Return B/H crossing parameters using B's wet-to-dry orientation for either edge order."""
    ga=float(base_a)-float(level_a);gb=float(base_b)-float(level_b)
    if ga<0.0<gb:
        return (crossing_t(level_a,base_a,level_b,base_b),
                crossing_t(level_a,cand_a,level_b,cand_b))
    if gb<0.0<ga:
        return (crossing_t(level_b,base_b,level_a,base_a),
                crossing_t(level_b,cand_b,level_a,cand_a))
    raise ValueError('baseline edge does not have a strict shoreline crossing')


def crossing_interval(level_w, h_w, level_d, h_d, length, shift=1.0):
    """Candidate-height interval for a fixed wet endpoint and +/- shift on edge position."""
    gw=float(h_w)-float(level_w); gd=float(h_d)-float(level_d)
    if not (gw < 0.0 < gd): raise ValueError('edge is not wet-to-dry')
    t0=-gw/(gd-gw); tlo=max(0.0,t0-shift/float(length)); thi=min(1.0,t0+shift/float(length))
    lower=float(level_d)+gw*(1.0-1.0/thi)
    upper=math.inf if tlo==0.0 else float(level_d)+gw*(1.0-1.0/tlo)
    return lower,upper,t0,tlo,thi


def new_flat_windows(before, after, window=CORE, tau=TAU_FLAT):
    r0,r1,c0,c1=window
    b=np.asarray(before[r0:r1,c0:c1],dtype=np.float64)
    h=np.asarray(after[r0:r1,c0:c1],dtype=np.float64)
    if b.shape[0]<2 or b.shape[1]<2: return []
    bs=np.maximum.reduce((b[:-1,:-1],b[1:,:-1],b[:-1,1:],b[1:,1:]))-np.minimum.reduce((b[:-1,:-1],b[1:,:-1],b[:-1,1:],b[1:,1:]))
    hs=np.maximum.reduce((h[:-1,:-1],h[1:,:-1],h[:-1,1:],h[1:,1:]))-np.minimum.reduce((h[:-1,:-1],h[1:,:-1],h[:-1,1:],h[1:,1:]))
    rr,cc=np.nonzero((bs>tau)&(hs<=tau))
    return [[int(r0+r),int(c0+c),float(bs[r,c]),float(hs[r,c])] for r,c in zip(rr,cc)]


def focus_prominence(h, row=ROW, col=COL):
    h=np.asarray(h,dtype=np.float64)
    return {
      'east_west':max(0.0,float(h[row,col]-max(h[row,col-1],h[row,col+1]))),
      'north_south':max(0.0,float(h[row,col]-max(h[row-1,col],h[row+1,col])))}


def rowcol_peak_prominence(h, window=CORE):
    """Max strict 1-D peak prominence per core row and column, using in-core neighbors."""
    a=np.asarray(h,dtype=np.float64);r0,r1,c0,c1=window
    rows=[];cols=[]
    for r in range(r0,r1):
        rows.append(max([min(float(a[r,c]-a[r,c-1]),float(a[r,c]-a[r,c+1]))
                         for c in range(c0+1,c1-1) if a[r,c]>a[r,c-1] and a[r,c]>a[r,c+1]]+[0.0]))
    for c in range(c0,c1):
        cols.append(max([min(float(a[r,c]-a[r-1,c]),float(a[r,c]-a[r+1,c]))
                         for r in range(r0+1,r1-1) if a[r,c]>a[r-1,c] and a[r,c]>a[r+1,c]]+[0.0]))
    return np.asarray(rows),np.asarray(cols)


def local_mesh_angles(h, center=(ROW,COL), radius=2, collar=None):
    """Independent triangle/edge geometry for slope and dihedral checks near a vertex."""
    a=np.asarray(h,dtype=np.float64);R,C=map(int,center)
    rlo=max(0,R-radius-1);rhi=min(a.shape[0]-1,R+radius+1)
    clo=max(0,C-radius-1);chi=min(a.shape[1]-1,C+radius+1)
    edges=defaultdict(list);slopes=[]
    for r in range(rlo,rhi):
      for c in range(clo,chi):
        verts=((r,c),(r,c+1),(r+1,c),(r+1,c+1))
        tris=((verts[0],verts[1],verts[3]),(verts[0],verts[2],verts[3]))
        for tri in tris:
            xyz=np.asarray([[v[1]*CELL,float(a[v]),Z0-v[0]*CELL] for v in tri],dtype=np.float64)
            n=np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0]);norm=float(np.linalg.norm(n))
            if norm<=1e-15:raise AssertionError(f'degenerate local triangle {tri}')
            n/=norm
            if n[1]<0:n=-n
            slopes.append(math.degrees(math.atan2(math.hypot(float(n[0]),float(n[2])),abs(float(n[1])))))
            for i,j in ((0,1),(1,2),(2,0)):
                key=tuple(sorted((tri[i],tri[j])))
                if (R,C) in key:edges[key].append(n.copy())
    hinges=[];collar_hinges=[]
    for edge,normals in edges.items():
        if len(normals)!=2:continue
        dot=max(-1.0,min(1.0,float(np.dot(normals[0],normals[1]))))
        deg=math.degrees(math.acos(dot));record={'edge':[[int(r),int(c)] for r,c in edge],'angle_deg':deg}
        hinges.append(record)
        if collar is not None and any(v in collar for v in edge):collar_hinges.append(record)
    return {'max_slope_deg':max(slopes,default=0.0),'slopes_deg':slopes,
            'max_incident_hinge_deg':max((x['angle_deg'] for x in hinges),default=0.0),
            'hinges':hinges,'collar_max_hinge_deg':max((x['angle_deg'] for x in collar_hinges),default=0.0),
            'collar_hinges':collar_hinges}


def focus_gate(before, after, row=ROW, col=COL):
    bp=focus_prominence(before,row,col);hp=focus_prominence(after,row,col)
    a=np.asarray(after,dtype=np.float64)
    minima={'east_west':bool(a[row,col]<min(a[row,col-1],a[row,col+1])),
            'north_south':bool(a[row,col]<min(a[row-1,col],a[row+1,col]))}
    good=all(bp[k]>0 and hp[k]<=0.75*bp[k] and not minima[k] for k in bp)
    return {'passed':bool(good),'before':bp,'after':hp,'new_strict_minimum':minima,
            'reductions_fraction':{k:(None if bp[k]<=0 else 1-hp[k]/bp[k]) for k in bp}}


def stencil_records(window=WINDOW, core=CORE, variables=None):
    """Freeze plan stencils touching a core variable; XZ uses central +/-1 corners."""
    r0,r1,c0,c1=window;cr0,cr1,cc0,cc1=core
    vars_set=({(r,c) for r in range(cr0,cr1) for c in range(cc0,cc1)} if variables is None
              else {tuple(map(int,q)) for q in variables})
    collar={(r,c) for r in range(r0,r1) for c in range(c0,c1)
            if r<r0+2 or r>=r1-2 or c<c0+2 or c>=c1-2}
    out=[]
    def add(keykind, kind, anchor, nodes, coeff):
        ns=tuple(nodes)
        if any(q in vars_set for q in ns):
            out.append({'kind':kind,'nodes':ns,'coeff':tuple(float(x) for x in coeff),
                        'collar':any(q in collar for q in ns),
                        'key':[keykind,int(anchor[0]),int(anchor[1])]})
    for r in range(r0,r1):
      for c in range(c0,c1-2):
        add('xx','Dxx',(r,c),((r,c),(r,c+1),(r,c+2)),(1,-2,1))
    for r in range(r0,r1-2):
      for c in range(c0,c1):
        add('zz','Dzz',(r,c),((r,c),(r+1,c),(r+2,c)),(1,-2,1))
    for r in range(r0,r1-2):
      for c in range(c0,c1-2):
        add('xz','Dxz',(r,c),((r,c),(r,c+2),(r+2,c),(r+2,c+2)),(-.25,.25,.25,-.25))
    out.sort(key=lambda x:({'Dxx':0,'Dzz':1,'Dxz':2}[x['kind']],x['key'][1],x['key'][2]))
    return out


def stencil_energy(h, records, collar_only=False):
    a=np.asarray(h,dtype=np.float64); total=0.0; count=0
    for x in records:
        if collar_only and not x['collar']: continue
        vals=sum(k*a[r,c] for (r,c),k in zip(x['nodes'],x['coeff']))
        total+=(2.0 if x['kind']=='Dxz' else 1.0)*float(vals*vals);count+=1
    return float(total),count


def triangle_depth_min(poly, tri_xy, tri_h, plane):
    """Exact min of a constant P minus affine NW-SE terrain on clipped polygon."""
    if not math.isfinite(float(plane)): return None
    piece=poly.intersection(Polygon(tri_xy))
    if piece.is_empty or piece.area<=1e-12:return None
    coeff=np.linalg.solve(np.column_stack((tri_xy[:,0],tri_xy[:,1],np.ones(3))),np.asarray(tri_h,dtype=np.float64))
    coords=[]
    for geom in ([piece] if piece.geom_type=='Polygon' else list(getattr(piece,'geoms',[]))):
        if geom.geom_type!='Polygon' or geom.is_empty:continue
        coords.extend(np.asarray(geom.exterior.coords[:-1],dtype=np.float64).tolist())
        for ring in geom.interiors: coords.extend(np.asarray(ring.coords[:-1],dtype=np.float64).tolist())
    if not coords:return None
    q=np.asarray(coords,dtype=np.float64)
    return float(np.min(float(plane)-(q@coeff[:2]+coeff[2])))


def corridor_depth_report(h, p, feature_collection, comparison=None):
    """Recompute all 19 signed corridor polygons against exact P and native terrain triangles.

    This is a nominal geometric depth metric. It does not imply wave clearance or runtime boat behavior.
    """
    h=np.asarray(h,dtype=np.float64);p=np.asarray(p,dtype=np.float64)
    comparison=None if comparison is None else np.asarray(comparison,dtype=np.float64)
    if h.shape!=(N,N) or p.shape!=(N-1,N-1):raise ValueError('unexpected H/P shape')
    features=feature_collection.get('features',[])
    if len(features)!=19:raise AssertionError(f'expected 19 frozen corridor features, got {len(features)}')
    out=[]
    for feature in features:
        geom=shape(feature['geometry']);xmin,zmin,xmax,zmax=geom.bounds
        c0=max(0,int(math.floor(xmin/CELL)));c1=min(N-1,int(math.ceil(xmax/CELL)))
        r0=max(0,int(math.floor((Z0-zmax)/CELL)));r1=min(N-1,int(math.ceil((Z0-zmin)/CELL)))
        covered=0.0;unknown=0.0;unknown_changed=0.0;unknown_unchanged=0.0;unknown_max_delta=0.0;worst=None;tri_count=0
        # Enumerate only x cells under each row-strip intersection. A full corridor
        # bounding-box scan would test ~1.58M empty cells for Luga_0.
        for r,c in corridor_candidate_cells(geom, (r0,r1,c0,c1)):
            ztop=Z0-r*CELL;zbottom=ztop-CELL
            cellbox=box(c*CELL,zbottom,(c+1)*CELL,ztop)
            if not geom.intersects(cellbox):continue
            cellpoly=cellbox.intersection(geom)
            if cellpoly.is_empty:continue
            xy=np.asarray([[c*CELL,Z0-r*CELL],[(c+1)*CELL,Z0-r*CELL],
                           [c*CELL,Z0-(r+1)*CELL],[(c+1)*CELL,Z0-(r+1)*CELL]],dtype=np.float64)
            hv=np.asarray([h[r,c],h[r,c+1],h[r+1,c],h[r+1,c+1]],dtype=np.float64)
            for ti,tri in enumerate(TRIS):
                tpoly=Polygon(xy[list(tri)]);part=cellpoly.intersection(tpoly)
                if part.is_empty or part.area<=1e-12:continue
                tri_count+=1;covered+=float(part.area)
                area=float(part.area)
                level=float(p[r,c])
                if not math.isfinite(level):
                    unknown+=area
                    if comparison is not None:
                        other=np.asarray([comparison[r,c],comparison[r,c+1],comparison[r+1,c],comparison[r+1,c+1]],dtype=np.float64)
                        delta=np.abs(other[list(tri)]-hv[list(tri)])
                        if np.any(delta>0):unknown_changed+=area
                        else:unknown_unchanged+=area
                        unknown_max_delta=max(unknown_max_delta,float(delta.max(initial=0.0)))
                    continue
                depth=triangle_depth_min(part,xy[list(tri)],hv[list(tri)],level)
                if depth is None:continue
                if worst is None or depth<worst['depth_m']:
                    # Evaluate minimum location among intersection boundary vertices.
                    coeff=np.linalg.solve(np.column_stack((xy[list(tri),0],xy[list(tri),1],np.ones(3))),hv[list(tri)])
                    pieces=([part] if part.geom_type=='Polygon' else list(getattr(part,'geoms',[])))
                    allxy=[]
                    for q in pieces:
                        if q.geom_type=='Polygon':allxy.extend(np.asarray(q.exterior.coords[:-1],dtype=np.float64).tolist())
                    q=np.asarray(allxy,dtype=np.float64);vals=level-(q@coeff[:2]+coeff[2]);k=int(np.argmin(vals))
                    worst={'depth_m':float(vals[k]),'xz':[float(x) for x in q[k]],'cell_rc':[r,c],'triangle':ti}
        err=abs(covered-float(geom.area))
        out.append({'id':feature.get('properties',{}).get('river'), 'area_m2':float(geom.area),
                    'covered_area_m2':covered,'coverage_error_m2':err,'unknown_P_area_m2':unknown,
                    'unknown_P_area_changed_between_pair_m2':unknown_changed if comparison is not None else None,
                    'unknown_P_area_exact_between_pair_m2':unknown_unchanged if comparison is not None else None,
                    'unknown_P_max_triangle_vertex_delta_m':unknown_max_delta if comparison is not None else None,
                    'native_triangles':tri_count,'minimum_nominal_depth_m':None if worst is None else worst['depth_m'],
                    'worst':worst,'full_P_coverage':unknown<=1e-9 and err<=1e-5})
    vals=[x['minimum_nominal_depth_m'] for x in out if x['minimum_nominal_depth_m'] is not None]
    return {'feature_count':len(out),'all_covered':all(x['full_P_coverage'] for x in out),
            'global_minimum_nominal_depth_m':min(vals) if len(vals)==len(out) else None,
            'meets_0_95_everywhere':len(vals)==19 and min(vals)>=0.95,
            'corridors':out}


def corridor_candidate_cells(geom, bounds):
    """Enumerate positive-area grid cells intersected by a polygon via row strips."""
    r0,r1,c0,c1=bounds
    xmin,_,xmax,_=geom.bounds
    cells=[]
    for r in range(r0,r1):
        ztop=Z0-r*CELL;zbottom=ztop-CELL
        row_piece=geom.intersection(box(xmin,zbottom,xmax,ztop))
        if row_piece.is_empty:continue
        parts=[row_piece] if row_piece.geom_type=='Polygon' else [q for q in getattr(row_piece,'geoms',[]) if q.geom_type=='Polygon' and q.area>1e-12]
        candidate_cols=set()
        for part_geom in parts:
            px0,_,px1,_=part_geom.bounds
            pc0=max(c0,int(math.floor(px0/CELL)));pc1=min(c1,int(math.ceil(px1/CELL)))
            candidate_cols.update(range(pc0,pc1))
        for c in sorted(candidate_cols):
            cellbox=box(c*CELL,zbottom,(c+1)*CELL,ztop)
            if geom.intersects(cellbox) and geom.intersection(cellbox).area>1e-12:
                cells.append((r,c))
    return cells


def high_bed_floor_report(h, terrain):
    """The inherited high-navigable-bed scope, excluding user-preserved Narva/low-water areas."""
    hh=np.asarray(h,dtype=np.float64)
    rr,cc=np.indices(hh.shape)
    x=cc*CELL;z=Z0-rr*CELL
    narva=np.hypot(x-NARVA_CENTER_XZ[0],z-NARVA_CENTER_XZ[1])<=NARVA_EXCLUSION_M
    high=(np.asarray(terrain['cls'])==3)&(np.asarray(terrain['level'])>=2)&~narva
    old=np.asarray(terrain['heights'],dtype=np.float64)
    return {'scope_vertices':int(np.count_nonzero(high)),
            'baseline_below_1m':int(np.count_nonzero(high&(old<1.0))),
            'candidate_below_1m':int(np.count_nonzero(high&(hh<1.0))),
            'high_bed_floor_1m_pass':bool(np.all(hh[high]>=1.0)),
            'scope_rule':'cls==3 && level>=2 && distance_to_frozen_Narva_center>620m'}


def axial_extrema(h, window=CORE):
    """Strict 4-neighbor extrema with prominence over the higher/lower adjacent pair."""
    a=np.asarray(h,dtype=np.float64);r0,r1,c0,c1=window;out=[]
    for r in range(max(1,r0),min(a.shape[0]-1,r1)):
      for c in range(max(1,c0),min(a.shape[1]-1,c1)):
        v=float(a[r,c]);neigh=(float(a[r,c-1]),float(a[r,c+1]),float(a[r-1,c]),float(a[r+1,c]))
        if v>max(neigh): out.append({'row':r,'col':c,'kind':'max','prominence':v-max(neigh)})
        elif v<min(neigh): out.append({'row':r,'col':c,'kind':'min','prominence':min(neigh)-v})
    return out


def extrema_matching(before, after, window=CORE, radius=1):
    """Maximum bipartite matching: each H extremum needs one unused B of same kind and >= prominence."""
    b=axial_extrema(before,window);h=axial_extrema(after,window)
    adj=[]
    for x in h:
        cand=[i for i,y in enumerate(b) if y['kind']==x['kind'] and max(abs(y['row']-x['row']),abs(y['col']-x['col']))<=radius and y['prominence']>=x['prominence']]
        adj.append(cand)
    owner={}
    def aug(i,seen):
        for j in adj[i]:
            if j in seen:continue
            seen.add(j)
            if j not in owner or aug(owner[j],seen):owner[j]=i;return True
        return False
    matched=sum(aug(i,set()) for i in sorted(range(len(h)),key=lambda k:(len(adj[k]),h[k]['row'],h[k]['col'])))
    pairs=sorted((j,i) for j,i in owner.items())
    used_b={j for j,_ in pairs};used_h={i for _,i in pairs}
    return {'passed':matched==len(h),'B_count':len(b),'H_count':len(h),'matched':matched,
            'new_H':[h[i] for i in range(len(h)) if i not in used_h],
            'extinguished_B':[b[i] for i in range(len(b)) if i not in used_b],
            'pairs':[{'B':b[j],'H':h[i]} for j,i in pairs]}


def check_fixtures():
    results={}
    # Crossing formula: both edge orientations share scalar geometry; test both movement directions.
    lo,hi,t0,tlo,thi=crossing_interval(0.0,-1.0,0.0,3.0,6.0)
    assert abs(crossing_t(0,-1,0,lo)-thi)<1e-12
    assert abs(crossing_t(0,-1,0,hi)-tlo)<1e-12
    moved=crossing_t(0,-1,0,lo+1e-6)
    assert abs(moved-t0)*6<1.0
    assert abs(t0-(t0+1.01/6))*6>1.0
    diagonal=crossing_interval(0,-1,0,3,6*math.sqrt(2))
    assert diagonal[2]==t0 and diagonal[3]<diagonal[4]
    forward=baseline_oriented_crossings(0,-1,0,3,-.5,3.5)
    reverse=baseline_oriented_crossings(0,3,0,-1,3.5,-.5)
    assert np.allclose(forward,(.25,.125),rtol=0,atol=1e-15)
    assert np.allclose(reverse,forward,rtol=0,atol=1e-15)
    # Near-flat threshold is strict at B and inclusive after H; test equality and ULP boundaries.
    flat_b=np.zeros((17,17),dtype=np.float64);flat_h=flat_b.copy()
    flat_b[1,1]=np.nextafter(TAU_FLAT,np.inf);flat_h[1,1]=TAU_FLAT
    assert new_flat_windows(flat_b,flat_h,(0,17,0,17),TAU_FLAT)
    assert not new_flat_windows(flat_b,flat_b,(0,17,0,17),TAU_FLAT)
    nonflat=np.zeros((17,17),dtype=np.float64);nonflat[1,1]=TAU_FLAT+1e-4
    assert new_flat_windows(nonflat,flat_h,(0,17,0,17),TAU_FLAT)
    # Exact polynomial energy fixture and collar stencil population.
    xx,zz=np.meshgrid(np.arange(17,dtype=float),np.arange(17,dtype=float));plane=2*xx-3*zz+5
    s=stencil_records((0,17,0,17),(2,15,2,15));e,n=stencil_energy(plane,s)
    assert n>0 and abs(e)<1e-18
    bowl=xx*xx+zz*zz;e2,_=stencil_energy(bowl,s);assert e2>0
    # Central XZ stencil uses the four diagonal corners of a 3x3 neighborhood.
    # With world z=-row, h=x*z must yield Dxz=1; separable quadratics yield 0.
    mixed=[{'kind':'Dxz','nodes':((0,0),(0,2),(2,0),(2,2)),
            'coeff':(-.25,.25,.25,-.25),'collar':False}]
    rr,cc=np.mgrid[0:3,0:3]
    xz=-rr*cc
    es,ns=stencil_energy(xz,mixed)
    assert ns==1 and abs(es-2.0)<1e-15
    separable=rr*rr+cc*cc
    ez,nz=stencil_energy(separable,mixed)
    assert nz==1 and abs(ez)<1e-15
    # Exact clipped depth is an affine extremum at polygon vertices; no raster sampling.
    tri_xy=np.asarray([[0.,0.],[6.,0.],[6.,-6.]])
    tri_poly=Polygon(tri_xy)
    assert abs(triangle_depth_min(tri_poly,tri_xy,np.asarray([0.,0.,0.]),3.0)-3.0)<1e-12
    assert abs(triangle_depth_min(tri_poly,tri_xy,np.asarray([0.,0.,6.]),3.0)+3.0)<1e-12
    assert triangle_depth_min(tri_poly,tri_xy,np.asarray([0.,0.,0.]),float('nan')) is None
    # The 19-feature path checks geometry coverage and never fills missing P.
    from shapely.geometry import mapping
    # Cell [0,0] spans x=[0,6], z=[Z0-6,Z0]; keep the test corridor inside it.
    tiny=Polygon([(0.5,Z0-0.5),(5.5,Z0-0.5),(5.5,Z0-5.5),(0.5,Z0-5.5)])
    fc={'type':'FeatureCollection','features':[{'type':'Feature','properties':{'river':str(i)},'geometry':mapping(tiny)} for i in range(19)]}
    fake_h=np.zeros((N,N),dtype=np.float64);fake_p=np.full((N-1,N-1),3.0,dtype=np.float64)
    cr=corridor_depth_report(fake_h,fake_p,fc)
    assert cr['all_covered'] and cr['meets_0_95_everywhere'] and abs(cr['global_minimum_nominal_depth_m']-3.0)<1e-12
    fake_p[0,0]=np.nan;cr_unknown=corridor_depth_report(fake_h,fake_p,fc)
    assert not cr_unknown['all_covered'] and cr_unknown['global_minimum_nominal_depth_m'] is None
    fake_p[0,0]=0.94;cr_shallow=corridor_depth_report(fake_h,fake_p,fc)
    assert cr_shallow['all_covered'] and not cr_shallow['meets_0_95_everywhere']
    # Row-strip enumeration must match exhaustive bbox clipping for diagonal edges,
    # a polygon hole, exact grid-aligned boundaries, and cells touched only at edges.
    shell=[(0.0,Z0),(42.0,Z0-6.0),(54.0,Z0-24.0),(36.0,Z0-48.0),
           (12.0,Z0-42.0),(0.0,Z0-24.0),(0.0,Z0)]
    hole=[(18.0,Z0-12.0),(30.0,Z0-12.0),(30.0,Z0-24.0),
          (18.0,Z0-24.0),(18.0,Z0-12.0)]
    clip_fixture=Polygon(shell,[hole])
    fxmin,fzmin,fxmax,fzmax=clip_fixture.bounds
    fb=(max(0,int(math.floor((Z0-fzmax)/CELL))),
        min(17,int(math.ceil((Z0-fzmin)/CELL))),
        max(0,int(math.floor(fxmin/CELL))),min(17,int(math.ceil(fxmax/CELL))))
    fast=set(corridor_candidate_cells(clip_fixture,fb));slow=set()
    for fr in range(fb[0],fb[1]):
      for fc in range(fb[2],fb[3]):
        cell=box(fc*CELL,Z0-(fr+1)*CELL,(fc+1)*CELL,Z0-fr*CELL)
        if clip_fixture.intersection(cell).area>1e-12:slow.add((fr,fc))
    assert fast==slow and len(fast)>20
    # Focus prominence, row/column peaks, and local 3-D triangle angles.
    peak=np.zeros((9,9));peak[4,4]=4.0
    fgate=focus_gate(peak,peak.copy(),4,4);assert not fgate['passed']
    reduced=peak.copy();reduced[4,4]=2.0
    assert focus_gate(peak,reduced,4,4)['passed']
    ramp=peak.copy();ramp[4,4]=1.0;ramp[4,5]=2.0;ramp[5,4]=2.0
    pit=peak.copy();pit[4,4]=-1.0
    assert focus_gate(peak,ramp,4,4)['passed']
    assert not focus_gate(peak,pit,4,4)['passed']
    rp,cp=rowcol_peak_prominence(peak,(1,8,1,8));assert rp[3]==4.0 and cp[3]==4.0
    local_plane=np.fromfunction(lambda r,c: 0.5*c-0.25*r,(9,9),dtype=float)
    ang=local_mesh_angles(local_plane,(4,4),radius=1)
    assert ang['max_incident_hinge_deg']<1e-6 and max(ang['slopes_deg'])>0
    pyramid=local_plane.copy();pyramid[4,4]+=3.0
    assert local_mesh_angles(pyramid,(4,4),radius=1)['max_incident_hinge_deg']>0
    # One-to-one extremum matching: a single B maximum cannot justify two H maxima.
    b=np.zeros((9,9));b[4,4]=2
    h=np.zeros((9,9));h[4,3]=2;h[4,5]=2
    m=extrema_matching(b,h,(1,8,1,8),1)
    assert not m['passed'] and len(m['new_H'])==1
    # A matched, non-worsened extremum is positive.
    m2=extrema_matching(b,b.copy(),(1,8,1,8),1);assert m2['passed']
    # Window/core dimensions are fixed before authoring, not inferred from candidate.
    assert (WINDOW[1]-WINDOW[0],WINDOW[3]-WINDOW[2])==(17,17)
    assert (CORE[1]-CORE[0],CORE[3]-CORE[2])==(13,13)
    results.update(crossing_bidirectional=True,crossing_diagonal=True,crossing_endpoint_order_independent=True,nearflat_tau_edges=True,
                   stencil_plane_bowl_and_central_xz=True,nominal_depth_exact_triangle_clip=True,
                   corridor_area_coverage_and_unknown_P=True,corridor_row_strip_matches_exhaustive=True,
                   focus_peak_to_ramp_passes_pit_fails=True,focus_rowcol_and_local_mesh_geometry=True,extrema_one_to_one=True,window_core_dimensions=True)
    return results


def check_frozen_representation_fixtures():
    ev=import_file('ev88_fixture_ev87',EV87)
    cv=import_file('ev88_fixture_coverage',COVERAGE);cv.ev=ev
    if sha(EV87)!=EV87_SHA or sha(COVERAGE)!=CV_SHA:raise AssertionError('frozen representation consumer source hash mismatch')
    if sha(Path(COVERAGE.parent/'../coverage-contract-proposal.md').resolve())!=CV_POLICY_SHA:
        raise AssertionError('frozen coverage policy hash mismatch')
    return {'ev87_geometry_controls':ev.verify_controls(),'coverage_policy_fixtures':cv.fixture_suite()}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--self-test',action='store_true')
    ap.add_argument('--preflight-only',action='store_true')
    ap.add_argument('--candidate',type=Path,default=EV88_CANDIDATE)
    ap.add_argument('--authoring-receipt',type=Path,default=EV88_RECEIPT)
    ap.add_argument('--report',type=Path,default=HERE/'ev88q-review.json')
    args=ap.parse_args()
    fixtures=check_fixtures()
    if args.self_test:
        fixtures['frozen_representation_consumers']=check_frozen_representation_fixtures()
        print(json.dumps({'status':'FIXTURES_PASS_NOT_CANDIDATE_ACCEPTANCE','fixtures':fixtures},indent=2));return 0
    if args.preflight_only:
        try:
            fixtures['frozen_representation_consumers']=check_frozen_representation_fixtures()
            bundle=checked_sources();pre=verify_preflight(bundle)
            receipt=verify_authoring_receipt(args.authoring_receipt,args.candidate,pre)
            out={'status':'PREFLIGHT_AND_RECEIPT_PASS_NOT_CANDIDATE_ACCEPTANCE','fixtures':fixtures,
                 'preflight':{k:v for k,v in pre.items() if k not in ('domain','crossings')},
                 'solver':receipt['solver'],'candidate_sha256':receipt['candidate_sha256']}
            print(json.dumps(out,indent=2,ensure_ascii=False));return 0
        except Exception as exc:
            print(json.dumps({'status':'PREFLIGHT_FAIL','error':f'{type(exc).__name__}: {exc}',
              'traceback':traceback.format_exc()},indent=2,ensure_ascii=False));return 1
    report={'status':'ERROR_EV88Q_OFFLINE_CONSUMER','fixtures':fixtures,'candidate_path':str(args.candidate),
      'authoring_receipt_path':str(args.authoring_receipt)}
    try:
        report=evaluate_candidate(args.candidate,args.authoring_receipt)
        report['fixtures']=fixtures
        report['consumer_sha256']=sha(Path(__file__).resolve())
    except Exception as exc:
        report.update(status='ERROR_EV88Q_OFFLINE_CONSUMER',error=f'{type(exc).__name__}: {exc}',traceback=traceback.format_exc())
    args.report.parent.mkdir(parents=True,exist_ok=True)
    tmp=args.report.with_suffix(args.report.suffix+'.tmp')
    tmp.write_text(json.dumps(report,indent=2,ensure_ascii=False,default=lambda x:bool(x) if isinstance(x,np.bool_) else int(x) if isinstance(x,np.integer) else float(x) if isinstance(x,np.floating) else str(x))+'\n',encoding='utf-8')
    tmp.replace(args.report)
    print(json.dumps({'status':report.get('status'),'false_gates':[k for k,v in report.get('gates',{}).items() if v is False],
      'error':report.get('error'),'report':str(args.report)},ensure_ascii=False),flush=True)
    return 0 if report.get('status')=='PASS_EV88Q_OFFLINE_CONSUMER' else 1

if __name__=='__main__':
    raise SystemExit(main())
