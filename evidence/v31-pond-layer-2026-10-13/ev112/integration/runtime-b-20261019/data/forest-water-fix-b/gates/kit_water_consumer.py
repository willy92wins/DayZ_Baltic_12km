"""Independent kit water consumer: uses OT1 gate geometry, not the placer rasterizer."""
import json,sys
from pathlib import Path
import numpy as np
import gcfg
P=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path.insert(0,str(P/'evidence/v31-pond-layer-2026-10-13/ev112/ot1/gates'))
import gatelib as K
sys.path.insert(0,str(P/'tools/terrain'))
from wrp0wzd import read
_MASK=None

def mask():
    global _MASK
    if _MASK is not None:return _MASK
    H=np.load(gcfg.TERRAIN)['heights'].astype(float)
    models=json.loads(Path(K.GEOM).read_text(encoding='utf-8'))['models']
    out=np.zeros((12288,12288),bool)
    for obj in read(gcfg.STAGE_WRP)['objects']:
        name=obj['name'].replace('/','\\').lower()
        if '\\streambed\\streambed_' not in name or 'stones' in name:continue
        piece=K.Piece(dict(model=obj['name'],matrix=obj['matrix']),models)
        c0=max(0,int(np.floor(piece.lo[0])));c1=min(12282,int(np.ceil(piece.hi[0])))
        r0=max(6,int(np.floor(12288-piece.hi[1])));r1=min(12288,int(np.ceil(12288-piece.lo[1])))
        if c1<=c0 or r1<=r0:continue
        X,Z=np.meshgrid(np.arange(c0,c1)+.5,12288-np.arange(r0,r1)-.5);Q=np.c_[X.ravel(),Z.ravel()]
        wy=K.tri_max(piece.water,Q,np.full(len(Q),-np.inf))
        out[r0:r1,c0:c1]|=(wy>K.terrain_y(H,Q[:,0],Q[:,1])).reshape(X.shape)
    _MASK=out
    return out

def sample(x,z):
    return mask()[np.clip(np.floor(12288-z).astype(int),0,12287),np.clip(np.floor(x).astype(int),0,12287)]
