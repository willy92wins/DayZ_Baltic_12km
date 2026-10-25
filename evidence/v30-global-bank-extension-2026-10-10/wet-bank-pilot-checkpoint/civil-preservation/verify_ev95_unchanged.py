"""Global civil-footprint regression proof for the EV95 source heightfield."""
from pathlib import Path
import hashlib,json,sys
if sys.flags.optimize:raise RuntimeError('Optimized Python would disable evidence assertions')
import numpy as np
ROOT=Path(__file__).resolve().parent
G=ROOT.parent.parent
BASE=Path('E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz')
FINAL=G/'global-operator-prototype/real-sector-preflight/ev94-rebase/slope-bound/composition-run-01/terrain.npz'
MASK=ROOT/'run-01/civil-mask.npz'
PINS={BASE:'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
 FINAL:'40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a',
 MASK:'46faaf22e2cfefc8137e2b555227a985cfe212265694f1bce106281937c9ffe3'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def changed_cells(changed):
    return changed[:-1,:-1]|changed[1:,:-1]|changed[:-1,1:]|changed[1:,1:]
def main():
    out=ROOT/'ev95-civil-preservation.json'
    assert not out.exists(), 'Do not overwrite evidence'
    before={str(p):sha(p) for p in PINS}
    assert all(before[str(p)]==h for p,h in PINS.items())
    with np.load(BASE,allow_pickle=False) as z:b=z['heights']
    with np.load(FINAL,allow_pickle=False) as z:h=z['heights']
    with np.load(MASK,allow_pickle=False) as z:masks={k:z[k] for k in z.files}
    assert b.dtype==h.dtype==np.float32 and b.shape==h.shape==(2048,2048)
    changed=b.view(np.uint32)!=h.view(np.uint32)
    cells=changed_cells(changed)
    metrics={k:{'protected':int(m.sum()),'changed':int(np.count_nonzero(m&(changed if m.shape==h.shape else cells)))} for k,m in masks.items()}
    # Consumer negative: a one-ULP height edit at a protected vertex must register.
    r,c=np.argwhere(masks['fixed_vertices'])[0]
    bad=h.copy();bad[r,c]=np.nextafter(bad[r,c],np.float32(np.inf))
    bad_diff=bad.view(np.uint32)!=b.view(np.uint32)
    negative=bool(np.any(bad_diff&masks['fixed_vertices']))
    assert negative
    after={p:sha(Path(p)) for p in before}
    gates={k+'_exact':v['changed']==0 for k,v in metrics.items()}
    gates.update(readset_stable=before==after,one_ulp_edit_negative=negative)
    report={'status':'PASS_EV95_GLOBAL_CIVIL_SOURCE_PRESERVED' if all(gates.values()) else 'FAIL',
        'checks':gates,'metrics':metrics,'source_pins_start':before,'source_pins_end':after,
        'consumer_sha256':sha(Path(__file__)),
        'limits':['Proof of EV95 source heights over the conservative global civil mask.',
                  'Existing vehicle/bridge runtime tests remain historical; EV95 native readback is pending.']}
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))
    if not all(gates.values()):raise SystemExit(2)
if __name__=='__main__':main()
