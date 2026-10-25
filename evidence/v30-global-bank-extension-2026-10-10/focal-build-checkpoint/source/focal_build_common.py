"""Fail-closed focal EV94 acceptance; validates offline evidence only."""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path

G = Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010')
EV82 = Path(r'E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010')
EV87_BUILD = Path(r'E:/DayZ-Baltic-Build/v30-global-strict-bank-relief-20261010/build')
FOCUS = G / 'global-operator-prototype/real-sector-preflight/focus-unit'
COMPOSITION_SOURCE = FOCUS / 'verify_focal_composition.py'
COMPOSITION_SOURCE_SHA = 'e5228392386606e495579f28b1cfa8ecd6d58aff1eb9f2967f4480e8440aecb2'
COMPOSITION_REPORT_SHA = 'a5a5aaa1f1f2c06c646bbd54a41ea8fd89d8dee8ffa14d2e59af4d7bc07b05e3'
SELECTED_GLOBAL_CONSUMER_SHA = '6e661b073e5f27b2475e6b82d75d6a7722d0503a082dcfd51d8f00bd6de9722b'
FOCAL_REPORT_SHA = 'b9af8d77c2efe342b02012af160a1f8cae44d41d5581be21045da8539116de7e'
SUPPLEMENT_SHA = 'fab5c76e2f1a7a5935cf70bfaa08dedd4500411e4c2ac11670dc7fccc4b89e7f'
CANDIDATE_SHA = '30d0ed33e477846297a17e758e34a51490d54ee809e8b63ec9d69229170d15a1'
COMPOSED_BASE_SHA = '6e27557315eb65ecc69052e1ec387304a19f37eaa4f5167ab82fb607f095461d'
BASE_ADDONS = Path(r'P:/Mods/@DayZ_Baltic_IncrementalBankPreviewV1/Addons')
PREVIEW_MOD = Path(r'P:/Mods/@DayZ_Baltic_EV94_FocalBankPreviewV1')
WORLD_PBO_SHA = 'b11c825b6c14ecc5649ac668b40c7dc6c9f52c64c26ddfa748983c04b340c36c'
WATER_PBO_SHA = '3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14'
BASE_TERRAIN_SHA = 'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0'
BASE_WATER_PLANE_SHA = '768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0'
BASE_VISIBLE_FIELD_SHA = 'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c'
BASE_SOURCE_WRP_SHA = '3071395e2d1830f1c5c28bd84346761b5c517710e9d5f1f4ac19cd3fc1eff1f6'
BASE_COMPILED_WRP_SHA = '3b12b21d554c6ab75d76c43b5ba902c9a1d49a26516bdd14b16f1a6048ba2539'
BASE_REFERENCE_INPUTS_SHA = 'feb562be42082cdd3749242d470330947a7a299b0c983df26b39b8b436a8216c'
EV82_SURFACE_HELPER_SHA = 'e4cdc3fd50b49ed8d66f32c13e84655cc2796b8d5a52b9c01cbcf5881c245f08'
EV82_NATIVE_VERIFIER_SHA = 'be9a531e9ca1fdd663ebe4064345f821b2fb185d0c2e0479522d834cc1689f0c'
EV87_NATIVE_V2_VERIFIER_SOURCE_SHA = EV82_NATIVE_VERIFIER_SHA
W = Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')


def sha(path: Path | str) -> str:
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''): h.update(block)
    return h.hexdigest()

def blob_sha(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def read_json(path: Path | str) -> dict:
    value=json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if not isinstance(value,dict): raise ValueError(f'expected JSON object: {path}')
    return value

def acceptance_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--composition-report', type=Path, required=True,
                        help='independent focal composition report; no EV93 selection receipt is accepted')
    parser.add_argument('--focal-supplement', type=Path, required=True,
                        help='36-gate focal offline acceptance supplement')

def _verify_map(readset, label):
    if not isinstance(readset,dict) or not readset: raise ValueError(f'{label} is empty')
    normalized={}
    for raw,want in readset.items():
        p=Path(raw)
        if not p.is_file() or sha(p)!=want: raise ValueError(f'{label} path/SHA mismatch: {p}')
        key=str(p.resolve()).casefold()
        if key in normalized and normalized[key]!=want: raise ValueError(f'{label} aliases disagree: {p}')
        normalized[key]=want
    return normalized

def _same_path(raw, expected, label):
    p=Path(raw).resolve()
    if p != Path(expected).resolve(): raise ValueError(f'{label} path differs: {p}')
    return p

def verify_baseline_pbos() -> None:
    world=BASE_ADDONS/'narva_trial.pbo'; water=BASE_ADDONS/'baltic_water_v30.pbo'
    if sha(world)!=WORLD_PBO_SHA: raise ValueError(f'baseline world PBO changed: {world}')
    if sha(water)!=WATER_PBO_SHA: raise ValueError(f'baseline water PBO changed: {water}')

