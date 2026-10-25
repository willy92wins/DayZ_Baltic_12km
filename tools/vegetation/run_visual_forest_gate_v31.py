"""Run the unchanged forest judge on compact records read from the staged WRP.

Only the records I/O adapter changes; metric functions, masks, bands and verdict
logic are the existing runtime-b consumer. All keys originate in valid WRP rows.
"""
import argparse,hashlib,json,runpy,sys
from pathlib import Path
import numpy as np


def main():
    ap=argparse.ArgumentParser();ap.add_argument('inputs');ap.add_argument('gate',choices=['g2g3_map','g8_agreement','g7_map']);a=ap.parse_args()
    root=Path(a.inputs);meta=json.loads((root/'inputs.json').read_text());assert meta['status']=='INPUTS_READY_NOT_ACCEPTANCE'
    for name,key in [('records.npz','records_sha256'),('g5m.npz','rasters_sha256')]:
        assert hashlib.sha256((root/name).read_bytes()).hexdigest()==meta[key]
    if a.gate=='g7_map':
        for name in ('wsea1m.npy','bog1m.npy','slot1m.npy'):
            assert hashlib.sha256((root/name).read_bytes()).hexdigest()==meta['auxiliary_rasters'][name]
    G=Path(meta['gates']);sys.path[:0]=[str(G),str(G.parent)]
    import recio
    def load_records(path,bbox=None):
        assert Path(path).resolve()==(root/'records.npz').resolve()
        z=np.load(path);models=z['models'].tolist();mi=z['midx'];m=z['matrix'].astype(np.float64)
        assert len(m)==meta['forest_count'] and m.shape[1]==12 and np.isfinite(m).all() and mi.max()<len(models)
        keys=np.ones(len(m),bool)
        if bbox is not None:
            x0,z0,x1,z1=bbox;k=(m[:,9]>=x0)&(m[:,9]<x1)&(m[:,11]>=z0)&(m[:,11]<z1);mi,m,keys=mi[k],m[k],keys[k]
        return models,mi,m,keys
    recio.load_records=load_records
    output=root/(a.gate+'.json');assert not output.exists()
    if a.gate=='g7_map':sys.argv=[str(G/(a.gate+'.py')),str(root/'records.npz'),str(root),str(output),'--livonia-bands',meta['bands']]
    else:sys.argv=[str(G/(a.gate+'.py')),str(root/'records.npz'),str(root),meta['bands'],str(output)]
    runpy.run_path(sys.argv[0],run_name='__main__')


if __name__=='__main__':main()
