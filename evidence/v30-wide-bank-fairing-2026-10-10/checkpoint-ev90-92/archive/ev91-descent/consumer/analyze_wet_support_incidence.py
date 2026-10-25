#!/usr/bin/env python
"""Read-only incidence expansion of the EV91 wet-support hinge diagnostic."""
from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
OUT_JSON = HERE / 'wet-support-incidence.json'
GIS_PYTHON = Path(r'C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe')
EXPECTED_CANDIDATE = '865901ab24aa3736da57847f9112d3c73181085213f89b48ef2e3e7a9f6ee702'
EXPECTED_EV91 = '5e726b93642f5db531193a8f1d85afabd139c7b9ac3afca4479df793afd53668'
EXPECTED_EV87 = '964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27'

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''): h.update(b)
    return h.hexdigest()

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise ImportError(path)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def project_nodes(ev87, hinge_mask, kind, shape):
    out=np.zeros(shape,dtype=bool)
    offsets={'diag':((0,0),(0,1),(1,0),(1,1)),
             'vertical':((0,0),(0,1),(1,1),(1,2)),
             'horizontal':((0,0),(1,0),(1,1),(2,1))}[kind]
    rr,cc=np.nonzero(hinge_mask)
    for dr,dc in offsets: out[rr+dr,cc+dc]=True
    return out

def fixture(ev87):
    # For one isolated supported node at (2,2), independently enumerate every
    # four-corner hinge containing it; ANY must match, ALL-FOUR must be empty.
    n=6; pop=np.zeros((n,n),dtype=bool); pop[2,2]=True; results={}
    for kind in ('diag','vertical','horizontal'):
        got=ev87.incident_any(pop,kind)
        all4=np.logical_and.reduce(ev87.edge_vertex_slices(pop,kind))
        shape=got.shape; expected=np.zeros(shape,dtype=bool)
        for r in range(shape[0]):
            for c in range(shape[1]):
                if (2,2) in ev87._ev87_hinge_vertices(kind,r,c): expected[r,c]=True
        results[kind]={'any_count':int(got.sum()),'expected_count':int(expected.sum()),
                       'any_exact':bool(np.array_equal(got,expected)),
                       'all_four_count':int(all4.sum()),'pass':bool(np.array_equal(got,expected) and not all4.any())}
    # A complete hinge must be included by ALL-FOUR and ANY in exactly its cell.
    full={}
    for kind in ('diag','vertical','horizontal'):
        p=np.zeros((n,n),dtype=bool)
        for r,c in ev87._ev87_hinge_vertices(kind,1,1): p[r,c]=True
        anym=ev87.incident_any(p,kind); allm=np.logical_and.reduce(ev87.edge_vertex_slices(p,kind))
        expected=np.zeros(allm.shape,dtype=bool); expected[1,1]=True
        full[kind]={'target_any':bool(anym[1,1]),'target_all_four':bool(allm[1,1]),
                    'all_four_count':int(allm.sum()),'pass':bool(anym[1,1] and np.array_equal(allm,expected))}
    return {'single_vertex_incidence':results,'single_hinge_four_vertex_support':full,
            'pass':all(x['pass'] for x in results.values()) and all(x['pass'] for x in full.values())}