def verify_baseline_reference_inputs() -> Path:
    path=EV87_BUILD/'reference-inputs.json'
    if sha(path)!=BASE_REFERENCE_INPUTS_SHA: raise ValueError(f'baseline reference input changed: {path}')
    ref=read_json(path)
    if not (ref.get('status')=='PASS_EV82_COMPOSITE_REFERENCE' and ref.get('world_sha256')==WORLD_PBO_SHA and
            ref.get('water_sha256')==WATER_PBO_SHA and ref.get('compiled_wrp_sha256')==BASE_COMPILED_WRP_SHA and
            ref.get('source_terrain_sha256')==BASE_TERRAIN_SHA and ref.get('entries')==6827):
        raise ValueError('baseline composite reference identity/shape mismatch')
    return path

def load_accepted_inputs(report_path: Path, supplement_path: Path) -> dict:
    report_path=report_path.resolve(); supplement_path=supplement_path.resolve()
    if not report_path.is_file() or not supplement_path.is_file(): raise FileNotFoundError('composition report and focal supplement are required')
    if sha(COMPOSITION_SOURCE)!=COMPOSITION_SOURCE_SHA: raise ValueError('live composition verifier source differs from reviewed freeze')
    if report_path!=FOCUS/'composition-run-01/review.json' or sha(report_path)!=COMPOSITION_REPORT_SHA: raise ValueError('composition report path/SHA is not the frozen run-01 review')
    report=read_json(report_path); supplement=read_json(supplement_path)
    if Path(report.get('report_path','')).resolve()!=report_path: raise ValueError('composition report does not self-identify its output path')
    if report.get('status')!='PASS_FOCAL_COMPOSITION_INCREMENTAL': raise ValueError(f'composition report not PASS: {report.get("status")!r}')
    if report.get('global_contract_status')!='OPEN_INHERITED_MAP_DEFECTS': raise ValueError('composition report must preserve inherited open map status')
    gates=report.get('gates')
    if not isinstance(gates,dict) or not gates or not all(v is True for v in gates.values()): raise ValueError('composition report gates absent or false')
    if report.get('checker_source_sha256')!=COMPOSITION_SOURCE_SHA: raise ValueError('composition checker source pin mismatch')
    if report.get('focal_report_sha256')!=FOCAL_REPORT_SHA: raise ValueError('composition focal report SHA mismatch')
    if report.get('selected_global_consumer_sha256')!=SELECTED_GLOBAL_CONSUMER_SHA: raise ValueError('composition selected global consumer SHA mismatch')
    if Path(report.get('selected_global_consumer_path','')).resolve()!=(G/'crest-extension/verify_selected_composite_v2.py').resolve(): raise ValueError('composition selected global consumer path mismatch')
    if Path(report.get('supplement_path','')).resolve()!=supplement_path or report.get('supplement_sha256')!=SUPPLEMENT_SHA: raise ValueError('composition report does not bind the supplied focal supplement')
    candidate=Path(report.get('candidate_path','')).resolve()
    if candidate.name!='candidate-terrain.npz' or not candidate.is_file() or sha(candidate)!=CANDIDATE_SHA or report.get('candidate_sha256')!=CANDIDATE_SHA:
        raise ValueError('focal composite candidate path/SHA differs from reviewed candidate')
    base=Path(report.get('base_candidate_path','')).resolve()
    if base!=G/'compound-selection/run-02/candidate-terrain.npz' or sha(base)!=COMPOSED_BASE_SHA or report.get('base_candidate_sha256')!=COMPOSED_BASE_SHA:
        raise ValueError('focal composition base candidate differs from selected EV93 candidate')
    if supplement_path!=FOCUS/'consumer-run-01/acceptance-supplement.json' or sha(supplement_path)!=SUPPLEMENT_SHA:
        raise ValueError('focal acceptance supplement path/SHA differs from frozen evidence')
    if supplement.get('schema')!='ev93.focal-acceptance-supplement.v1' or supplement.get('status')!='PASS_FOCAL_DELTA_OFFLINE_COMPLETE_GATESET':
        raise ValueError('focal supplement schema/status is not accepted')
    if supplement.get('candidate_sha256')!=CANDIDATE_SHA or supplement.get('map_status')!='OPEN_INHERITED_MAP_DEFECTS':
        raise ValueError('focal supplement candidate/map status mismatch')
    sg=supplement.get('gates'); extra=supplement.get('additional_checks')
    if not isinstance(sg,dict) or len(sg)!=36 or not all(v is True for v in sg.values()): raise ValueError('focal supplement must carry 36 true gates')
    if not isinstance(extra,dict) or not extra or not all(v is True for v in extra.values()): raise ValueError('focal supplement additional checks absent/false')
    if supplement.get('source_sha256')!='bb5cd1ddc65004654bfce64bda8c57afc4af6ac39e954db92c6c165caa6f73b1': raise ValueError('focal supplement finalizer source pin mismatch')
    focal_path=Path(supplement.get('focal_report_path','')).resolve()
    if not focal_path.is_file() or sha(focal_path)!=FOCAL_REPORT_SHA or supplement.get('focal_report_sha256')!=FOCAL_REPORT_SHA:
        raise ValueError('focal raw consumer report identity mismatch')
    i=report.get('selection_units')
    f=report.get('focal')
    if not isinstance(i,dict) or i.get('retained')!=499 or i.get('legacy')!=332 or i.get('crest')!=167: raise ValueError('composition must retain exact 499-unit composition')
    if not isinstance(f,dict) or f.get('changed_vertices')!=[[840,370]] or f.get('support_cells')!=[[839,369],[839,370],[840,369],[840,370]]:
        raise ValueError('focal delta identity/support mismatch')
    if int(i.get('unique_changed_vertices',-1))!=int(i.get('changed_vertices',-2)): raise ValueError('selected-unit change inventory is not unique')
    changed=int(i['unique_changed_vertices'])+1
    if changed!=30067: raise ValueError(f'composed changed-vertex count mismatch: {changed}')
    start=report.get('source_pins_start'); end=report.get('source_pins_end')
    if not isinstance(start,dict) or not start or start!=end: raise ValueError('composition source pins start/end differ')
    if start.get(str(COMPOSITION_SOURCE.resolve()))!=COMPOSITION_SOURCE_SHA: raise ValueError('composition readset omits checker source pin')
    normalized_pins=_verify_map(start,'composition source pins')
    supplement_sources=supplement.get('source_read_set')
    normalized_supplement=_verify_map(supplement_sources,'focal supplement source set')
    pin_count=len(normalized_pins); supplement_count=len(normalized_supplement)
    for key,digest in normalized_supplement.items():
        if normalized_pins.get(key)!=digest: raise ValueError(f'composition source pins omit/mismatch focal supplement input: {key}')
    source_path=_same_path(report.get('consumer_source_path',''), FOCUS/'verify_focus_1981.py', 'focal consumer source')
    source_sha=report.get('consumer_source_sha256')
    if source_sha!=supplement.get('original_consumer_sha256') or sha(source_path)!=source_sha: raise ValueError('focal consumer source identity mismatch')
    return {'composition_report_path':report_path,'composition_report_sha256':sha(report_path),
        'composition_source_path':COMPOSITION_SOURCE,'composition_source_sha256':COMPOSITION_SOURCE_SHA,
        'supplement_path':supplement_path,'supplement_sha256':SUPPLEMENT_SHA,
        'candidate_path':candidate,'candidate_sha256':CANDIDATE_SHA,
        'base_candidate_path':base,'base_candidate_sha256':COMPOSED_BASE_SHA,
        'consumer_source_path':source_path,'consumer_source_sha256':source_sha,
        'changed_vertices':changed,'retained_units':499,'readset_files':pin_count,
        'supplement_readset_files':supplement_count,'report':report,'supplement':supplement,
        'source_pins':start,
        'receipt_sha256':sha(report_path),'compound_pool_sha256':SUPPLEMENT_SHA,
        'consumer_report_sha256':sha(report_path),'consumer_report_path':report_path,'selector_source_path':COMPOSITION_SOURCE,
        'selector_source_sha256':COMPOSITION_SOURCE_SHA,'consumer_source_path':source_path,
        'consumer_source_sha256':source_sha,'focal_consumer_source_sha256':source_sha,
        'focal_supplement_sha256':SUPPLEMENT_SHA,'consumer_report_path':report_path}

