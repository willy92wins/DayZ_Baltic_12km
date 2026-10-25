"""Restore complete horizontal tile/band groups at all three native reaches.

Regenerate affected tile groups, instead of stacking fillers on clipped ponds.
Other source models/poses are copied unchanged; source archives stay immutable.
"""
from pathlib import Path
import hashlib,json,math,shutil,sys
from collections import defaultdict
import numpy as np
import shapely
from shapely.geometry import box
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008')
FIT=Path('E:/DayZ-Baltic-Build/v30-continuation-20261008/junction-fix-r2')
E=W/'evidence/v30-curved-channel-pilot-2026-10-08'
sys.path[:0]=[str(W/'tools/terrain'),str(W/'tools/navigation')]
from v30_common import cell_planes
from water_mesh import write_water_mesh
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    out=B/'flat-water';out.mkdir(exist_ok=False)
    src=out/'water/source/baltic_water_v30'
    shutil.copytree(FIT/'water/source/baltic_water_v30',src)
    manifest=json.loads((FIT/'water/pieces.json').read_text())
    axes=json.loads((FIT/'axes.json').read_text())
    removed={tuple(rc) for a in axes.values() for rc in a['removed_cells']}
    tiles=set()
    for r,c in removed:
        x0,z0,x1,z1=c*6,12282-(r+1)*6,(c+1)*6,12282-r*6
        for tx in range(math.floor((x0-.01)/48),math.floor((x1+.01)/48)+1):
            for tz in range(math.floor((z0-.01)/48),math.floor((z1+.01)/48)+1):tiles.add((tx,tz))
    t=np.load(B/'flat-profile/terrain_flat.npz');planes=cell_planes(t['cls'],t['level'])
    keep=[];dropped=[]
    for p in manifest['poses']:
        if 'matrix' in p or (math.floor(p['origin'][0]/48),math.floor(p['origin'][2]/48)) in tiles:dropped.append(p)
        else:keep.append(p)
    assert sum('matrix' in p for p in dropped)==sum(len(a['pieces']) for a in axes.values())
    newposes=[];newmodels=[]
    for tx,tz in sorted(tiles):
        tile=box(tx*48-.01,tz*48-.01,(tx+1)*48+.01,(tz+1)*48+.01)
        origin=(tx*48+24,tz*48+24)
        byband=defaultdict(list)
        for r in range(max(0,math.floor((12282-(tz+1)*48)/6)-1),min(2047,math.ceil((12282-tz*48)/6)+1)):
            for c in range(max(0,tx*8-1),min(2047,(tx+1)*8+1)):
                if not np.isfinite(planes[r,c]):continue
                p=box(c*6,12282-(r+1)*6,(c+1)*6,12282-r*6).intersection(tile)
                if p.area>1e-6:byband[round(float(planes[r,c])/.025)].append(p)
        for band,parts in sorted(byband.items()):
            g=shapely.union_all(parts);name=f'flatfix_{tx:03d}_{tz:03d}_{band:04d}'
            assert not (src/(name+'.p3d')).exists()
            rep=write_water_mesh(g,src/(name+'.p3d'),origin,uv_local=True)
            x0,z0,x1,z1=g.bounds
            rep.update(name=name,bounds_rel=[x0-origin[0],z0-origin[1],x1-origin[0],z1-origin[1]],sha256=sha(src/(name+'.p3d')))
            newmodels.append(rep)
            newposes.append(dict(model=f'baltic_water_v30\\{name}.p3d',origin=[origin[0],band*.025,origin[1]],band=band,area_m2=round(g.area,3)))
    manifest['poses']=keep+newposes;manifest['model_list']+=newmodels
    manifest.update(instances=len(manifest['poses']),models=len(manifest['model_list']),
                    triangles=sum(m['triangles'] for m in manifest['model_list']),terrain_sha256=sha(B/'flat-profile/terrain_flat.npz'),
                    status='FLAT_FALLBACK_SOURCE_PENDING_COMPILE')
    (out/'water/pieces.json').write_text(json.dumps(manifest,indent=1)+'\n')
    (out/'axes.json').write_text('{}\n')
    compile_src=out/'compile/source/baltic_water_v30';compile_src.mkdir(parents=True)
    for name in [m['name']+'.p3d' for m in newmodels]+['config.cpp','$PBOPREFIX$']:shutil.copyfile(src/name,compile_src/name)
    report=dict(status='FLAT_SOURCE_PENDING_GATES',affected_tiles=sorted(tiles),removed_cells=len(removed),
                removed_poses=dropped,new_poses=newposes,new_models=newmodels,
                unchanged_poses=len(keep),source_manifest_sha256=sha(FIT/'water/pieces.json'),manifest_sha256=sha(out/'water/pieces.json'))
    (E/'flat-water-authoring.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(tiles=len(tiles),removed_poses=len(dropped),new_models=len(newmodels),kept_poses=len(keep))))

if __name__=='__main__':main()
