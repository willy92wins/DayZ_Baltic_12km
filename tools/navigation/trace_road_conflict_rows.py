"""Reproduce only raw identities of a certified V16 conflict, never solve/edit."""
from pathlib import Path
import hashlib,inspect,json
import numpy as np
from scipy.sparse import load_npz
import refine_road_network_v16 as producer
ROOT=Path(__file__).resolve().parents[2];FOLDER=ROOT/'tests/regional_road_network_v16';OUT=FOLDER/'conflict-row-trace'

def main():
    source=Path(producer.__file__)
    assert hashlib.sha256(source.read_bytes()).hexdigest()=='92640b4a25e3bc8037fc9d62ebe775232b31fb66ad1051a9a0db3e6cf6cb98de'
    assert not OUT.exists()
    certificate=np.load(FOLDER/'cap-certificate-scan/certificate-00.npz');wanted=set(np.flatnonzero(certificate['ray']))
    B=load_npz(FOLDER/'constraints.npz');original=np.load(FOLDER/'variables.npz')
    records=[]
    def capture(row,indices,coefficients,limit,prior,mapping):
        if row not in wanted:return
        row=int(row);indices=np.asarray(indices);coefficients=np.asarray(coefficients);expected=B.getrow(row)
        actual={}
        for vertex,coefficient in zip(indices,coefficients):
            column=mapping[vertex]
            if column>=0 and abs(coefficient)>1e-14:actual[int(column)]=actual.get(int(column),0)+float(coefficient)
        recorded=dict(zip(map(int,expected.indices),map(float,expected.data)))
        assert all(abs(actual.get(k,0)-recorded.get(k,0))<1e-12 for k in actual.keys()|recorded.keys()),row
        rhs=float(limit-coefficients@prior[indices]);assert abs(rhs-original['rhs'][row])<1e-12,row
        records.append(dict(row=row,limit=float(limit),rhs=rhs,vertices=[dict(index=int(v),x_m=int(v%2048*6),z_m=int(12282-v//2048*6),height=float(prior[v]),coefficient=float(c),editable=bool(mapping[v]>=0)) for v,c in zip(indices,coefficients)]))
    code=inspect.getsource(producer.main)
    begin=code.index('    def bound(ix,w,limit):');end=code.index('    retained_total=',begin)
    code=code[:begin]+'''    def bound(ix,w,limit):
        row=len(rhs);rhs.append(0.)
        capture(row,ix,w,limit,prior,mapping)
'''+code[end:]
    code=code[:code.index('    B=coo_matrix(')]+'''    assert len(rhs)==expected_rows
    assert {r['row'] for r in records}==wanted
    (OUT/'trace.json').write_text(json.dumps(dict(status='EXACT_ROWS_MATCH_FROZEN_MATRIX',records=records),indent=2)+'\\n',encoding='utf-8')
    print(json.dumps(dict(status='EXACT_ROWS_MATCH_FROZEN_MATRIX',rows=len(records))))
'''
    scope=dict(vars(producer),OUT=OUT,capture=capture,records=records,wanted=wanted,expected_rows=B.shape[0])
    exec(compile(code,str(source)+' [read-only trace]','exec'),scope);scope['main']()

if __name__=='__main__':main()
