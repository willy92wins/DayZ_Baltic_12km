from __future__ import annotations
import hashlib, importlib.util, json, time
from pathlib import Path
import numpy as np

OUT=Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/ev95-global-shape-census')
SCRIPT=Path(__file__).resolve()
ROOT=Path(r'E:/DayZ-Baltic-Build')
EV87=ROOT/'v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py'
B=ROOT/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'
H=ROOT/'v30-global-bank-extension-20261010/global-operator-prototype/real-sector-preflight/ev94-rebase/slope-bound/composition-run-01/terrain.npz'
EV79C=ROOT/'v30-narva-dry-bank-relief-20261010/constraints.npz'
V2=ROOT/'v30-global-bank-extension-20261010/ev93-face-index/surface-census/v2'
V2NPZ=V2/'sector-native-curvature-census.npz'; V2JSON=V2/'summary.json'
EXPECTED={
 'EV87':'964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27',
 'B':'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
 'EV95':'40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a',
 'EV79C':'ad0cffd5f26fc942e17fc959236494287650b1528b728a15f4b1100da72f319c',
}
FAMILIES=('diag','vertical','horizontal')
POPS=('all','bank','interior','wet_support')
EPS=1e-6

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''): h.update(block)
    return h.hexdigest()

def load_ev87():
    spec=importlib.util.spec_from_file_location('ev87_shape_census',EV87)
    if spec is None or spec.loader is None: raise ImportError(str(EV87))
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    if sha(EV87)!=EXPECTED['EV87']: raise AssertionError('EV87 pin changed')
    return mod

def same_array(a,b):
    if a.shape!=b.shape or a.dtype!=b.dtype: return False
    if np.issubdtype(a.dtype,np.inexact): return bool(np.array_equal(a,b,equal_nan=True))
    return bool(np.array_equal(a,b))

def fixture(ev87):
    flat=np.zeros((7,7),dtype=np.float32)
    plane=(np.arange(7,dtype=np.float32)[None,:]*0.25 + np.arange(7,dtype=np.float32)[:,None]*-0.125)
    flat_metrics=dict(ev87.edge_angles(flat)); plane_metrics=dict(ev87.edge_angles(plane))
    assert all(np.max(a,initial=0.0)==0 for a in flat_metrics.values())
    assert all(np.max(a,initial=0.0)<1e-5 for a in plane_metrics.values())
    pyramid=flat.copy(); pyramid[3,3]=5.0
    pyramid_metrics=dict(ev87.edge_angles(pyramid))
    assert any(np.max(a)>30.0 for a in pyramid_metrics.values())
    perturbed=plane.copy(); perturbed[3,3]+=np.float32(0.25)
    changed=dict(ev87.edge_angles(perturbed))
    assert all(changed[k].shape==plane_metrics[k].shape for k in FAMILIES)
    assert any(np.any(np.abs(changed[k]-plane_metrics[k])>EPS) for k in FAMILIES)
    return {'flat_zero_all_families':True,'affine_plane_zero_all_families':True,
            'pyramid_has_hinges_over_30':True,'single_vertex_perturbation_changes_hinges':True,
            'family_shapes':{k:list(v.shape) for k,v in plane_metrics.items()}}

def metrics(before,after):
    d=after-before
    return {'n':int(before.size),'above30_B':int(np.count_nonzero(before>30.0)),
      'above30_EV95':int(np.count_nonzero(after>30.0)),
      'new_above30':int(np.count_nonzero((before<=30.0)&(after>30.0))),
      'improved_gt_1e-6':int(np.count_nonzero(d < -EPS)),
      'worsened_gt_1e-6':int(np.count_nonzero(d > EPS)),
      'within_1e-6':int(np.count_nonzero(np.abs(d)<=EPS)),
      'max_B_deg':float(np.max(before,initial=0.0)),'max_EV95_deg':float(np.max(after,initial=0.0)),
      'p99_B_deg':float(np.percentile(before,99)) if before.size else None,
      'p99_EV95_deg':float(np.percentile(after,99)) if after.size else None,
      'mean_square_B_deg2':float(np.mean(before*before,dtype=np.float64)) if before.size else None,
      'mean_square_EV95_deg2':float(np.mean(after*after,dtype=np.float64)) if after.size else None}

