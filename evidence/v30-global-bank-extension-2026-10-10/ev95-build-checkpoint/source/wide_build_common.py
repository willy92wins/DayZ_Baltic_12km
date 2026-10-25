"""Fail-closed EV95 wide-slope acceptance; offline evidence only."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json
from pathlib import Path
import numpy as np

G=Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010')
EV82=Path(r'E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010')
EV87_BUILD=Path(r'E:/DayZ-Baltic-Build/v30-global-strict-bank-relief-20261010/build')
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
ROOT=G/'global-operator-prototype/real-sector-preflight/ev94-rebase/slope-bound'
FOCUS=G/'global-operator-prototype/real-sector-preflight/focus-unit'
COMPOSITION=ROOT/'composition-run-01/composition.json'
COMPOSITION_SHA='db732d229c0d7c13961355ca80e704a2bfe3fede5ac3eef2d01c80af065b0c67'
COMPOSER=ROOT/'compose_verified_sector.py'
COMPOSER_SHA='bf7d32204caa8b83e1f5dcb3e8eeb1c65aa83af438a8e966a4d9804f293c6860'
CONSUMER=ROOT/'verify_slope_bound.py'
CONSUMER_SHA='d111772e9584f09384e6bb912a55fa6e62cb823c808818fc5a8d9d4328ec38b0'
CONSUMER_REPORT=ROOT/'consumer/full-run-01.json'
CONSUMER_REPORT_SHA='b0b7c872746002d11a6fc44228d7d6901bf936efc42e5156b5e77293ba84fe47'
LOCAL=ROOT/'solve-run-01/candidate-local.npz'
LOCAL_SHA='88f945b2b58a0def288693d3171c6ee8b10179c04b2ca48fc125e8458b9004e6'
WIDE_CANDIDATE=ROOT/'composition-run-01/terrain.npz'
WIDE_CANDIDATE_SHA='40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a'
FOCAL_CANDIDATE=FOCUS/'author-run-01/candidate-terrain.npz'
FOCAL_SHA='30d0ed33e477846297a17e758e34a51490d54ee809e8b63ec9d69229170d15a1'
FOCAL_COMPOSITION=FOCUS/'composition-run-01/review.json'
FOCAL_SUPPLEMENT=FOCUS/'consumer-run-01/acceptance-supplement.json'
FOCAL_COMMON=G/'build-focal/focal_build_common.py'
FOCAL_COMMON_SHA='30626759986c91780028e945538bd3427e909872f9f3da070560b0571d5bc3d4'
BASE_ADDONS=Path(r'P:/Mods/@DayZ_Baltic_IncrementalBankPreviewV1/Addons')
PREVIEW_MOD=Path(r'P:/Mods/@DayZ_Baltic_EV95_WideBankPreviewV1')
WORLD_PBO_SHA='b11c825b6c14ecc5649ac668b40c7dc6c9f52c64c26ddfa748983c04b340c36c'
WATER_PBO_SHA='3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14'
BASE_TERRAIN_SHA='f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0'
BASE_WATER_PLANE_SHA='768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0'
BASE_VISIBLE_FIELD_SHA='f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c'
BASE_SOURCE_WRP_SHA='3071395e2d1830f1c5c28bd84346761b5c517710e9d5f1f4ac19cd3fc1eff1f6'
BASE_COMPILED_WRP_SHA='3b12b21d554c6ab75d76c43b5ba902c9a1d49a26516bdd14b16f1a6048ba2539'
BASE_REFERENCE_INPUTS_SHA='feb562be42082cdd3749242d470330947a7a299b0c983df26b39b8b436a8216c'
EV82_SURFACE_HELPER_SHA='e4cdc3fd50b49ed8d66f32c13e84655cc2796b8d5a52b9c01cbcf5881c245f08'
EV82_NATIVE_VERIFIER_SHA='be9a531e9ca1fdd663ebe4064345f821b2fb185d0c2e0479522d834cc1689f0c'
GATES={
'fresh_pending_solve_and_resources','independent_domain_matrices_bounds_rebuilt',
'independent_baseline_C_and_order_feasible','independent_kkt_closure_objective',
'float32_bounds_and_D8','scalar_slope_face_bounded_from_baseline',
'retained_499_windows_halo2_and_focus_exact','water_civil_P9_exact',
'P_F_SEA_signs_crossings_within_1m','no_new_local_minima',
'slope_hinge_global_nonregression','bank_interior_p99_nonworse',
'corridor_geometry_covered','known_P_depth_ge_0_95','unknown_P_preserved',
'high_navigable_bed_floor_1m','seed_improved'}
CONTEXT=(710,970,240,500)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''): h.update(block)
    return h.hexdigest()
def blob_sha(data): return hashlib.sha256(data).hexdigest()
def read_json(path):
    obj=json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if not isinstance(obj,dict): raise ValueError(f'Expected JSON object: {path}')
    return obj
def _same_path(value, expected, label):
    p=Path(value).resolve()
    if p!=Path(expected).resolve(): raise ValueError(f'{label} path mismatch: {p}')
    return p
def _verify_map(mapping,label):
    if not isinstance(mapping,dict) or not mapping: raise ValueError(f'{label} empty')
    for raw,digest in mapping.items():
        p=Path(raw)
        if not p.is_file() or sha(p)!=digest: raise ValueError(f'{label} hash mismatch: {p}')
    return mapping
def _rehash_report_readsets(info):
    groups=('source_hashes_start','source_hashes_end','artifact_hashes_start','artifact_hashes_end','consumer_static_hashes_start','consumer_static_hashes_end','solve_hashes_start','solve_hashes_end')
    normalized={}
    for key in groups:
        value=info.get(key)
        if not isinstance(value,dict) or not value: raise ValueError(f'Missing report readset {key}')
        _verify_map(value,key)
        normalized[key]=value
    for before,after in (('source_hashes_start','source_hashes_end'),('artifact_hashes_start','artifact_hashes_end'),('consumer_static_hashes_start','consumer_static_hashes_end'),('solve_hashes_start','solve_hashes_end')):
        if normalized[before]!=normalized[after]: raise ValueError(f'Report readset drift: {before}/{after}')
    return normalized
def acceptance_args(parser):
    parser.add_argument('--composition-receipt',type=Path,required=True)
def verify_baseline_pbos():
    if sha(BASE_ADDONS/'narva_trial.pbo')!=WORLD_PBO_SHA: raise ValueError('Baseline world PBO mismatch')
    if sha(BASE_ADDONS/'baltic_water_v30.pbo')!=WATER_PBO_SHA: raise ValueError('Baseline water PBO mismatch')
def verify_baseline_reference_inputs():
    p=EV87_BUILD/'reference-inputs.json'
    if sha(p)!=BASE_REFERENCE_INPUTS_SHA: raise ValueError('Baseline reference-inputs hash mismatch')
    r=read_json(p)
    if not (r.get('status')=='PASS_EV82_COMPOSITE_REFERENCE' and r.get('world_sha256')==WORLD_PBO_SHA and r.get('water_sha256')==WATER_PBO_SHA and r.get('compiled_wrp_sha256')==BASE_COMPILED_WRP_SHA and r.get('source_terrain_sha256')==BASE_TERRAIN_SHA and r.get('entries')==6827):
        raise ValueError('Baseline reference inputs identity mismatch')
    return p

def _load_npz(path):
    with np.load(path,allow_pickle=False) as z: return {k:z[k].copy() for k in z.files}
def _load_focal_accepted():
    if sha(FOCAL_COMMON)!=FOCAL_COMMON_SHA: raise ValueError('Reviewed focal common source changed')
    spec=importlib.util.spec_from_file_location('reviewed_wide_build_common',FOCAL_COMMON)
    if spec is None or spec.loader is None: raise RuntimeError('Cannot load reviewed focal acceptance helper')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod.load_accepted_inputs(FOCAL_COMPOSITION,FOCAL_SUPPLEMENT)

def load_accepted_inputs(receipt_path:Path):
    receipt_path=receipt_path.resolve()
    if receipt_path!=COMPOSITION or sha(receipt_path)!=COMPOSITION_SHA: raise ValueError('Wide composition receipt path/SHA mismatch')
    r=read_json(receipt_path)
    if r.get('status')!='PASS_EXACT_FULL_GRID_COMPOSITION_OFFLINE' or r.get('map_status')!='OPEN_INHERITED_MAP_DEFECTS' or r.get('native_acceptance') is not False or r.get('visual_acceptance') is not False: raise ValueError('Composition status/scope invalid')
    if r.get('metadata_byte_exact') is not True or r.get('outside_declared_nodes_byte_exact') is not True or r.get('sparse_readback_exact') is not True or r.get('compiled_water_corners_preserved_by_consumer') is not True: raise ValueError('Composition exactness claims missing')
    if r.get('consumer_source_sha256')!=CONSUMER_SHA or sha(CONSUMER)!=CONSUMER_SHA: raise ValueError('Full consumer source identity mismatch')
    if sha(COMPOSER)!=COMPOSER_SHA or r.get('composer')!={'path':str(COMPOSER),'sha256':COMPOSER_SHA}: raise ValueError('Composition source identity mismatch')
    report_ref=r.get('independent_report',{})
    if _same_path(report_ref.get('path',''),CONSUMER_REPORT,'Independent report')!=CONSUMER_REPORT or report_ref.get('sha256')!=CONSUMER_REPORT_SHA or sha(CONSUMER_REPORT)!=CONSUMER_REPORT_SHA: raise ValueError('Consumer report path/SHA mismatch')
    report=read_json(CONSUMER_REPORT)
    if report.get('status')!='PASS_EV94_REBASE_SECTOR_OFFLINE_OPEN_P_UNKNOWN' or _same_path(report.get('consumer_path',''),CONSUMER,'Consumer path')!=CONSUMER or report.get('consumer_sha256')!=CONSUMER_SHA: raise ValueError('Consumer report identity/status mismatch')
    gates=report.get('gates')
    if not isinstance(gates,dict) or set(gates)!=GATES or any(value is not True for value in gates.values()): raise ValueError('Exact 17-gate acceptance set did not pass')
    info=report.get('information')
    if not isinstance(info,dict) or info.get('candidate_sha256')!=LOCAL_SHA or info.get('base_sha256')!=FOCAL_SHA or info.get('changed_vertices')!=35991: raise ValueError('Consumer report candidate/base/count mismatch')
    if report_ref.get('status')!=report.get('status'): raise ValueError('Receipt/report status mismatch')
    readsets=_rehash_report_readsets(info)
    if sha(LOCAL)!=LOCAL_SHA or sha(FOCAL_CANDIDATE)!=FOCAL_SHA: raise ValueError('Sector or focal candidate changed')
    focal=_load_focal_accepted()
    if focal['candidate_sha256']!=FOCAL_SHA or focal['retained_units']!=499: raise ValueError('Focal composition chain no longer passes pinned acceptance')
    base_ref=r.get('base',{}); local_ref=r.get('local',{}); candidate_ref=r.get('candidate',{})
    if _same_path(base_ref.get('path',''),FOCAL_CANDIDATE,'Composition base')!=FOCAL_CANDIDATE or base_ref.get('sha256')!=FOCAL_SHA: raise ValueError('Receipt focal base ref mismatch')
    if _same_path(local_ref.get('path',''),LOCAL,'Local candidate')!=LOCAL or local_ref.get('sha256')!=LOCAL_SHA: raise ValueError('Receipt local candidate ref mismatch')
    candidate=_same_path(candidate_ref.get('path',''),WIDE_CANDIDATE,'Composed full candidate')
    if candidate_ref.get('sha256')!=WIDE_CANDIDATE_SHA or candidate.stat().st_size!=candidate_ref.get('bytes') or sha(candidate)!=WIDE_CANDIDATE_SHA: raise ValueError('Composed candidate identity mismatch')
    f=_load_npz(FOCAL_CANDIDATE); local=_load_npz(LOCAL); full=_load_npz(candidate); ev82=_load_npz(EV82/'candidate/terrain.npz')
    if set(f)!=set(full) or set(f)!=set(ev82): raise ValueError('Full candidate archive keys differ from focal/B')
    if set(local)!={'candidate','base','nodes_local'}: raise ValueError('Unexpected local candidate schema')
    r0,r1,c0,c1=CONTEXT
    if local['candidate'].dtype!=np.float32 or local['base'].dtype!=np.float32 or local['candidate'].shape!=(260,260) or local['base'].shape!=(260,260): raise ValueError('Local candidate shape/dtype mismatch')
    if not np.array_equal(local['base'],f['heights'][r0:r1,c0:c1]): raise ValueError('Local solve base is not exact focal context')
    nodes=local['nodes_local']
    if nodes.dtype!=np.int32 or nodes.ndim!=2 or nodes.shape[1]!=2 or len({tuple(map(int,x)) for x in nodes})!=len(nodes): raise ValueError('Local node declaration invalid/duplicated')
    local_changed=np.argwhere(local['candidate']!=local['base'])
    declared={tuple(map(int,x)) for x in nodes}
    if any(tuple(map(int,x)) not in declared for x in local_changed): raise ValueError('Local candidate changed outside declared solver nodes')
    if len(local_changed)!=35991: raise ValueError('Local changed-node count differs from consumer')
    expect=f['heights'].copy(); expect[r0:r1,c0:c1]=local['candidate']
    if full['heights'].dtype!=expect.dtype or full['heights'].shape!=expect.shape or full['heights'].tobytes()!=expect.tobytes(): raise ValueError('Full heights do not equal focal+local composition')
    for name in f:
        if name=='heights': continue
        if full[name].dtype!=f[name].dtype or full[name].shape!=f[name].shape or full[name].tobytes()!=f[name].tobytes(): raise ValueError(f'Composition changed non-height metadata: {name}')
        if ev82[name].dtype!=f[name].dtype or ev82[name].shape!=f[name].shape or ev82[name].tobytes()!=f[name].tobytes(): raise ValueError(f'Focal metadata differs from EV82 B: {name}')
    if full['heights'][840,370]!=f['heights'][840,370]: raise ValueError('Focal improvement was overwritten')
    changed_vs_b=int(np.count_nonzero(full['heights']!=ev82['heights']))
    if changed_vs_b<=0: raise ValueError('Wide candidate is a no-op against EV82 B')
    # Final TOCTOU rehash: source report maps and all linked candidates still match.
    _rehash_report_readsets(info)
    if sha(receipt_path)!=COMPOSITION_SHA or sha(CONSUMER_REPORT)!=CONSUMER_REPORT_SHA or sha(candidate)!=WIDE_CANDIDATE_SHA or sha(LOCAL)!=LOCAL_SHA or sha(FOCAL_CANDIDATE)!=FOCAL_SHA:
        raise ValueError('Wide composition readset changed during validation')
    return {'composition_report_path':receipt_path,'composition_report_sha256':COMPOSITION_SHA,
        'composition_source_path':COMPOSER,'composition_source_sha256':COMPOSER_SHA,
        'consumer_report_path':CONSUMER_REPORT,'consumer_report_sha256':CONSUMER_REPORT_SHA,
        'consumer_source_path':CONSUMER,'consumer_source_sha256':CONSUMER_SHA,
        'receipt_sha256':COMPOSITION_SHA,'composition_receipt_sha256':COMPOSITION_SHA,
        'candidate_path':candidate,'candidate_sha256':WIDE_CANDIDATE_SHA,
        'base_candidate_path':FOCAL_CANDIDATE,'base_candidate_sha256':FOCAL_SHA,
        'local_candidate_path':LOCAL,'local_candidate_sha256':LOCAL_SHA,
        'changed_vertices':changed_vs_b,'changed_local_vs_focal':len(local_changed),
        'retained_units':499,'readset_files':sum(len(v) for v in readsets.values()),
        'readsets':readsets,'receipt':r,'report':report}

def add_acceptance_manifest(target,accepted):
    target.update({'ev95_composition_receipt':str(accepted['composition_report_path']),
        'ev95_composition_receipt_sha256':accepted['composition_report_sha256'],
        'ev95_composition_source':str(accepted['composition_source_path']),
        'ev95_composition_source_sha256':accepted['composition_source_sha256'],
        'ev95_sector_report':str(accepted['consumer_report_path']),
        'ev95_sector_report_sha256':accepted['consumer_report_sha256'],
        'ev95_sector_consumer':str(accepted['consumer_source_path']),
        'ev95_sector_consumer_sha256':accepted['consumer_source_sha256'],
        'ev95_focal_base_sha256':accepted['base_candidate_sha256'],
        'ev95_local_candidate_sha256':accepted['local_candidate_sha256'],
        'ev95_candidate':str(accepted['candidate_path']),
        'ev95_candidate_sha256':accepted['candidate_sha256'],
        'ev95_changed_vertices_vs_EV82_B':accepted['changed_vertices'],
        'ev95_changed_local_vs_focal':accepted['changed_local_vs_focal'],
        'baseline_world_pbo_sha256':WORLD_PBO_SHA,'baseline_water_pbo_sha256':WATER_PBO_SHA,
        'baseline_terrain_sha256':BASE_TERRAIN_SHA,'baseline_water_plane_sha256':BASE_WATER_PLANE_SHA,
        'baseline_visible_field_sha256':BASE_VISIBLE_FIELD_SHA,
        'status_scope':'EV95 isolated wide slope-bound preview; inherited map defects and unknown-P status remain open; no promotion'} )
    return target
EV87_NATIVE_V2_VERIFIER_SOURCE_SHA = EV82_NATIVE_VERIFIER_SHA

