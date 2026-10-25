"""Local shore transition for the approved R1/R2/R3 flat-water fallback.

Only the removed native-piece cells and their 24 m bank halo may change.
The inner 12 m is fully profiled; a quintic taper joins the outer boundary.
Existing road/platform/nature and certified 24 m corridor vertices are fixed.
Narva is editable only inside this local R1 domain, as approved on 8 October.
"""
from pathlib import Path
from types import SimpleNamespace
import hashlib,json,sys
import numpy as np
from scipy import ndimage
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
R=W.parents[2]
B=Path(r'E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008')
E=W/'evidence/v30-curved-channel-pilot-2026-10-08'
sys.path[:0]=[str(W/'tools/terrain'),str(W/'tools/water')]
from profile_inland_v30 import profile
from finish_shores_v30 import protect_corridors,discard_steeper_land_faces,ease
from v30_common import cell_planes,grid_xz
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
SOURCE=Path('E:/DayZ-Baltic-Build/v30-navigation-contract-20261008/terrain_floor.npz')

def main():
    out=B/'flat-profile';out.mkdir(exist_ok=False)
    assert sha(SOURCE)=='05a9d6812ba3e3391b8da0d4690e8034ea747a92aa0fdaa96425b58dd78074d3'
    t=dict(np.load(SOURCE));h=t['heights'].astype(float)
    axes=json.loads(Path('E:/DayZ-Baltic-Build/v30-continuation-20261008/junction-fix-r2/axes.json').read_text())
    core=np.zeros(h.shape,bool)
    for a in axes.values():
        for r,c in a['removed_cells']:core[r:r+2,c:c+2]=True
    dist=ndimage.distance_transform_edt(~core,sampling=6.)
    corridor,_,_,_=protect_corridors(cell_planes(t['cls'],t['level']))
    nature=np.load(R/'tests/regional_outline_v1/reference.npz')['reserve'].astype(bool)
    frozen=t['reserve']|t['platform']|corridor|nature
    allowed=(dist<24)&~frozen
    params=json.loads(Path('E:/DayZ-Baltic-Build/v30-v12/inland/report.json').read_text())['params']
    params.update(narva_radius=0.,bed_floor=None,band=18.,sigma=18.)
    params['slope_by_class']={int(k):v for k,v in params['slope_by_class'].items()}
    a=SimpleNamespace(**params);a.ext_sd=np.load(a.outline_sd)['sd'].astype(float)
    # Reuse the established shore method; select only the approved local domain below.
    print('profile start',flush=True)
    full,_,rep=profile(t,corridor,np.zeros(h.shape,bool),a)
    print('profile complete',flush=True)
    weight=ease((24-dist)/12.)
    candidate=h.copy();candidate[allowed]=h[allowed]+weight[allowed]*(full['heights'][allowed]-h[allowed])
    # A bed already at the accepted floor cannot be lowered below it. Low/Narva
    # beds under that floor keep the pre-existing exception, not a new excavation.
    floor_guard=allowed&np.isin(t['cls'],(2,3,5,6,7))&(h>=1.)
    candidate[floor_guard]=np.maximum(candidate[floor_guard],1.)
    candidate,recovery=discard_steeper_land_faces(candidate,h,t['cls'])
    result=dict(t,heights=candidate.astype(t['heights'].dtype))
    delta=result['heights'].astype(float)-h;changed=delta!=0
    assert not np.any(changed&~allowed)
    assert not np.any(changed&frozen)
    assert not np.any(result['heights'][floor_guard]<1.)
    dest=out/'terrain_flat.npz';np.savez_compressed(dest,**result)
    np.savez_compressed(out/'masks.npz',core=core,allowed=allowed,frozen=frozen,corridor=corridor)
    x,z=grid_xz();narva=np.hypot(x-2417.1428225906,z-6889.8850822322)<=620
    report=dict(status='LOCAL_PROFILE_PENDING_GEOMETRY_AND_RUNTIME',source=str(SOURCE),source_sha256=sha(SOURCE),
                output=str(dest),output_sha256=sha(dest),changed_vertices=int(changed.sum()),
                changed_narva_vertices=int((changed&narva).sum()),delta_min_max=[float(delta.min()),float(delta.max())],
                metadata_exact=True,frozen_exact=True,outside_domain_exact=True,existing_bed_floor_preserved=True,
                parameters=params,profile_report=rep,face_recovery=recovery)
    (E/'flat-profile.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('profile_report','parameters')},indent=2),flush=True)

if __name__=='__main__':main()
