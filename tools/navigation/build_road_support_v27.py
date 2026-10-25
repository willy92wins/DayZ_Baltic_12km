"""Rebuild the full support from continuous bands, without a stale variable map."""
from pathlib import Path
import hashlib,inspect
import refine_road_network_v16 as source
from road_continuous_coverage import add_bands,add_chords,water_exclusion
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'tests/regional_road_network_v27_constraints'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    path=Path(source.__file__)
    assert sha(path)=='92640b4a25e3bc8037fc9d62ebe775232b31fb66ad1051a9a0db3e6cf6cb98de'
    assert sha(ROOT/'tests/regional_outline_smoothing_v33/reference.npz')=='8e84d5ce38da8863116c52ecdf9953d5b201a097459513054eea8e0f0e14c45a'
    code=inspect.getsource(source.main)
    start=code.index('    for route_number,route in enumerate(routes):')
    stop=code.index('    support=(distance_transform_edt',start)
    code=code[:start]+'    coverage=add_bands(routes,dry,band,touched)\n'+code[stop:]
    start=code.index('    for route in routes:\n',code.index('polygon_count=len(polygons)'))
    stop=code.index('    B=coo_matrix',start)
    code=code[:start]+'    exact_chord_points=add_chords(routes,dry,bound,weights)\n'+code[stop:]
    replacements={
        "source=ROOT/'tests/regional_foundation_combined_v10/reference.npz'":"source=ROOT/'tests/regional_outline_smoothing_v33/reference.npz'",
        '    def dry(p):':'    allowed &= ~water_exclusion(ROOT,sha)\n    def dry(p):',
        'support=(distance_transform_edt(~support)*6<=12)&allowed':'support=(distance_transform_edt(~support)*6<=48)&allowed',
        'maximum_allowed_delta_m=2.05':'maximum_allowed_delta_m=6.0',
        'indices=variables,rhs=rhs,floor=floor,support=support':'indices=variables,rhs=rhs,floor=floor,support=support,allowed=allowed',
    }
    for before,after in replacements.items():
        assert code.count(before)==1,before;code=code.replace(before,after)
    code=code[:code.index('    cap=2.05;matrix=')]+'''    receipt.update(status='FROZEN_CONSTRAINTS_ONLY',lateral_transition_m=48.,maximum_geographic_distance_m=60.5,source_npz='tests/regional_outline_smoothing_v33/reference.npz',original_delta_cap_m=6.,continuous_coverage=coverage,exact_chord_points=exact_chord_points,true_water30m_and_native_faces=True)
    receipt['constraints_sha256']=sha(OUT/'constraints.npz')
    receipt['variables_sha256']=sha(OUT/'variables.npz')
    (OUT/'build-receipt.json').write_text(json.dumps(receipt,indent=2)+'\\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k!='routes'}),flush=True)
'''
    scope=dict(vars(source),OUT=OUT,sha=sha,add_bands=add_bands,add_chords=add_chords,water_exclusion=water_exclusion)
    exec(compile(code,str(path)+' [V27 continuous coverage]','exec'),scope);scope['main']()


if __name__=='__main__':main()
