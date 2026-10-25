"""Prepare current WRP records and raster inputs for the unchanged forest judges.

No acceptance here. Texture/bog/urban/bridge masks retain the verified runtime
baseline. Native water is recalculated on the merged terrain; removed vanilla
pieces are absent, and custom water/bed use saved model faces with binary parity.
"""
import argparse,hashlib,json,struct,sys,shutil
from pathlib import Path
import numpy as np
from scipy.ndimage import distance_transform_edt
from matplotlib.path import Path as MPath
from shapely.geometry import Polygon
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent/'terrain')]
from prune_visual_forest_v31 import prefix,objects
from wrp0wzd import read


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('build');ap.add_argument('out');a=ap.parse_args()
    B=Path(a.build);out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
    S=B/'stage-visual-forest-20261024-b';P=B/'visual-pilot-20261024-p';M=B/'visual-merged-20261024-b'
    src=S/'root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
    assert sha(src)=='19e1a63711080d4214b1d8aef5de874d873fe00d128076e5f2092b65595375e9'
    support=json.loads((S/'forest-support-review-full.json').read_text());assert support['status']=='SUPPORT_CLEARANCE_PASS' and support['source_wrp_sha256']==sha(src)
    G=B/'forest-water-fix-b/gates';sys.path.insert(0,str(G));import gcfg
    T=gcfg.tool()
    sys.path.insert(0,str(HERE.parents[1]/'evidence/v31-pond-layer-2026-10-13/ev112/ot1/gates'));import gatelib as K
    baseline=B/'forest-painted-rasters-runtime-b';meta=json.loads((baseline/'grasters.json').read_text())
    assert sha(baseline/'g5m.npz')==meta['files']['g5m.npz']
    g=np.load(baseline/'g5m.npz');ras={k:g[k] for k in g.files}
    H=np.load(M/'terrain-buried.npz')['heights'];assert sha(M/'terrain-buried.npz')==support['terrain_sha256']
    fp=np.load(M/'bury-work/fp0/footprint.npz')
    # Forest records are read from the actual staged WRP, not the placer JSON.
    reference=json.loads((S/'stage-report.json').read_text())['forest_reference'];assert sha(reference['path'])==reference['sha256']
    names=sorted(json.loads(Path(reference['path']).read_text())['models']);index={n:i for i,n in enumerate(names)}
    count=support['instances'];matrix=np.empty((count,12),np.float32);midx=np.empty(count,np.uint16);ids=np.empty(count,np.uint32);n=0;total=0
    with src.open('rb') as f:
        prefix(f)
        for ident,name,raw in objects(f):
            total+=1
            if name not in index:continue
            assert n<count;matrix[n]=struct.unpack_from('<12f',raw);midx[n]=index[name];ids[n]=ident;n+=1
    assert n==count and len(np.unique(ids))==n and np.isfinite(matrix).all()
    np.savez_compressed(out/'records.npz',models=np.array(names),midx=midx,matrix=matrix,ids=ids);del matrix,midx,ids
    print('staged forest',count,'of',total,flush=True)
    water=np.zeros((12288,12288),bool)
    sea_band=np.zeros_like(water)
    for start in range(0,12288,128):
        X,Z=np.meshgrid(np.arange(12288)+.5,12288-(start+np.arange(128))-.5)
        water[start:start+128],sea_band[start:start+128]=T.wet_at(H,fp['plane'],fp['env_plane'],X,Z)
    stage=B/'stage-visual-probe-20261024-a/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
    records=read(stage)['objects'];current_ids={o['id'] for o in records}
    geometry=json.loads(Path(K.GEOM).read_text())['models']
    def stamp_water(tris):
        v=tris.reshape(-1,3);lo=v[:,[0,2]].min(0);hi=v[:,[0,2]].max(0)
        c0=max(0,int(np.floor(lo[0])));c1=min(12282,int(np.ceil(hi[0])))
        r0=max(6,int(np.floor(12288-hi[1])));r1=min(12288,int(np.ceil(12288-lo[1])))
        X,Z=np.meshgrid(np.arange(c0,c1)+.5,12288-np.arange(r0,r1)-.5);q=np.c_[X.ravel(),Z.ravel()]
        y=K.tri_max(tris,q,np.full(len(q),-np.inf))
        water[r0:r1,c0:c1]|=(y>K.terrain_y(H,q[:,0],q[:,1])).reshape(X.shape)
    for obj in records:
        name=obj['name'].lower()
        if '\\streambed\\streambed_' in name and 'stones' not in name:
            piece=K.Piece(dict(model=obj['name'],matrix=obj['matrix']),geometry);stamp_water(piece.water)
    kit=np.zeros_like(ras['kit'])
    def stamp_kit(poly):
        lo=np.min(poly,0);hi=np.max(poly,0)
        c0=max(0,int(lo[0]//5));c1=min(2458,int(hi[0]//5)+2);r0=max(0,int(lo[1]//5));r1=min(2458,int(hi[1]//5)+2)
        X,Z=np.meshgrid((np.arange(c0,c1)+.5)*5,(np.arange(r0,r1)+.5)*5)
        kit[r0:r1,c0:c1]|=MPath(poly).contains_points(np.c_[X.ravel(),Z.ravel()]).reshape(X.shape)
    old=B/'stage-nonforest-c/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
    for hull in T.object_hulls(old)[0]:
        if hull['id'] in current_ids and hull['kind']=='kit':stamp_kit(hull['hull'])
    sys.path.insert(0,'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/py3d');import py3d
    author=json.loads((P/'author-report.json').read_text());bedpolys=[]
    for inst in author['instances']:
        source=P/'source'/inst['model'].replace('\\','/');assert sha(source)==inst['sha256']
        with source.open('rb') as f:
            assert struct.unpack('<4s2I',f.read(12))==(b'MLOD',257,4);lod=py3d.LOD(f)
        v=np.array([p.coords for p in lod.points])+inst['origin'];wet=[]
        for face in lod.faces:
            points=v[[p.point_index for p in face.vertices]]
            if 'water_streambed' in face.material:wet.append(points)
            else:bedpolys.append(Polygon(points[:,[0,2]]))
        stamp_water(np.array(wet))
    bed=unary_union(bedpolys);assert bed.is_valid
    for poly in (list(bed.geoms) if hasattr(bed,'geoms') else [bed]):
        assert not poly.interiors;stamp_kit(np.array(poly.exterior.coords))
    padded=np.ones((12290,12290),bool);padded[:12288,:12288]=water[::-1]
    water5=padded.reshape(2458,5,2458,5).mean((1,3))>=.5
    changed_water=int(np.count_nonzero(ras['water']!=water5));changed_kit=int(np.count_nonzero(ras['kit']!=kit))
    ras.update(water=water5,kit=kit,dw=(distance_transform_edt(~water5)*5).astype(np.float32))
    np.savez_compressed(out/'g5m.npz',**ras);np.save(out/'water1m.npy',water)
    np.save(out/'wsea1m.npy',water.astype(np.uint8)|(sea_band.astype(np.uint8)<<1))
    for name in ('bog1m.npy','slot1m.npy'):
        assert sha(baseline/name)==meta['files'][name];shutil.copy2(baseline/name,out/name)
    result=dict(status='INPUTS_READY_NOT_ACCEPTANCE',forest_count=count,source_wrp_sha256=sha(src),terrain_sha256=support['terrain_sha256'],
                records_sha256=sha(out/'records.npz'),rasters_sha256=sha(out/'g5m.npz'),baseline_rasters_sha256=meta['files']['g5m.npz'],
                water_cells_changed=changed_water,kit_cells_changed=changed_kit,unchanged_rasters=[k for k in ras if k not in ('water','kit','dw')],
                gates=str(G),bands=str(B.parent/'ev112-wip/forest/gates-run/livonia-ev112-bands.json'),
                auxiliary_rasters={n:sha(out/n) for n in ('water1m.npy','wsea1m.npy','bog1m.npy','slot1m.npy')},
                limits=['1m/5m raster context and existing mask conventions; source WRP only.','No compilation, walking, visual or performance verdict.'])
    (out/'inputs.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))


if __name__=='__main__':main()
