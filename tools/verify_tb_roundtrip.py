"""Compare actual Terrain Builder exports against immutable ASC inputs."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import rasterio

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
parser.add_argument('--out', type=Path)
args = parser.parse_args()
ROOT = args.repo.resolve()
OUT = args.out or ROOT / 'evidence' / 'tb-import'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def compare(label, source, export):
    source, export = ROOT / source, ROOT / export
    with rasterio.open(source) as a, rasterio.open(export) as b:
        av, bv = a.read(1).astype('float64'), b.read(1).astype('float64')
        same_grid = a.shape == b.shape and a.transform == b.transform
        result = dict(label=label, source=str(source), export=str(export),
            source_sha256=sha(source), export_sha256=sha(export),
            source_shape=a.shape, export_shape=b.shape,
            source_transform=list(a.transform), export_transform=list(b.transform),
            same_grid=same_grid, export_crs=str(b.crs),
            crs_note='TB zone 31N is an engineering wrapper; not Baltic georeferencing.')
        if same_grid:
            delta = np.abs(av-bv)
            result.update(samples=int(av.size), differing_samples=int(np.count_nonzero(delta)),
                max_absolute_error_m=float(delta.max()), mean_absolute_error_m=float(delta.mean()),
                samples_over_0_00501m=int(np.count_nonzero(delta>0.00501)),
                rounded_centimetre_equivalent=bool(np.allclose(np.round(av,2),bv,atol=0.000001,rtol=0)))
            result['status'] = 'PASS' if np.isfinite(bv).all() and delta.max()<=0.00501 else 'FAIL'
        else:
            result['status']='FAIL'
        if label=='probe' and same_grid:
            controls=json.loads((ROOT/'tests/registration-probe/expected.json').read_text())['controls']
            result['controls']=[dict(c, actual=float(bv[c['row'],c['col']]),
                pass_height=bool(bv[c['row'],c['col']]==c['z'])) for c in controls]
        result['vertex_registration']='NOT_VERIFIED; raster roundtrip does not prove sample centre versus mesh vertex placement.'
        return result

report={'date':'2026-09-29','tolerance_m':0.00501,
    'tolerance_reason':'TB ASCII export writes two decimal places; allow half of one centimetre plus float epsilon.',
    'results':[
        compare('probe','tests/registration-probe/probe_128_6m.asc','tb/registration_probe/probe_tb_export.asc'),
        compare('regional','source/baltic_physical_2048_6m.asc','tb/baltic_physical/baltic_physical_tb_export.asc')
    ]}
report['status']='PASS' if all(r['status']=='PASS' for r in report['results']) else 'FAIL'
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'tb-roundtrip.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