def top_records(kind,before,after,masks):
    delta=after-before; flat_delta=delta.ravel(); flat_after=after.ravel(); n=flat_delta.size
    changed=np.flatnonzero(flat_delta>EPS)
    if changed.size:
        take=changed[np.argsort(flat_delta[changed],kind='stable')[-20:][::-1]]
    else: take=np.empty(0,dtype=np.int64)
    rem=np.flatnonzero(flat_after>30.0)
    if rem.size: rem=rem[np.argsort(flat_after[rem],kind='stable')[-20:][::-1]]
    cols=before.shape[1]
    def rec(ix):
        r=int(ix//cols);c=int(ix%cols)
        return {'anchor_rc':[r,c],'B_deg':float(before[r,c]),'EV95_deg':float(after[r,c]),
          'delta_deg':float(delta[r,c]),'any_bank':bool(masks['bank'][r,c]),
          'any_interior':bool(masks['interior'][r,c]),'any_wet_support':bool(masks['wet_support'][r,c])}
    return {'largest_worsenings_gt_1e-6':[rec(int(i)) for i in take],
            'largest_remaining_over30':[rec(int(i)) for i in rem]}

def main():
    started=time.perf_counter()
    paths={'EV87':EV87,'B':B,'EV95':H,'EV79C':EV79C,'census_v2_npz':V2NPZ,'census_v2_summary':V2JSON,'census_script':SCRIPT}
    pins_start={k:sha(v) for k,v in paths.items()}
    for k in EXPECTED:
        if pins_start[k]!=EXPECTED[k]: raise AssertionError(f'{k} SHA changed: {pins_start[k]}')
    ev87=load_ev87(); fixture_result=fixture(ev87)
    with np.load(B,allow_pickle=False) as zb, np.load(H,allow_pickle=False) as zh:
        if tuple(zb.files)!=tuple(zh.files): raise AssertionError('B/EV95 key inventory differs')
        base={k:zb[k] for k in ('cls','reserve','platform','heights')}
        hb=zb['heights']; hh=zh['heights']
        metadata=[]
        for key in zb.files:
            if key=='heights': continue
            a=zb[key]; b=zh[key]
            if not same_array(a,b): raise AssertionError(f'metadata differs: {key}')
            metadata.append(key)
    if hb.shape!=(2048,2048) or hh.shape!=hb.shape or hb.dtype!=np.float32 or hh.dtype!=np.float32:
        raise AssertionError('terrain heights shape/dtype mismatch')
    with np.load(EV79C,allow_pickle=False) as zc:
        if 'wet_support' not in zc.files: raise AssertionError('wet_support missing')
        wet_support=zc['wet_support'].astype(bool)
    cons={'wet_support':wet_support}
    populations=ev87._ev87_populations(base,cons)
    vertex_masks={'bank':np.asarray(populations['bank'],dtype=bool),
                  'interior':np.asarray(populations['interior'],dtype=bool),
                  'wet_support':wet_support}
    if any(m.shape!=hb.shape for m in vertex_masks.values()): raise AssertionError('population mask shape mismatch')
    with np.load(V2NPZ,allow_pickle=False) as vz:
        v2angles={k:vz[f'angle_{k}'] for k in FAMILIES}
        v2inc={k:vz[f'incidence_{k}'] for k in FAMILIES}
    summary=json.loads(V2JSON.read_text(encoding='utf-8'))
    if summary.get('status')!='PASS_OFFLINE_CENSUS' or summary.get('sources',{}).get('sha256',{}).get('B')!=EXPECTED['B']:
        raise AssertionError('v2 census provenance/status mismatch')
    b_angles=dict(ev87.edge_angles(hb.astype(np.float64)))
    h_angles=dict(ev87.edge_angles(hh.astype(np.float64)))
    for kind in FAMILIES:
        if not np.array_equal(np.asarray(b_angles[kind],dtype=np.float64),np.asarray(v2angles[kind],dtype=np.float64)):
            raise AssertionError(f'B EV87 angle array differs from pinned census v2: {kind}')
    if tuple(h_angles)!=FAMILIES: raise AssertionError('EV87 family order changed')
    vertex_count={k:int(np.count_nonzero(v)) for k,v in vertex_masks.items()}
    incident={k:{} for k in FAMILIES}
    direct_check={}
    bit=summary['scope']['incidence_bit_flags']
    for kind in FAMILIES:
        if v2angles[kind].shape!=h_angles[kind].shape or v2inc[kind].shape!=h_angles[kind].shape:
            raise AssertionError(f'hinge array shape mismatch for {kind}')
        if not np.isfinite(h_angles[kind]).all(): raise AssertionError(f'nonfinite angles {kind}')
        for pop,vm in vertex_masks.items():
            m=np.logical_or.reduce(ev87.edge_vertex_slices(vm,kind))
            flagname='any_'+pop
            from_v2=(v2inc[kind]&np.uint32(bit[flagname]))!=0
            if not np.array_equal(m,from_v2): raise AssertionError(f'v2 incidence mismatch {kind}/{pop}')
            incident[kind][pop]=m
            direct_check[f'{kind}/{pop}']=int(np.count_nonzero(m))
        old=summary['families'][kind]['global']['all']
        olda=np.asarray(v2angles[kind],dtype=np.float64)
        if int(old['n'])!=olda.size or abs(float(old['max_deg'])-float(olda.max()))>1e-12 or abs(float(old['p99_deg'])-float(np.percentile(olda,99)))>1e-12 or abs(float(old['mean_square_deg2'])-float(np.mean(olda*olda,dtype=np.float64)))>1e-12:
            raise AssertionError(f'v2 baseline aggregate mismatch {kind}')
    # Metrics per family and per stable, overlapping incidence-ANY population.
    family_metrics={}; aggregate_inputs={p:{'B':[],'EV95':[]} for p in POPS}
    worsened=[]; remaining=[]
    for kind in FAMILIES:
        b=np.asarray(b_angles[kind],dtype=np.float64); a=np.asarray(h_angles[kind],dtype=np.float64)
        if b.shape!=a.shape: raise AssertionError(f'angle shape mismatch {kind}')
        family_metrics[kind]={}
        for pop in POPS:
            m=np.ones(b.shape,dtype=bool) if pop=='all' else incident[kind][pop]
            bv=b[m]; av=a[m]
            family_metrics[kind][pop]=metrics(bv,av)
            aggregate_inputs[pop]['B'].append(bv)
            aggregate_inputs[pop]['EV95'].append(av)
        masks={p:(np.ones(b.shape,dtype=bool) if p=='all' else incident[kind][p]) for p in ('bank','interior','wet_support')}
        tops=top_records(kind,b,a,masks)
        worsened.append({'family':kind,**tops})
    aggregate_metrics={}
    for pop in POPS:
        bv=np.concatenate(aggregate_inputs[pop]['B']);av=np.concatenate(aggregate_inputs[pop]['EV95'])
        aggregate_metrics[pop]=metrics(bv,av)
    overlap_counts={}
    for kind in FAMILIES:
        bmask=incident[kind]['bank']; imask=incident[kind]['interior']; wmask=incident[kind]['wet_support']
        overlap_counts[kind]={'bank_intersection_interior':int(np.count_nonzero(bmask&imask)),
          'bank_intersection_wet_support':int(np.count_nonzero(bmask&wmask)),
          'interior_intersection_wet_support':int(np.count_nonzero(imask&wmask))}
    pins_end={k:sha(v) for k,v in paths.items()}
    if pins_start!=pins_end: raise AssertionError('input drift during census')
    report={'schema':'ev95.global_native_hinge_census.v1','status':'COMPLETE_OFFLINE_CENSUS',
      'claim_limit':'Geometric angle/count census only; not an artistic or in-game quality PASS.',
      'inputs':{k:{'path':str(paths[k]),'sha256':pins_start[k]} for k in paths},
      'terrain':{'shape':list(hb.shape),'dtype':str(hb.dtype),'metadata_keys_equal_except_heights':metadata,
        'B_sha256':pins_start['B'],'EV95_sha256':pins_start['EV95']},
      'method':{'angle_source':'verify_ev87.edge_angles recomputed on full B and EV95 grids after promoting native float32 heights to float64 (as in v2); B arrays required exact-equal to pinned v2 baseline',
        'families':list(FAMILIES),'population_vertex_masks':{'bank':'EV87._ev87_populations on B cls/reserve/platform plus frozen EV79 wet_support','interior':'same EV87 population complement','wet_support':'frozen EV79 constraints wet_support'},
        'incidence':'ANY of the four exact vertices from verify_ev87.edge_vertex_slices; populations overlap at hinge level',
        'threshold_new_over30_deg':'strict >30.0; this is descriptive, not consumer gate',
        'improved_worsened':'delta=EV95-B in degrees; improved if delta < -1e-6; worsened if delta > +1e-6; otherwise within tolerance',
        'energy':'mean(angle_deg squared), reported as mean_square_deg2',
        'p99':'numpy percentile default linear interpolation on concatenated three family arrays'},
      'fixture':fixture_result,'exhaustive':{'all_native_family_shapes':{k:list(v.shape) for k,v in h_angles.items()},
        'total_hinges':int(sum(a.size for a in h_angles.values())),
        'v2_all_family_baseline_reconciled':True,'EV87_B_angles_exact_equal_v2':True,'v2_incidence_flags_reconciled_for_three_populations':direct_check,
        'population_vertex_counts':vertex_count,'overlap_hinge_counts':overlap_counts},
      'by_family':family_metrics,'aggregate_three_families':aggregate_metrics,'top20_by_family':worsened,
      'source_readset_start':pins_start,'source_readset_end':pins_end,
      'elapsed_seconds':time.perf_counter()-started}
    out_json=OUT/'report.json';out_json.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    # CSV of all hinges worsened beyond tolerance. This is a reproducible diagnostic inventory, not a defect verdict.
    import csv
    out_csv=OUT/'worsened-hinges.csv'
    with out_csv.open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['family','anchor_row','anchor_col','B_angle_deg','EV95_angle_deg','delta_deg','any_bank','any_interior','any_wet_support'])
        for kind in FAMILIES:
            b=np.asarray(b_angles[kind],dtype=np.float64);a=np.asarray(h_angles[kind],dtype=np.float64);d=a-b
            rr,cc=np.where(d>EPS)
            for r,c in zip(rr.tolist(),cc.tolist()):
                w.writerow([kind,r,c,format(float(b[r,c]),'.17g'),format(float(a[r,c]),'.17g'),format(float(d[r,c]),'.17g'),
                  int(incident[kind]['bank'][r,c]),int(incident[kind]['interior'][r,c]),int(incident[kind]['wet_support'][r,c])])
    print(json.dumps({'status':report['status'],'total_hinges':report['exhaustive']['total_hinges'],
      'aggregate':aggregate_metrics,'report':str(out_json),'csv':str(out_csv),'elapsed_seconds':report['elapsed_seconds']},allow_nan=False))

if __name__=='__main__': main()





