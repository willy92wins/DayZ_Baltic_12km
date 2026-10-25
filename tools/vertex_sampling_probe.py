"""Disposable test of pixel-centre -> NW-corner TB vertex sampling.

This does not modify or authorize resampling the production coastline/terrain.
"""
from pathlib import Path
import argparse, json, hashlib
import numpy as np
import shapefile

def centres_to_vertices(a):
    """Bilinear sampling at (row-.5, col-.5); clamp top/left outer edge."""
    if a.ndim!=2 or not np.isfinite(a).all():
        raise ValueError('Expected a finite 2D raster without nodata')
    previous_row=np.maximum(np.arange(a.shape[0])-1,0)
    previous_col=np.maximum(np.arange(a.shape[1])-1,0)
    return (a+a[previous_row,:]+a[:,previous_col]+a[previous_row[:,None],previous_col])*.25

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    if a.out.exists(): raise SystemExit('Refusing to overwrite fixture directory')
    a.out.mkdir(parents=True)
    row,col=np.indices((128,128))
    # Independent analytic reference in engineering metres.
    def plane(x,y): return 100+(x-200000)/6+y/12
    source=plane(200000+(col+.5)*6,768-(row+.5)*6)
    corrected=centres_to_vertices(source)
    expected=plane(200000+col*6,768-row*6)
    assert np.max(np.abs(corrected[1:,1:]-expected[1:,1:]))<1e-12
    assert np.min(np.abs(source[1:,1:]-expected[1:,1:]))==.25
    for name,data in [('plane_gis_centres',source),('plane_tb_vertices',corrected)]:
        with (a.out/(name+'.asc')).open('w',newline='\n') as f:
            f.write('ncols 128\nnrows 128\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n')
            np.savetxt(f,data,fmt='%.4f')
    controls=[]
    with shapefile.Writer(str(a.out/'vertex_controls'),shapeType=shapefile.POINT) as wr:
        wr.field('label','C',10);wr.field('expect_z','C',20)
        for name,r,c in [('NW',8,11),('NE',17,112),('SW',110,20),('SE',101,106)]:
            x=200000+c*6;y=768-r*6;z=plane(x,y)
            wr.point(x,y);wr.record(name,str(z))
            controls.append({'name':name,'row':r,'col':c,'x':x,'y':y,'z':z,'uncorrected_z':float(source[r,c])})
    wkt=(a.repo/'tb/registration_probe/probe_tb_export.prj').read_text(encoding='ascii')
    (a.out/'vertex_controls.prj').write_text(wkt,encoding='ascii')
    (a.out/'vertex_controls.cpg').write_text('UTF-8',encoding='ascii')
    report={'purpose':'Disposable consumer test only','formula':'z=100+(X-200000)/6+Y/12',
            'tb_vertex_contract':'X=200000+col*6; Y=768-row*6',
            'source_sample_contract':'X=200003+col*6; Y=765-row*6',
            'edge_policy':'Top row/left column clamped. Analytic exactness applies to interior only.',
            'offline_interior_max_error_m':float(np.max(np.abs(corrected[1:,1:]-expected[1:,1:]))),
            'negative_control_uncorrected_error_m':.25,'controls':controls,
            'terrain_builder_verdict':'NOT_TESTED',
            'production':'NOT_APPLIED: must assess coastline, nodata, edge and hydrographic constraints separately',
            'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in a.out.iterdir() if p.is_file()}}
    (a.out/'expected.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
