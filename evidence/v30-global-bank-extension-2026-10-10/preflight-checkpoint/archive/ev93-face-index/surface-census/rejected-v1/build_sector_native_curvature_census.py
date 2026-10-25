#!/usr/bin/env python
"""Read-only sector census of every native EV87 B hinge; no authoring."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path

import numpy as np

ROOT=Path(r'E:/DayZ-Baltic-Build')
OUT=ROOT/'v30-global-bank-extension-20261010/ev93-face-index/surface-census'
EV87_PATH=ROOT/'v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py'
EV79=ROOT/'v30-narva-dry-bank-relief-20261010'
PRIOR=ROOT/'v30-remaining-exact-dry-support-20261009/constraints.npz'
EXPECTED={
    'EV87':'964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27',
    'B':'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
    'EV79':'dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c',
    'EV79_CONSTRAINTS':'ad0cffd5f26fc942e17fc959236494287650b1528b728a15f4b1100da72f319c',
    'PRIOR_CONSTRAINTS':'18a3639907a68a8ceda37fe2a402884c2c4bc111fe8c7775d0a7d07dac02d370',
    'P':'768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0',
    'F':'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c',
}
FAMILIES=('diag','vertical','horizontal')
POPULATIONS=('all','any_eligible','any_bank','any_interior','any_wet_support',
             'any_fixed','any_protected','no_eligible','mixed_eligible',
             'all_eligible','any_other_fixed','any_engineering_halo',
             'any_large_lake_banks','any_reserve_or_platform',
             'any_waterline_blocked','any_nonclass0','any_eligible_bank',
             'any_eligible_interior','any_eligible_wet_support')
BITS={name:1<<i for i,name in enumerate(POPULATIONS) if name!='all'}
SECTOR_NODES=64
N=2048


def sha(path:Path)->str:
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()


def load_npz(path:Path)->dict[str,np.ndarray]:
    with np.load(path,allow_pickle=False) as z:return {k:z[k] for k in z.files}


def load_ev87():
    spec=importlib.util.spec_from_file_location('ev87_census_source',EV87_PATH)
    if spec is None or spec.loader is None:raise ImportError(EV87_PATH)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    if sha(EV87_PATH)!=EXPECTED['EV87']:raise AssertionError('EV87 source SHA changed')
    return mod


def verify_inputs(ev87):
    paths={'EV87':EV87_PATH,'B':ev87.B/'candidate/terrain.npz',
        'EV79':ev87.EV79/'candidate/terrain.npz','EV79_CONSTRAINTS':ev87.EV79/'constraints.npz',
        'PRIOR_CONSTRAINTS':PRIOR,'P':ev87.EV79/'candidate/plane.npy',
        'F':ev87.EV79/'candidate/visible-field.npy'}
    actual={key:sha(path) for key,path in paths.items()}
    bad={k:(EXPECTED[k],actual[k]) for k in EXPECTED if actual.get(k)!=EXPECTED[k]}
    if bad:raise AssertionError(f'input identity mismatch: {bad}')
    return paths,actual


def hinge_shape(kind):
    return {'diag':(N-1,N-1),'vertical':(N-1,N-2),
            'horizontal':(N-2,N-1)}[kind]


def incident_any(ev87,mask,kind):
    slices=ev87.edge_vertex_slices(mask,kind)
    return np.logical_or.reduce(slices)


def make_incidence_flags(ev87,kind,vertex_masks):
    groups={name:incident_any(ev87,mask,kind) for name,mask in vertex_masks.items()}
    any_eligible=groups['eligible']
    flags=np.zeros(any_eligible.shape,dtype=np.uint32)
    values={
        'any_eligible':any_eligible,'any_bank':groups['bank'],
        'any_interior':groups['interior'],'any_wet_support':groups['wet_support'],
        'any_fixed':groups['fixed'],'any_protected':groups['protected'],
        'no_eligible':~any_eligible,'mixed_eligible':any_eligible & ~groups['all_eligible'],
        'all_eligible':groups['all_eligible'],'any_other_fixed':groups['other_fixed'],
        'any_engineering_halo':groups['engineering_halo'],
        'any_large_lake_banks':groups['large_lake_banks'],
        'any_reserve_or_platform':groups['reserve_or_platform'],
        'any_waterline_blocked':groups['waterline_blocked'],
        'any_nonclass0':groups['nonclass0'],
        'any_eligible_bank':groups['eligible_bank'],
        'any_eligible_interior':groups['eligible_interior'],
        'any_eligible_wet_support':groups['eligible_wet_support'],
    }
    for name,mask in values.items():flags[mask]|=BITS[name]
    return flags


def population_masks(base,cons,prior,eligible,levels,ev87):
    population=ev87._ev87_populations(base,cons)
    fixed=(cons['other_fixed'].astype(bool)|cons['engineering_halo'].astype(bool))
    protected=(fixed|prior['large_lake_banks'].astype(bool)|base['reserve'].astype(bool)|base['platform'].astype(bool))
    all_eligible=eligible.copy()
    return {
        'eligible':eligible.astype(bool),
        'bank':population['bank'].astype(bool),
        'interior':population['interior'].astype(bool),
        'wet_support':cons['wet_support'].astype(bool),
        'eligible_bank':eligible.astype(bool)&population['bank'].astype(bool),
        'eligible_interior':eligible.astype(bool)&population['interior'].astype(bool),
        'eligible_wet_support':eligible.astype(bool)&cons['wet_support'].astype(bool),
        'other_fixed':cons['other_fixed'].astype(bool),
        'fixed':fixed,
        'protected':protected,
        'all_eligible':all_eligible,
        'engineering_halo':cons['engineering_halo'].astype(bool),
        'large_lake_banks':prior['large_lake_banks'].astype(bool),
        'reserve_or_platform':(base['reserve'].astype(bool)|base['platform'].astype(bool)),
        'waterline_blocked':heights_mask(base,levels),
        'nonclass0':base['cls']!=0,
    }


def heights_mask(base,levels):
    return base['heights'].astype(np.float64)<=np.asarray(levels,dtype=np.float64)


def iter_sector_slices(shape):
    rows,cols=shape
    for sr in range((rows+SECTOR_NODES-1)//SECTOR_NODES):
        r0=sr*SECTOR_NODES;r1=min(r0+SECTOR_NODES,rows)
        for sc in range((cols+SECTOR_NODES-1)//SECTOR_NODES):
            c0=sc*SECTOR_NODES;c1=min(c0+SECTOR_NODES,cols)
            yield sr,sc,(slice(r0,r1),slice(c0,c1))


def aggregate_family(angles,flags,kind):
    rows,cols=angles.shape;nr=(rows+63)//64;nc=(cols+63)//64
    shape=(nr,nc,len(POPULATIONS))
    stats={name:np.zeros(shape,dtype=np.float64) for name in ('mean_deg','mean_square_deg2','max_deg','p99_deg')}
    counts=np.zeros(shape,dtype=np.int64)
    for sr,sc,(rs,cs) in iter_sector_slices(angles.shape):
        a=angles[rs,cs]
        if a.size==0:continue
        if not np.isfinite(a).all() or np.any(a<0):raise AssertionError(f'invalid B angle field {kind} sector={(sr,sc)}')
        local_flags=flags[rs,cs]
        for pi,name in enumerate(POPULATIONS):
            if name=='all':mask=np.ones(a.shape,dtype=bool)
            else:mask=(local_flags & BITS[name])!=0
            v=a[mask]
            if not v.size:continue
            counts[sr,sc,pi]=v.size
            stats['mean_deg'][sr,sc,pi]=float(np.mean(v,dtype=np.float64))
            stats['mean_square_deg2'][sr,sc,pi]=float(np.mean(v.astype(np.float64)**2))
            stats['max_deg'][sr,sc,pi]=float(np.max(v))
            stats['p99_deg'][sr,sc,pi]=float(np.percentile(v,99))
    return counts,stats


def global_stats(angles,flags,kind):
    result={}
    for name in POPULATIONS:
        mask=np.ones(angles.shape,dtype=bool) if name=='all' else (flags & BITS[name])!=0
        v=angles[mask].astype(np.float64)
        if v.size:
            result[name]={'n':int(v.size),'mean_deg':float(np.mean(v)),
                'mean_square_deg2':float(np.mean(v*v)),'max_deg':float(np.max(v)),
                'p99_deg':float(np.percentile(v,99))}
        else:result[name]={'n':0,'mean_deg':None,'mean_square_deg2':None,'max_deg':None,'p99_deg':None}
    return result


def _fixture_any_against_naive(ev87):
    mask=np.zeros((7,8),dtype=bool);mask[2,3]=True;mask[5,6]=True
    shapes={'diag':(6,7),'vertical':(6,6),'horizontal':(5,7)}
    for kind,(rows,cols) in shapes.items():
        fast=incident_any(ev87,mask,kind)
        oracle=np.zeros((rows,cols),dtype=bool)
        for r in range(rows):
            for c in range(cols):
                oracle[r,c]=any(mask[rr,cc] for rr,cc in ev87._ev87_hinge_vertices(kind,r,c))
        if not np.array_equal(fast,oracle):raise AssertionError(f'any-incidence mismatch: {kind}')
    return True


def _fixture_sector_partition():
    for shape in ((130,131),(130,129),(129,131)):
        covered=np.zeros(shape,dtype=np.uint8)
        for _,_,(rs,cs) in iter_sector_slices(shape):covered[rs,cs]+=1
        if not np.all(covered==1):raise AssertionError(f'sector partition omitted/doubled anchors: {shape}')
    return True


def run_fixtures(ev87):
    assert _fixture_any_against_naive(ev87)
    assert _fixture_sector_partition()
    return {'any_incidence_matches_independent_four_vertex_oracle':True,
        '64_anchor_sector_partition_no_omission_or_double_count':True}


def _clean(value):
    if isinstance(value,dict):return {str(k):_clean(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [_clean(x) for x in value]
    if isinstance(value,(np.bool_,)):return bool(value)
    if isinstance(value,(np.integer,)):return int(value)
    if isinstance(value,(np.floating,float)):
        return float(value) if np.isfinite(value) else None
    return value


def run():
    ev87=load_ev87();fixtures=run_fixtures(ev87);paths,inputs=verify_inputs(ev87)
    base=load_npz(paths['B']);cons=load_npz(paths['EV79_CONSTRAINTS']);prior=load_npz(paths['PRIOR_CONSTRAINTS'])
    p=np.load(paths['P'],allow_pickle=False).astype(np.float64)
    f=np.load(paths['F'],allow_pickle=False).astype(np.float64)
    heights=base['heights'].astype(np.float64)
    if heights.shape!=(N,N) or p.shape!=(N-1,N-1) or f.shape!=(N-1,N-1,4):
        raise AssertionError('unexpected B/P/F dimensions')
    eligible,levels=ev87._ev87_eligible(base,cons,prior,heights,p,f)
    masks=population_masks(base,cons,prior,eligible,levels,ev87)
    direct_counts={name:int(np.count_nonzero(mask)) for name,mask in masks.items()}
    if direct_counts['bank']+direct_counts['interior']!=int(np.count_nonzero(masks['bank']|masks['interior'])):
        raise AssertionError('bank/interior overlap contract changed')
    all_angles=dict(ev87.edge_angles(heights))
    if tuple(all_angles)!=FAMILIES:raise AssertionError(f'EV87 hinge family order changed: {tuple(all_angles)}')
    sector_arrays={};family_summaries={};family_totals={};reconciliation={}
    for fi,kind in enumerate(FAMILIES):
        angles=np.asarray(all_angles[kind],dtype=np.float64)
        expected_shape=hinge_shape(kind)
        if angles.shape!=expected_shape:raise AssertionError(f'{kind} shape {angles.shape} != {expected_shape}')
        flags=make_incidence_flags(ev87,kind,masks)
        counts,stats=aggregate_family(angles,flags,kind)
        global_row=global_stats(angles,flags,kind)
        direct_any={name:int(np.count_nonzero(angles_mask)) for name,angles_mask in
            ((n,np.ones(angles.shape,dtype=bool) if n=='all' else (flags&BITS[n])!=0) for n in POPULATIONS)}
        for pi,name in enumerate(POPULATIONS):
            got=int(counts[:,:,pi].sum());want=direct_any[name]
            if got!=want:raise AssertionError(f'sector count does not reconcile {kind}/{name}: {got}!={want}')
            if global_row[name]['n']!=want:raise AssertionError(f'global count does not reconcile {kind}/{name}')
            if name=='all' and got!=int(np.prod(expected_shape)):raise AssertionError(f'hinge partition count wrong: {kind}')
        sector_arrays[f'angle_{kind}']=angles.astype(np.float64)
        sector_arrays[f'incidence_{kind}']=flags
        sector_arrays[f'count_{kind}']=counts
        for metric,arr in stats.items():sector_arrays[f'{metric}_{kind}']=arr
        family_summaries[kind]={'anchor_shape':list(expected_shape),'hinge_count':int(angles.size),
            'sector_shape':list(counts.shape[:2]),'global':global_row,
            'sector_population_counts_sum':{name:int(counts[:,:,pi].sum()) for pi,name in enumerate(POPULATIONS)}}
        family_totals[kind]=int(angles.size)
        reconciliation[kind]={'all_hinges':int(counts[:,:,0].sum()),
            'expected_all_hinges':int(np.prod(expected_shape)),
            'sector_count_reconciliation_all_populations':True}
    arrays_path=OUT/'sector-native-curvature-census.npz'
    summary_path=OUT/'summary.json'
    OUT.mkdir(parents=True,exist_ok=True)
    tmp=arrays_path.with_suffix('.npz.tmp')
    with tmp.open('wb') as stream:np.savez_compressed(stream,**sector_arrays)
    os.replace(tmp,arrays_path)
    output_hash=sha(arrays_path)
    summary={'status':'PASS_OFFLINE_CENSUS','artifact_class':'read-only B baseline census; no candidate comparison or terrain edits',
        'schema':'ev93.sector-native-curvature-census.v1','sources':{'paths':{k:str(v) for k,v in paths.items()},'sha256':inputs},
        'formulas':{'angles':'exact verify_ev87.edge_angles(B.heights); native diag, vertical, horizontal only',
            'incidence':'ANY of the four exact vertices returned by verify_ev87.edge_vertex_slices',
            'sector_assignment':'hinge-array anchor (r,c) belongs to (r//64,c//64); closed partition over each family anchor array; no derived border hinges; a hinge crossing a sector boundary is counted once at its anchor and retains its full four-vertex incidence',
            'mean_square':'mean(theta_deg**2)','p99':'numpy percentile default linear interpolation','angle_units':'degrees'},
        'scope':{'map_vertices':list(heights.shape),'native_cell_m':float(ev87.CELL),
            'sector_anchor_nodes':SECTOR_NODES,'sector_size_m':SECTOR_NODES*float(ev87.CELL),
            'population_vertex_counts':direct_counts,'incidence_populations':list(POPULATIONS),
            'incidence_bit_flags':BITS,
            'wet_support_is_diagnostic_population_not_selector_veto':True,
            'separate_3m_grid_input_present':False,'claim':'all native B hinge anchors counted once by family; eligibility/property categories are incidence-ANY, overlapping unless noted'},
        'family_order':list(FAMILIES),'families':family_summaries,'hinge_totals':family_totals,
        'reconciliation':reconciliation,'fixtures':fixtures,
        'output':{'npz':str(arrays_path),'sha256':output_hash,'bytes':arrays_path.stat().st_size,
            'summary':str(summary_path)}}
    summary_path.write_text(json.dumps(_clean(summary),indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    if args.self_test:
        print(json.dumps({'status':'PASS_FIXTURES','fixtures':run_fixtures(load_ev87())},indent=2))
        raise SystemExit(0)
    result=run()
    print(json.dumps({'status':result['status'],'hinge_totals':result['hinge_totals'],
        'eligible_vertices':result['scope']['population_vertex_counts']['eligible'],
        'output_sha256':result['output']['sha256'],'output_bytes':result['output']['bytes']},indent=2))
