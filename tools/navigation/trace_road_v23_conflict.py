"""Trace the V23 certificate back to exact V22 rows and fixed terrain vertices."""
from pathlib import Path
import hashlib,inspect,json
import numpy as np
from scipy.sparse import load_npz
from scipy.ndimage import distance_transform_edt
from shapely.geometry import LineString,Point
from shapely import STRtree
import refine_road_network_v16 as producer
ROOT=Path(__file__).resolve().parents[2];FOLDER=ROOT/'tests/regional_road_network_v22_constraints';OUT=FOLDER/'conflict-v23-trace'

def main():
    source=Path(producer.__file__)
    assert hashlib.sha256(source.read_bytes()).hexdigest()=='92640b4a25e3bc8037fc9d62ebe775232b31fb66ad1051a9a0db3e6cf6cb98de'
    assert not OUT.exists()
    cert=np.load(ROOT/'tests/regional_road_network_v23/certificate.npz');active=cert['active_rows'];ray=cert['ray']
    assert np.max(abs(ray[len(active):]))<1e-9,'L1 auxiliary rows need separate trace'
    weights={int(active[i]):float(ray[i]) for i in np.flatnonzero(abs(ray[:len(active)])>1e-12)};wanted=set(weights)
    B=load_npz(FOLDER/'constraints.npz');original=np.load(FOLDER/'variables.npz');original_rhs=original['rhs'];records=[]
    def capture(row,indices,coefficients,limit,prior,mapping):
        if row not in wanted:return
        row=int(row);indices=np.asarray(indices);coefficients=np.asarray(coefficients);expected=B.getrow(row);actual={}
        for vertex,coefficient in zip(indices,coefficients):
            column=mapping[vertex]
            if column>=0 and abs(coefficient)>1e-14:actual[int(column)]=actual.get(int(column),0)+float(coefficient)
        recorded=dict(zip(map(int,expected.indices),map(float,expected.data)))
        assert all(abs(actual.get(k,0)-recorded.get(k,0))<1e-12 for k in actual.keys()|recorded.keys()),row
        rhs=float(limit-coefficients@prior[indices]);assert abs(rhs-original_rhs[row])<1e-12,row
        records.append(dict(row=row,weight=weights[row],limit=float(limit),rhs=rhs,vertices=[dict(index=int(v),x_m=int(v%2048*6),z_m=int(12282-v//2048*6),height=float(prior[v]),coefficient=float(c),editable=bool(mapping[v]>=0)) for v,c in zip(indices,coefficients)]))
    code=inspect.getsource(producer.main)
    before='support=(distance_transform_edt(~support)*6<=12)&allowed';assert code.count(before)==1
    code=code.replace(before,'''core_distance=distance_transform_edt(~support)*6
    local=(cc*6>=4278)&(cc*6<=4572)&(12282-rr*6>=6876)&(12282-rr*6<=7008)
    np.savez_compressed(OUT/'road-triangles-cache.npz',triangles=np.asarray(list(polygons),dtype=np.int16))
    support=((core_distance<=24)|((core_distance<=48)&local))&allowed''')
    begin=code.index('    def bound(ix,w,limit):');end=code.index('    retained_total=',begin)
    code=code[:begin]+'''    def bound(ix,w,limit):
        row=len(rhs);rhs.append(0.)
        capture(row,ix,w,limit,prior,mapping)
'''+code[end:]
    code=code[:code.index('    B=coo_matrix(')]+'''    assert len(rhs)==expected_rows
    assert {r['row'] for r in records}==wanted
    (OUT/'trace.json').write_text(json.dumps(dict(status='EXACT_ROWS_MATCH_FROZEN_MATRIX',records=records),indent=2)+'\\n',encoding='utf-8')
'''
    scope=dict(vars(producer),OUT=OUT,capture=capture,records=records,wanted=wanted,expected_rows=B.shape[0])
    exec(compile(code,str(source)+' [V23 read-only trace]','exec'),scope);scope['main']()
    fixed={}
    for record in records:
        for vertex in record['vertices']:
            if vertex['editable']:continue
            ident=vertex['index']
            if ident not in fixed:fixed[ident]=dict(vertex,combined_coefficient=0.)
            fixed[ident]['combined_coefficient']+=record['weight']*vertex['coefficient']
    ref=np.load(ROOT/'tests/regional_foundation_combined_v10/reference.npz');wetdist=distance_transform_edt(~(ref['wet']|ref['ocean']))*6;fairway=ref['fairway_support']
    routes=json.loads((FOLDER/'build-receipt.json').read_text(encoding='utf-8'))['routes'];lines=np.array([LineString(r['source_polyline']) for r in routes],dtype=object);tree=STRtree(lines)
    vertices=[]
    for value in fixed.values():
        if abs(value['combined_coefficient'])<1e-9:continue
        r,c=divmod(value['index'],2048);point=Point(value['x_m'],value['z_m']);nearest=lines[tree.nearest(point)]
        value.update(wet_distance_m=float(wetdist[r,c]),fairway=bool(fairway[r,c]),source_road_distance_m=float(point.distance(nearest)));vertices.append(value)
    report=dict(status='EXACT_CERTIFICATE_FIXED_BOUNDARY_TRACE',rows=len(records),fixed_vertices=vertices,limit='Source-centerline distance is descriptive; no support or terrain changes authorized by this trace alone.')
    (OUT/'fixed-boundary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))

if __name__=='__main__':main()
