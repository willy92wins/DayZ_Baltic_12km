"""Measure the existing P11 road contract on current terrain, without editing it.

The wet mask conservatively includes any 1m wet sample in each vertex's 6m
Voronoi cell. Original 48m/470m/18m exclusions and road judge remain unchanged.
"""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import verify_roads_v30 as judge

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('build');ap.add_argument('out');a=ap.parse_args()
    B=Path(a.build);out=Path(a.out);out.mkdir(parents=True,exist_ok=False);W=HERE.parents[1]
    I=B/'forest-visual-consumers-20261024-a';meta=json.loads((I/'inputs.json').read_text())
    assert sha(I/'water1m.npy')==meta['auxiliary_rasters']['water1m.npy']
    wet=np.load(I/'water1m.npy');assert wet.shape==(12288,12288)
    v=np.pad(wet[::-1],((3,0),(3,0)),constant_values=True)[:12288,:12288].reshape(2048,6,2048,6).any((1,3))[::-1]
    np.savez_compressed(out/'water-vertices.npz',wet=v)
    R=Path(judge.R)  # Historical source geometry is an untracked dataset in the primary checkout.
    assert (R/'tests/regional_foundation_roads_v6/reference.npz').is_file()
    assert (R/'evidence/regional-foundation-v1/road-grade-chains-v6.json').is_file()
    # Check source equality after newline decoding: the shared checkout uses LF,
    # the assigned worktree CRLF. Both byte hashes are retained in the report.
    assert Path(judge.sample.__code__.co_filename).read_text(encoding='utf-8')==(W/'tools/navigation/waterway_common.py').read_text(encoding='utf-8')
    terrain=B/'visual-merged-20261024-b/terrain-buried.npz';baseline=B/'water-fix-b/terrain.npz'
    assert sha(terrain)==meta['terrain_sha256'];assert sha(baseline)=='07054c46ebf2861bc905fe2d68fb3b734d7b8e9ad1d538c73a7ee745edd56d62'
    results={}
    for label,path in [('baseline_same_current_mask',baseline),('current',terrain)]:
        h=np.load(path)['heights'];result=judge.evaluate(h.astype(float),v);results[label]=result
        (out/(label+'.json')).write_text(json.dumps(result,indent=2));print(label,json.dumps({k:v for k,v in result.items() if k!='fail_list'}),flush=True)
    report=dict(status=results['current']['status'],scope='P11 offline terrain reservation; no physical roads or vehicle acceptance',
                terrain_sha256=sha(terrain),baseline_sha256=sha(baseline),water_sha256=sha(out/'water-vertices.npz'),
                current={k:v for k,v in results['current'].items() if k!='fail_list'},
                baseline_same_current_mask={k:v for k,v in results['baseline_same_current_mask'].items() if k!='fail_list'},
                sources={str(p):sha(p) for p in (I/'water1m.npy',Path(judge.__file__),Path(judge.sample.__code__.co_filename),
                    R/'tests/regional_foundation_roads_v6/reference.npz',R/'evidence/regional-foundation-v1/road-grade-chains-v6.json')},
                limits=['6m vertex distance mask, conservative wet sampling; exact bridge/river overlaps excluded by existing contract.',
                        'Physical mapping, endpoint/junction aprons and wet crossings are outside this gate; no vehicle run.'])
    (out/'review.json').write_text(json.dumps(report,indent=2))

if __name__=='__main__':main()
