"""Bind the original strict G2/G3 pilot judges to the current staged forest.

The union water raster is sampled at the same 1m cell centres as sector_measure;
OR-ing it with native water is idempotent. Metrics and thresholds are unchanged.
"""
import argparse,hashlib,json,runpy,sys
from pathlib import Path
import numpy as np

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('build');ap.add_argument('inputs');ap.add_argument('gate',choices=['G2','G3']);a=ap.parse_args()
    B=Path(a.build);root=Path(a.inputs);meta=json.loads((root/'inputs.json').read_text())
    for name,key in [('records.npz','records_sha256'),('g5m.npz','rasters_sha256')]:assert sha(root/name)==meta[key]
    assert sha(root/'water1m.npy')==meta['auxiliary_rasters']['water1m.npy']
    D=B/'forest-water-fix-b';sys.path[:0]=[str(D/'gates'),str(D/'r2/gates')]
    import gcfg as C
    package=B/'package-runtime-b';receipt=json.loads((package/'package.json').read_text());pbo=package/'packed/narva_trial.pbo'
    assert sha(pbo)==receipt['pbo_sha256'];assert sha(B/'surface-runtime-b/manifest.json')==receipt['manifest_sha256']
    assert all(sha(p)==h for p,h in json.loads((B/'forest-ae-frozen.json').read_text())['files'].items())
    C.PBO=str(pbo);C.LAYER_DIRS=[str(B/'surface-runtime-b/layers'),*C.LAYER_DIRS]
    C.TERRAIN=B/'visual-merged-20261024-b/terrain-buried.npz';assert sha(C.TERRAIN)==meta['terrain_sha256']
    deployed_fp=C.FOOTPRINT
    assert sha(deployed_fp)=='49ee2a69db85f047425f8e1d31a964f92771ceb19b203c42570b04c3c6207de5'
    C.FOOTPRINT=B/'visual-merged-20261024-b/bury-work/fp0/footprint.npz'
    assert np.array_equal(np.load(C.FOOTPRINT)['plane'],np.load(deployed_fp)['plane'],equal_nan=True)
    C.STAGE_WRP=B/'stage-visual-forest-20261024-b/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
    assert sha(C.STAGE_WRP)==meta['source_wrp_sha256']
    import gate_common as GC
    GC.KIT_WATER._MASK=np.load(root/'water1m.npy',mmap_mode='r')
    data=np.load(root/'records.npz');matrix=data['matrix'];names=data['models'];mi=data['midx'];ids=data['ids']
    sectors=json.loads(C.SECTORS.read_text())['sectors'];keep=np.zeros(len(matrix),bool)
    for sec in sectors:
        # Include the entire polygon bbox: sector_measure owns the exact polygon selection.
        p=np.array(sec['polygon_xz']);lo=p.min(0);hi=p.max(0)
        keep|=(matrix[:,9]>=lo[0])&(matrix[:,9]<=hi[0])&(matrix[:,11]>=lo[1])&(matrix[:,11]<=hi[1])
    records=[dict(id=int(ids[i]),model=str(names[mi[i]]),matrix=matrix[i].tolist()) for i in np.flatnonzero(keep)]
    def load_records(path):
        assert Path(path).resolve()==(root/'records.npz').resolve();return records
    GC.load_records=load_records
    output=root/(a.gate.lower()+'_pilot.json');assert not output.exists()
    binding=dict(source_wrp_sha256=meta['source_wrp_sha256'],records_sha256=meta['records_sha256'],subset_count=len(records),
                 sources={str(p):sha(p) for p in (C.TERRAIN,C.FOOTPRINT,C.SECTORS,C.REFERENCE,Path(pbo),root/'water1m.npy',Path(GC.__file__),D/'r2/gates/g2_g3.py')},
                 changes='I/O binding only; original strict judge, masks and density requirement preserved')
    (root/(a.gate.lower()+'_pilot_binding.json')).write_text(json.dumps(binding,indent=2))
    script=D/'r2/gates/g2_g3.py';sys.argv=[str(script),str(root/'records.npz'),a.gate,'--json',str(output)]
    if a.gate=='G2':sys.argv+=['--dense','A-reserva']
    runpy.run_path(str(script),run_name='__main__')

if __name__=='__main__':main()
