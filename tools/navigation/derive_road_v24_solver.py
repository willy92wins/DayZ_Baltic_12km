"""Derive a bounded V24 worker from the hash-pinned existing road solver."""
from pathlib import Path
import hashlib

ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'tools/navigation/solve_road_network_v23.py'
target=ROOT/'tools/navigation/solve_road_network_v24.py'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='9682b93293eb9d2b54195d7693f3e80d42a743b0cd95577928a14b43add1b89e'
assert not target.exists()
code=source.read_text()
replacements={
    'frozen V22 row':'frozen V24 row',
    "SOURCE=ROOT/'tests/regional_road_network_v22_constraints'":"SOURCE=ROOT/'tests/regional_road_network_v24_constraints'",
    "OUT=ROOT/'tests/regional_road_network_v23'":"OUT=ROOT/'tests/regional_road_network_v24'",
    "assert frozen['local_transition']==dict(bounds_xz=[4278,6876,4572,7008],transition_m=48.,maximum_geographic_distance_m=60.5)":"assert frozen['lateral_transition_m']==48. and frozen['maximum_geographic_distance_m']==60.5",
    "parent=ROOT/'tests/regional_foundation_combined_v10/reference.npz'":"parent=ROOT/'tests/regional_outline_smoothing_v33/reference.npz'",
    "assert sha(parent)=='a43cb0f128c17318207a114f94f08801ff35a81af5d36a4b7e3427dd3d6aca2d'":"assert sha(parent)=='8e84d5ce38da8863116c52ecdf9953d5b201a097459513054eea8e0f0e14c45a'",
    "cap=6.;floor=data['floor'];lo=np.maximum(-cap,floor);hi=np.full(n,cap);active=np.union1d(np.flatnonzero(-rhs>1e-8),np.load(ROOT/'tests/regional_road_network_v22/certificate.npz')['active_rows'])":"""cap=6.;floor=data['floor']
    original=ROOT/'tests/regional_foundation_combined_v10/reference.npz'
    assert sha(original)=='a43cb0f128c17318207a114f94f08801ff35a81af5d36a4b7e3427dd3d6aca2d'
    v10=np.load(original)['candidate'].ravel()[ix].astype(float);current=h.ravel()[ix].astype(float)
    lo=np.maximum.reduce([np.full(n,-cap),floor,v10-cap-current]);hi=np.minimum(cap,v10+cap-current)
    assert np.all(lo<=hi)
    active=np.flatnonzero(-rhs>1e-8)""",
    "margin=lambda c:float(np.maximum(combined,0)@np.maximum(-c,floor)+np.minimum(combined,0).sum()*c-bound)":"margin=float(np.maximum(combined,0)@lo+np.minimum(combined,0)@hi-bound)",
    'and margin(cap)>1e-7':'and margin>1e-7',
    'certificate_margin=margin(cap)':'certificate_margin=margin',
    "baltic_road_network_v23.asc":"baltic_road_network_v24.asc",
}
for old,new in replacements.items():
    assert code.count(old)==1,old
    code=code.replace(old,new)
start=code.index('                if valid and margin(50)<=0:')
end=code.index('                used=np.flatnonzero',start)
code=code[:start]+code[end:]
target.write_text(code,encoding='utf-8')
print(target)