def add_acceptance_manifest(target:dict, accepted:dict)->dict:
    target.update({'ev94_composition_report':str(accepted['composition_report_path']),
        'ev94_composition_report_sha256':accepted['composition_report_sha256'],
        'ev94_composition_source':str(accepted['composition_source_path']),
        'ev94_composition_source_sha256':accepted['composition_source_sha256'],
        'ev94_focal_supplement':str(accepted['supplement_path']),
        'ev94_focal_supplement_sha256':accepted['supplement_sha256'],
        'ev94_focal_candidate':str(accepted['candidate_path']),
        'ev94_candidate_sha256':accepted['candidate_sha256'],
        'ev94_base_candidate_sha256':accepted['base_candidate_sha256'],
        'ev94_focal_consumer_source':str(accepted['consumer_source_path']),
        'ev94_focal_consumer_source_sha256':accepted['consumer_source_sha256'],
        'ev94_composed_changed_vertices':accepted['changed_vertices'],
        'ev94_composition_input_hashes':accepted['source_pins'],
        'baseline_world_pbo_sha256':WORLD_PBO_SHA,'baseline_water_pbo_sha256':WATER_PBO_SHA,
        'baseline_terrain_sha256':BASE_TERRAIN_SHA,'baseline_water_plane_sha256':BASE_WATER_PLANE_SHA,
        'baseline_visible_field_sha256':BASE_VISIBLE_FIELD_SHA,
        'status_scope':'isolated EV94 focal+selected composition preview; inherited map defects remain open; not promoted'} )
    return target










