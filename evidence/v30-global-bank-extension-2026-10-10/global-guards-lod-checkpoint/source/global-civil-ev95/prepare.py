"""Read-only global civil protection inventory; never writes terrain."""
from pathlib import Path
import hashlib,importlib.util,json,time
import numpy as np
from scipy.ndimage import binary_dilation

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'real-sector-preflight/civil_inventory.py'
SOURCE_SHA='60d1beb2a36739a98fc70dc5a3b29033286e14abbc87461247bc87dd6f48c0c3'
G=HERE.parent.parent
STAGE=G/'build-wide-slope/stage.json'
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def main():
    out=HERE/'run-01'
    if out.exists():raise FileExistsError(out)
    start=time.perf_counter();assert sha(SOURCE)==SOURCE_SHA
    spec=importlib.util.spec_from_file_location('global_civil_source',SOURCE)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    before=m.check_pins();before[str(SOURCE)]=sha(SOURCE);before[str(__file__)]=sha(__file__)
    before[str(STAGE)]=sha(STAGE)
    stage=json.loads(STAGE.read_text())
    assert stage['status']=='STAGED_EV95_WIDE_HEIGHTS_ONLY' and stage['objects_and_materials_exact'] is True
    wrp=G/'build-wide-slope/package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
    assert sha(wrp)==stage['staged_wrp_sha256'];before[str(wrp)]=sha(wrp)
    reader=m.load_module('global_civil_wrp',m.WRP_READER)
    old,new=reader.read(m.WRP),reader.read(wrp)
    assert old['objects']==new['objects'] and len(new['objects'])==18033
    m.WINDOW=(0,2048,0,2048)
    roads,road_report=m.road_sample_cells()
    # The historical grade checker skips five two/three-node chains. Include
    # their centerlines here too. A full-cell halo below covers the entire
    # +/-4m strip: every centerline point is <=0.5m from a sampled station,
    # and 4.5m < the 6m cell width, independent of tangent direction.
    xy=np.load(m.ROAD_REFERENCE,allow_pickle=False)['xy']
    chains=json.loads(m.ROAD_CHAINS.read_text())['chains']
    shorts=[]
    for i,chain in enumerate(chains):
        if len(chain)>=4:continue
        if len(chain)<2:raise ValueError('isolated road node needs explicit policy')
        pts=xy[np.asarray(chain,dtype=np.int64)]
        s=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(pts,axis=0),axis=1))]
        if s[-1]<=0:raise ValueError('zero-length road chain')
        samples=np.linspace(0,s[-1],int(np.ceil(s[-1]))+1)
        q=np.column_stack([np.interp(samples,s,pts[:,d]) for d in (0,1)])
        for x,z in q:roads.update(m.cells_for_world_point(float(x),float(z)))
        shorts.append({'chain_id':i,'nodes':len(chain),'length_m':float(s[-1]),'samples':len(q)})
    bridges,bridge_report=m.bridge_face_cells()
    def cell_mask(cells):
        good=np.asarray(sorted((r,c) for r,c in cells if 0<=r<2047 and 0<=c<2047),dtype=np.int32).reshape(-1,2)
        a=np.zeros((2047,2047),bool);a[tuple(good.T)]=True
        return a
    road_mask=cell_mask(roads)
    road_guard=binary_dilation(road_mask,structure=np.ones((3,3),bool))
    bridge_mask=cell_mask(bridges)
    cells=road_guard|bridge_mask
    vertices=np.zeros((2048,2048),bool)
    for dr,dc in ((0,0),(0,1),(1,0),(1,1)):vertices[dr:dr+2047,dc:dc+2047]|=cells
    # Every recorded original station-support cell and bridge cell is protected.
    assert np.all(cells[road_mask]) and np.all(cells[bridge_mask])
    after={p:sha(p) for p in before};assert before==after
    out.mkdir()
    np.savez_compressed(out/'civil-mask.npz',fixed_vertices=vertices,road_sample_cells=road_mask,
        road_guard_cells=road_guard,bridge_cells=bridge_mask)
    report={'status':'PREPARED_GLOBAL_CIVIL_MASK_ONLY','source_pins_start':before,'source_pins_end':after,
        'base_terrain_sha256':stage['terrain_sha256'],'objects_exact_vs_B':True,'object_count':18033,
        'grid_shape':[2048,2048],'road_chains':len(chains),'short_chains_added':shorts,
        'road_sample_cell_count':int(road_mask.sum()),'road_guard_cell_count':int(road_guard.sum()),
        'bridge_cell_count':int(bridge_mask.sum()),'fixed_vertices':int(vertices.sum()),
        'road':road_report,'bridge':bridge_report,'mask_sha256':sha(out/'civil-mask.npz'),
        'elapsed_s':time.perf_counter()-start,
        'policy':'All road stations including short chains and crossings; one-cell sampled-road halo; all face-bearing bridge LOD footprints.',
        'limits':['Conservative civil freeze, not road grade acceptance or engine collision readback.',
                  'Does not replace platform/reserve/summit/P9 or semantic protection masks. No terrain edit.']}
    (out/'inventory.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','road_chains','road_sample_cell_count','bridge_cell_count','fixed_vertices','elapsed_s')}))

if __name__=='__main__':main()
