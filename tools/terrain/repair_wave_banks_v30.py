"""Small dry-bank edits for two reproduced wave exposures on the combined preview.

Lowering the bank, instead of its wet neighbour, preserves the approved bed
floor. Fixed water metadata and a cosine shoulder limit the local edit.
This is authoring; independent geometry and engine consumers must accept it.
"""
from pathlib import Path
import argparse
import json

import numpy as np

from audit_fairway_triangles_v30 import sha
from v30_common import cell_planes, tri_sample, vertex_plane_bounds

SOURCE_SHA = 'a292b6c39ad5c4fa19936e5498dc0ddaa064ee6ce4ecdb3115a763a3f0bc57c1'
REFERENCE_SHA = 'b823d0f167380abe3ca553f4312176fa7323a84d7b92fc436a5b9e072d1b19ad'
PARAMS = dict(target_margin_m=.201, radius_m=12., maximum_lowering_m=.25,
              dry_floor_m=1.4001, adjacent_plane_freeboard_m=.0501)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--terrain', type=Path, required=True)
    ap.add_argument('--reference', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    assert sha(a.terrain) == SOURCE_SHA and sha(a.reference) == REFERENCE_SHA
    assert not a.out.exists()
    t = np.load(a.terrain)
    old = t['heights'].astype(float)
    planes = cell_planes(t['cls'], t['level'], sea_cut=.51)
    _, high = vertex_plane_bounds(planes)
    rr, cc = np.indices(old.shape)
    x, z = cc*6., 12282-rr*6.
    narva = np.hypot(x-2417.1428225906,z-6889.8850822322) <= 620
    mutable = (t['cls']==0) & ~t['platform'] & ~t['reserve'] & ~narva
    floor = np.maximum(PARAMS['dry_floor_m'], np.nan_to_num(high, nan=-100.)+.0501)
    lowering = np.zeros_like(old)
    report = []
    for p in json.loads(a.reference.read_text())['points']:
        if p['id'] not in (765,1176):
            continue
        r,c = (12282-p['z'])/6.,p['x']/6.
        i,j = int(r),int(c)
        fr,fc = r-i,c-j
        corners = [(i,j,1-fc),(i,j+1,fc-fr),(i+1,j+1,fr)] if fc>=fr else [
            (i,j,1-fr),(i+1,j,fr-fc),(i+1,j+1,fc)]
        bank = [(u,v,w) for u,v,w in corners if w>1e-6 and mutable[u,v]]
        assert len(bank)==1, 'This repair requires one mutable dry support vertex'
        u,v,w = bank[0]
        depth = float(planes[i,j]-tri_sample(old,p['x'],p['z']))
        amount = (PARAMS['target_margin_m']-depth)/w
        assert 0<amount<=PARAMS['maximum_lowering_m']
        distance = np.hypot(x-v*6,z-(12282-u*6))
        shoulder = .5*(1+np.cos(np.pi*np.minimum(distance/12.,1)))
        patch = np.minimum(amount*shoulder,np.maximum(old-floor,0.))*mutable
        assert abs(patch[u,v]-amount)<1e-8, 'Bank protection conflicts with the target'
        lowering = np.maximum(lowering,patch)
        report.append(dict(id=p['id'],x=p['x'],z=p['z'],plane=float(planes[i,j]),
                           before_depth_m=depth,bank_row=u,bank_col=v,lowering_m=amount))
    assert len(report)==2
    new = (old-lowering).astype(t['heights'].dtype)
    changed = new!=t['heights']
    assert np.all(mutable[changed])
    a.out.mkdir(parents=True)
    path = a.out/'terrain_wave_banks.npz'
    np.savez_compressed(path,**{k:new if k=='heights' else t[k] for k in t.files})
    result = dict(status='AUTHORING_CANDIDATE',source_sha256=SOURCE_SHA,
                  reference_sha256=REFERENCE_SHA,terrain_sha256=sha(path),parameters=PARAMS,
                  points=report,changes=[dict(row=int(r),col=int(c),before=float(old[r,c]),after=float(new[r,c]))
                                        for r,c in zip(*np.nonzero(changed))])
    (a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=result['status'],points=report,changed_vertices=int(changed.sum()),
                         maximum_lowering_m=float((old-new).max()),terrain_sha256=sha(path)),indent=1))


if __name__=='__main__':
    main()
