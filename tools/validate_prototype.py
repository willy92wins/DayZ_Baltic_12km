"""Consumer validation and independent source/control checks for the candidate."""
from collections import Counter,defaultdict
import hashlib,json,math,subprocess,sys
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from shapely.geometry import shape,Point
import shapefile
from geo_common import ROOT,RAW,DERIVED,EVIDENCE,N,CELL,SIZE,TB_X,TB_Y,save_json

def main():
    checks={}
    approval=json.loads((EVIDENCE/'aprobacion.json').read_text(encoding='utf-8'))
    for relative in ['recorte-v0.kml','evidencia/georef-v0.json']:
        p=EVIDENCE/Path(relative).name
        checks['approved_'+p.name]=hashlib.sha256(p.read_bytes()).hexdigest()==approval['reference_sha256'][relative]
    stats=json.loads((EVIDENCE/'prototype-summary.json').read_text())
    contract=json.loads((EVIDENCE/'coordinate-contract.json').read_text())
    source_meta=json.loads((EVIDENCE/'source-manifest.json').read_text())['sources']
    west,south,east,north=contract['source_bbox_lonlat']
    # Independent spherical Mercator expression, no call to the generator transform.
    merc_y=lambda lat:math.log(math.tan(math.pi/4+math.radians(lat)/2))
    def grid_position(lon,lat):
        return int((merc_y(north)-merc_y(lat))/(merc_y(north)-merc_y(south))*N),int((lon-west)/(east-west)*N)
    anchors=[('Lake Peipus',27.85,58.30),('Lake Ladoga',31.35,60.10),('Lake Ilmen',31.45,58.20),
             ('Gatchina',30.1329523,59.5770957),('Luga',29.8496614,58.7377484),('Narva',28.1790751,59.3796931)]
    controls=[]
    for name,lon,lat in anchors:
        row,col=grid_position(lon,lat)
        lo0=west+col/N*(east-west);lo1=west+(col+1)/N*(east-west)
        top_y=merc_y(north)-row/N*(merc_y(north)-merc_y(south))
        bottom_y=merc_y(north)-(row+1)/N*(merc_y(north)-merc_y(south))
        la1=math.degrees(2*math.atan(math.exp(top_y))-math.pi/2)
        la0=math.degrees(2*math.atan(math.exp(bottom_y))-math.pi/2)
        candidates=[s for s in source_meta if s['group']=='dem' and s['nominal_sw']==[math.floor(lon),math.floor(lat)]]
        assert len(candidates)==1
        with rasterio.open(candidates[0]['path']) as raw:
            win=from_bounds(lo0,la0,lo1,la1,raw.transform).round_offsets().round_lengths()
            values=raw.read(1,window=win,masked=True)
            expected_mean=float(values.mean())
        controls.append({'name':name,'longitude':lon,'latitude':lat,'row':row,'col':col,
          'source_egm2008_mean_m':expected_mean,'source_file':candidates[0]['filename'],
          'method':'Direct source-window mean at independently computed output-cell bounds; 6 real-metre tolerance for footprint weighting/DSM variation.'})
    terrain_reports=[]
    for name,multiplier in [('physical',1),('relief3x',3)]:
        spec=json.loads((EVIDENCE/f'{name}.ascii-spec.json').read_text())
        factor=contract['z_physical_factor']*multiplier
        spec['controls']=[{'name':c['name'],'row':c['row'],'col':c['col'],
          'expected_z':c['source_egm2008_mean_m']*factor,
          'tolerance':6*factor} for c in controls]
        save_json(EVIDENCE/f'{name}.ascii-spec.json',spec)
        asc=DERIVED/f'tb/source/baltic_{name}_2048_6m.asc'
        report=EVIDENCE/f'{name}.ascii-validation.json'
        proc=subprocess.run([sys.executable,str(ROOT/'tools/validate_ascii.py'),str(asc),'--spec',str(EVIDENCE/f'{name}.ascii-spec.json'),'--report',str(report)],capture_output=True,text=True)
        parsed=json.loads(report.read_text());checks[name+'_ascii_validator']=proc.returncode==0
        with rasterio.open(asc) as src:
            a=src.read(1)
            checks[name+'_gdal_shape']=src.shape==(2048,2048)
            checks[name+'_gdal_bounds']=np.allclose(src.bounds,[200000,0,212288,12288],atol=1e-7,rtol=0)
            checks[name+'_gdal_top_left_center']=np.allclose(src.xy(0,0),(200003,12285),atol=1e-7,rtol=0)
            checks[name+'_finite_no_holes']=bool(np.isfinite(a).all() and not (a==src.nodata).any())
            actual=[]
            for c in controls:
                actual.append(dict(c,actual_z=float(a[c['row'],c['col']]),expected_z=c['source_egm2008_mean_m']*factor))
            terrain_reports.append({'variant':name,'controls':actual,'validator_status':parsed['status'],'errors':parsed['errors']})
        with rasterio.open(DERIVED/f'gis/height_{name}_game.tif') as tif:
            checks[name+'_ascii_tiff_roundtrip']=bool(np.allclose(tif.read(1),a,atol=.00006,rtol=0))
    material_root=Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DZ\surfaces\data\terrain')
    material_names=['cp_gravel','cp_conifer_common1','cp_grass','cp_grass_tall']
    checks['vanilla_materials_exist']=all((material_root/(name+'.rvmat')).is_file() for name in material_names)
    shapes=[]
    for path in (DERIVED/'tb/source/vectors').glob('*.shp'):
        with shapefile.Reader(str(path),encoding='utf-8') as reader:
            count=len(reader);bbox=list(reader.bbox)
            shapes.append({'name':path.name,'features':count,'bounds':bbox})
            checks['shape_'+path.stem]=bool(count>0 and bbox[0]>=TB_X-.001 and bbox[1]>=-.001 and bbox[2]<=TB_X+SIZE+.001 and bbox[3]<=SIZE+.001)
    with rasterio.open(DERIVED/'tb/source/sat_preview.png') as sat:
        checks['sat_worldfile_registration']=np.allclose(sat.bounds,[200000,0,212288,12288],atol=1e-7,rtol=0)
    border=json.loads((EVIDENCE/'border-processing.json').read_text())
    checks['border_uses_country_relation']=border['clipped_ways']>=10 and not border['missing_geometry']
    checks['land_worldcover_no_unknowns']=stats['worldcover_unclassified_non_ocean_cells']==0
    osm=json.loads((EVIDENCE/'osm-processing.json').read_text())
    checks['osm_no_missing_geometry_errors']=not osm['errors']
    report={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'terrain_source_controls':terrain_reports,
      'shapefile_consumers':shapes,'scope':'Offline format, spatial registration and source controls. Runtime, water interaction, navigation, Terrain Builder sampling and 80-100-player performance are not tested.'}
    save_json(EVIDENCE/'validation-report.json',report)
    print(json.dumps({'status':report['status'],'failed':[k for k,v in checks.items() if not v],'checks':len(checks)},indent=2))
    if not all(checks.values()):raise SystemExit(1)

from pathlib import Path
if __name__=='__main__':main()
