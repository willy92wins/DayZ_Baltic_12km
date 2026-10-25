"""Disposable consumer probe: deliberately asymmetric terrain sample locations."""
from pathlib import Path
import json
import numpy as np
import shapefile
from geo_common import ROOT,GAME_CRS,save_json

def main():
    folder=ROOT/'tests/registration-probe';folder.mkdir(parents=True,exist_ok=True)
    a=np.full((128,128),5.0,dtype=np.float32)
    samples=[('NW',8,11,10),('NE',17,112,20),('SW',110,20,30),('SE',101,106,40)]
    controls=[]
    for name,row,col,z in samples:
        a[row-2:row+3,col-2:col+3]=z
        # Single higher centre identifies the exact sample location.
        a[row,col]=z+5
        controls.append({'name':name,'row':row,'col':col,'x':200000+(col+.5)*6,'y':768-(row+.5)*6,'z':z+5})
    p=folder/'probe_128_6m.asc'
    with p.open('w',newline='\n') as f:
        f.write('ncols 128\nnrows 128\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n')
        np.savetxt(f,a,fmt='%.1f')
    with shapefile.Writer(str(folder/'sample_centres'),shapeType=shapefile.POINT) as w:
        w.field('label','C',10);w.field('z','F',10,2)
        for c in controls:w.point(c['x'],c['y']);w.record(c['name'],c['z'])
    (folder/'sample_centres.prj').write_text(GAME_CRS)
    save_json(folder/'expected.json',{'gdal_outer_bounds':[200000,0,200768,768],'controls':controls,'terrain_builder':'NOT_TESTED; compare actual sample positions before applying any half-cell correction.'})
    print('REGISTRATION PROBE CREATED')

if __name__=='__main__':main()