def main():
    ev91_path=HERE/'verify_ev91.py'; candidate=HERE.parent/'candidate-terrain.npz'
    if sha(ev91_path)!=EXPECTED_EV91: raise AssertionError('EV91 verifier pin mismatch')
    consumer=load('ev91_incidence_consumer',ev91_path)
    if sha(candidate)!=EXPECTED_CANDIDATE: raise AssertionError('EV91 candidate pin mismatch')
    for path,want in consumer.PINNED.items():
        if sha(path)!=want: raise AssertionError(f'pinned input mismatch: {path}')
    ev=consumer.load_pinned('ev88_incidence_helpers',consumer.EV88_PATH,consumer.PINNED[str(consumer.EV88_PATH)])
    bundle=ev.checked_sources()
    ev87=ev.import_file('ev87_incidence_geometry',consumer.EV87_PATH)
    if sha(consumer.EV87_PATH)!=EXPECTED_EV87: raise AssertionError('EV87 helper pin mismatch')
    with np.load(candidate,allow_pickle=False) as z: h=np.asarray(z['heights'])
    b=np.asarray(bundle['B']['heights']); cons=bundle['constraints']; prior=bundle['prior']
    if b.shape!=(2048,2048) or h.shape!=b.shape or b.dtype!=np.float32 or h.dtype!=np.float32: raise AssertionError('B/H layout mismatch')
    eligible,_=ev87._ev87_eligible(bundle['B'],cons,prior,b,bundle['P'],bundle['F'])
    pop=eligible & cons['wet_support'].astype(bool)
    if int(pop.sum())!=65955: raise AssertionError(f'wet population changed: {int(pop.sum())}')
    pops=ev87._ev87_populations(bundle['B'],cons)
    categories={'wet_support':pop,'bank':pops['bank'],'interior':pops['interior']}
    a_b=dict(ev87.edge_angles(b)); a_h=dict(ev87.edge_angles(h))
    measured={}; all_data={}; any_data={}; kinds=('diag','vertical','horizontal')
    for mode in ('any','all_four'):
        mode_family={}; union=np.zeros(pop.shape,dtype=bool); union_hinges={}
        pooled_b=[]; pooled_h=[]; new_count=0
        for kind in kinds:
            slices=ev87.edge_vertex_slices(pop,kind)
            mask=ev87.incident_any(pop,kind) if mode=='any' else np.logical_and.reduce(slices)
            union |= project_nodes(ev87,mask,kind,pop.shape)
            # Per-family metrics follow EV87's exact summaries and 30-degree comparison.
            vb=np.asarray(a_b[kind][mask],dtype=np.float64); vh=np.asarray(a_h[kind][mask],dtype=np.float64)
            add=int(np.count_nonzero((vb<=30.0+ev87.ANG_TOL)&(vh>30.0+ev87.ANG_TOL)))
            pooled_b.append(vb); pooled_h.append(vh); new_count+=add
            # A hinge is mixed if its 4 corners touch wet support and one dry population.
            has_wet=np.logical_or.reduce(slices)
            has_bank=np.logical_or.reduce(ev87.edge_vertex_slices(pops['bank'],kind))
            has_interior=np.logical_or.reduce(ev87.edge_vertex_slices(pops['interior'],kind))
            mode_family[kind]={'hinges':int(mask.sum()),'B':ev87.summaries([vb]),'H':ev87.summaries([vh]),
                'new_over30':add,
                'hinges_touching_bank':int(np.count_nonzero(mask & has_bank)),
                'hinges_touching_interior':int(np.count_nonzero(mask & has_interior)),
                'mixed_wet_bank':int(np.count_nonzero(mask & has_wet & has_bank)),
                'mixed_wet_interior':int(np.count_nonzero(mask & has_wet & has_interior))}
            union_hinges[kind]=mask
        pb=np.concatenate(pooled_b); ph=np.concatenate(pooled_h)
        mode_data={'hinges_by_family':mode_family,'B':ev87.summaries(pooled_b),'H':ev87.summaries(pooled_h),
                   'new_over30_count':new_count,'measured_node_union':int(union.sum()),
                   'measured_wet_support_nodes':int(np.count_nonzero(union & pop)),
                   'measured_nodes_by_population':{name:int(np.count_nonzero(union & mask)) for name,mask in categories.items()},
                   'hinge_count_total':int(sum(x['hinges'] for x in mode_family.values()))}
        measured[mode]=union; all_data[mode]=mode_family
        if mode=='any': any_data=mode_data
        else: all_data['all_four_aggregate']=mode_data
    # Compare hinge-level sets and explicitly quantify the extra ANY coverage.
    comparison={}
    any_union=measured['any']; all_union=measured['all_four']
    for kind in kinds:
        s=ev87.edge_vertex_slices(pop,kind)
        anym=ev87.incident_any(pop,kind); allm=np.logical_and.reduce(s)
        comparison[kind]={'any_hinges':int(anym.sum()),'all_four_hinges':int(allm.sum()),
                          'any_only_hinges':int(np.count_nonzero(anym & ~allm)),
                          'any_union_nodes':int(project_nodes(ev87,anym,kind,pop.shape).sum()),
                          'all_four_union_nodes':int(project_nodes(ev87,allm,kind,pop.shape).sum())}
    comparison['all_families']={'any_union_nodes':int(any_union.sum()),'all_four_union_nodes':int(all_union.sum()),
       'any_only_union_nodes':int(np.count_nonzero(any_union & ~all_union)),
       'any_measured_wet_support_nodes':int(np.count_nonzero(any_union & pop)),
       'all_four_measured_wet_support_nodes':int(np.count_nonzero(all_union & pop)),
       'any_union_bank_overlap':int(np.count_nonzero(any_union & pops['bank'])),
       'any_union_interior_overlap':int(np.count_nonzero(any_union & pops['interior'])),
       'all_four_union_bank_overlap':int(np.count_nonzero(all_union & pops['bank'])),
       'all_four_union_interior_overlap':int(np.count_nonzero(all_union & pops['interior']))}
    fixture_result=fixture(ev87)
    if not fixture_result['pass']: raise AssertionError('discrete support fixture failed')
    input_hashes={str(Path(__file__).resolve()):sha(Path(__file__).resolve()),
                  str(ev91_path):sha(ev91_path),str(candidate):sha(candidate),
                  str(consumer.EV87_PATH):sha(consumer.EV87_PATH),str(consumer.EV88_PATH):sha(consumer.EV88_PATH),
                  str(consumer.POPULATION_RECONCILIATION):sha(consumer.POPULATION_RECONCILIATION),**bundle['hashes']}
    # Close the read set against in-run replacement.
    for p,d in input_hashes.items():
        if sha(p)!=d: raise AssertionError(f'input changed during diagnostic: {p}')
    any_data['p99_nonworse']=any_data['H']['p99']<=any_data['B']['p99']+ev87.ANG_TOL
    any_data['above30_nonworse']=any_data['H']['above30']<=any_data['B']['above30']
    any_data['no_new_over30']=any_data['new_over30_count']==0
    all_data['all_four_aggregate']['p99_nonworse']=all_data['all_four_aggregate']['H']['p99']<=all_data['all_four_aggregate']['B']['p99']+ev87.ANG_TOL
    all_data['all_four_aggregate']['above30_nonworse']=all_data['all_four_aggregate']['H']['above30']<=all_data['all_four_aggregate']['B']['above30']
    all_data['all_four_aggregate']['no_new_over30']=all_data['all_four_aggregate']['new_over30_count']==0
    report={'status':'WET_SUPPORT_INCIDENCE_DIAGNOSTIC_ONLY','python':sys.executable,'python_version':sys.version,
       'input_hashes':input_hashes,'population':{'eligible_wet_support':int(pop.sum()),
       'eligible_wet_support_union_incident_measured_any':int(np.count_nonzero(any_union & pop)),
       'eligible_wet_support_union_incident_measured_all_four':int(np.count_nonzero(all_union & pop)),
       'eligible_wet_support_not_measured_by_any_family':int(np.count_nonzero(pop & ~any_union)),
       'family_comparison':comparison},
       'any_incident':any_data,'all_four_incident':all_data['all_four_aggregate'],
       'discrete_four_vertex_fixture':fixture_result,
       'scope_limit':'Read-only diagnostic on pinned B/H. ANY means a hinge has at least one eligible wet-support corner; angles are the existing EV87 four-vertex hinge metric. This does not assert water/render acceptance, classify every coastal face, or close remaining surface risk.'}
    tmp=OUT_JSON.with_suffix('.json.tmp'); tmp.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8'); tmp.replace(OUT_JSON)
    print(json.dumps({'status':report['status'],'wet_nodes':int(pop.sum()),
      'any_measured_wet_nodes':report['population']['eligible_wet_support_union_incident_measured_any'],
      'all4_measured_wet_nodes':report['population']['eligible_wet_support_union_incident_measured_all_four'],
      'any_hinges':any_data['hinge_count_total'],'all4_hinges':report['all_four_incident']['hinge_count_total'],
      'fixture_pass':fixture_result['pass'],'output':str(OUT_JSON)}))

if __name__=='__main__': main()

