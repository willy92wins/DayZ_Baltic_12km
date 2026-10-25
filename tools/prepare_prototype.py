"""Prepare an import candidate, preserving source data and explicit prototype edits."""
from collections import Counter
import csv,json,math
import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree
import rasterio
from rasterio.features import rasterize
from shapely import make_valid,set_precision
from shapely.geometry import shape,mapping,Point,box
from shapely.ops import polygonize,unary_union
import shapefile
from PIL import Image,ImageDraw
from geo_common import *
from build_rasters import write_tif

SOURCE=DERIVED/'tb/source'
SOURCE.mkdir(parents=True,exist_ok=True)

def load_layer(name):
    data=json.loads((DERIVED/f'gis/osm_{name}_wgs84.geojson').read_text(encoding='utf-8'))
    return [(tb_geometry(shape(f['geometry'])),f['properties']) for f in data['features']]

def pieces(geom,wanted):
    if geom.geom_type in wanted:yield geom
    elif hasattr(geom,'geoms'):
        for g in geom.geoms:yield from pieces(g,wanted)

def write_shape(name,features,kind):
    dest=SOURCE/'vectors'/name;dest.parent.mkdir(exist_ok=True)
    types={'line':shapefile.POLYLINE,'polygon':shapefile.POLYGON,'point':shapefile.POINT}
    with shapefile.Writer(str(dest),shapeType=types[kind],encoding='utf-8') as w:
        w.field('osm_id','C',40);w.field('name','C',120);w.field('type','C',40);w.field('bridge','C',10)
        for geom,props in features:
            targets={'line':{'LineString'},'polygon':{'Polygon'},'point':{'Point'}}[kind]
            for g in pieces(geom,targets):
                if kind=='line':w.line([list(g.coords)])
                elif kind=='point':w.point(g.x,g.y)
                else:
                    from shapely.geometry.polygon import orient
                    g=orient(g,sign=-1)
                    w.poly([list(g.exterior.coords)]+[list(r.coords) for r in g.interiors])
                label=props.get('name:en',props.get('name',''))
                category=props.get('highway',props.get('water',props.get('waterway',props.get('place',''))))
                w.record(props.get('osm_id',''),label,category,props.get('bridge',''))
    dest.with_suffix('.prj').write_text(GAME_CRS,encoding='ascii')
    dest.with_suffix('.cpg').write_text('UTF-8',encoding='ascii')

def ocean_polygon(coasts):
    frame=box(TB_X,TB_Y,TB_X+SIZE,TB_Y+SIZE)
    lines=[set_precision(frame.boundary,1e-5)]
    for geom,_ in coasts:lines.extend(set_precision(g,1e-5) for g in pieces(geom,{'LineString'}))
    polygons=list(polygonize(unary_union(lines)))
    seed_x,seed_y=game_xy(28.6,60.05)
    seed=Point(float(seed_x+TB_X),float(seed_y+TB_Y))
    selected=[g for g in polygons if g.covers(seed)]
    assert len(selected)==1, f'Ocean component ambiguous: {len(selected)}'
    ocean=selected[0]
    controls=[('Narva',28.1790751,59.3796931,False),('Petersburg',30.3609096,59.9310584,False),
      ('Kotlin',29.75,60.005,False),('Ladoga',31.35,60.10,False),('Peipus',27.85,58.30,False),
      ('Ilmen',31.45,58.20,False),('Gulf',28.6,60.05,True)]
    checks=[]
    for name,lon,lat,expected in controls:
        x,y=game_xy(lon,lat);actual=ocean.covers(Point(float(x+TB_X),float(y+TB_Y)))
        checks.append({'name':name,'lon':lon,'lat':lat,'ocean_expected':expected,'ocean_actual':actual})
        assert actual==expected, f'Ocean incorrectly classified at {name}'
    assert .05 < ocean.area/(SIZE*SIZE) < .40,'Unreasonable ocean coverage; inspect coastline assembly'
    save_json(EVIDENCE/'ocean-classification.json',{'polygonized_components':len(polygons),'ocean_fraction':ocean.area/(SIZE*SIZE),'controls':checks,'method':'OSM coastline + approved frame polygonization; gulf seed, inland/land exclusion controls. No water-connectivity flood fill.'})
    return ocean

def ascii_grid(path,data):
    assert data.shape==(N,N) and np.isfinite(data).all()
    with path.open('w',encoding='ascii',newline='\n') as f:
        f.write(f'ncols {N}\nnrows {N}\nxllcorner {TB_X:.0f}\nyllcorner {TB_Y:.0f}\ncellsize {CELL:.0f}\nNODATA_value -9999\n')
        np.savetxt(f,data,fmt='%.4f')

def main():
    contract=coordinate_contract()
    with rasterio.open(DERIVED/'gis/dsm_egm2008_3857.tif') as src:dsm=src.read(1);assert not (dsm==src.nodata).any()
    with rasterio.open(DERIVED/'gis/worldcover_2021_3857.tif') as src:cover=src.read(1)
    layers={k:load_layer(k) for k in ['roads','rivers','coastline','water','places','border']}
    ocean=ocean_polygon(layers['coastline'])
    sea=rasterize([(ocean,1)],out_shape=(N,N),transform=GAME_TRANSFORM,dtype='uint8').astype(bool)
    water=rasterize([(g,1) for g,_ in layers['water']],out_shape=(N,N),transform=GAME_TRANSFORM,dtype='uint8').astype(bool)
    allwater=sea|water|(cover==80)
    write_tif(DERIVED/'gis/ocean_mask_game.tif',sea.astype('uint8'),crs=GAME_CRS,transform=GAME_TRANSFORM)
    write_tif(DERIVED/'gis/inland_water_mask_game.tif',(water & ~sea).astype('uint8'),crs=GAME_CRS,transform=GAME_TRANSFORM)
    depths=np.minimum(12.0,distance_transform_edt(sea)*CELL*.08)
    terrain_stats=[]
    for name,multiplier in [('physical',1.0),('relief3x',3.0)]:
        raw_height=(dsm*contract['z_physical_factor']*multiplier).astype('float32')
        height=raw_height.copy()
        # These two edits are clearly labelled prototype construction, not measured data.
        floor=(~allwater)&(height<.25)
        height[floor]=.25
        height[sea]=-depths[sea]
        change=height-raw_height
        write_tif(DERIVED/f'gis/height_{name}_game.tif',height,crs=GAME_CRS,transform=GAME_TRANSFORM)
        write_tif(DERIVED/f'gis/prototype_delta_{name}_game.tif',change,crs=GAME_CRS,transform=GAME_TRANSFORM)
        path=SOURCE/f'baltic_{name}_2048_6m.asc';ascii_grid(path,height)
        dzdy,dzdx=np.gradient(height,CELL);slope=np.degrees(np.arctan(np.hypot(dzdx,dzdy)))
        terrain_stats.append({'variant':name,'z_factor':contract['z_physical_factor']*multiplier,
          'minimum':float(height.min()),'maximum':float(height.max()),'land_floor_cells':int(floor.sum()),
          'land_floor_fraction':float(floor.sum()/N**2),'land_slope_degrees_p50_p95_p99':np.percentile(slope[~sea],[50,95,99]).tolist(),
          'land_slope_over_30_degrees_cells':int(((slope>30)&~sea).sum()),
          'source_dsm_below_zero_land_cells':int(((dsm<0)&~allwater).sum())})
        spec={'ncols':N,'nrows':N,'cellsize':CELL,'xllcorner':TB_X,'yllcorner':TB_Y,'height_min':-12.001,'height_max':100,'controls':[]}
        save_json(EVIDENCE/f'{name}.ascii-spec.json',spec)
        print('HEIGHT '+name,flush=True)
    # A four-material prototype with vanilla paths verified against local extraction.
    index=np.zeros((N,N),dtype='uint8')
    index[cover==10]=1
    index[np.isin(cover,[20,30,40])]=2
    index[cover==90]=3
    index[allwater]=0
    mask_palette=np.array([[0,0,0],[0,255,0],[255,0,0],[0,0,255]],dtype='uint8')
    Image.fromarray(mask_palette[index]).save(SOURCE/'mask_preview.png')
    display={0:(198,80,182),10:(67,105,63),20:(116,135,80),30:(151,163,105),40:(179,175,117),50:(173,164,153),60:(170,153,125),70:(229,233,233),80:(103,165,192),90:(94,130,109),95:(71,115,75),100:(176,177,140)}
    rgb=np.zeros((N,N,3),dtype='uint8')
    for code,color in display.items():rgb[cover==code]=color
    rgb[allwater]=display[80]
    Image.fromarray(rgb).save(SOURCE/'sat_preview.png')
    for name in ['sat_preview','mask_preview']:
        (SOURCE/(name+'.pgw')).write_text(f'{CELL}\n0\n0\n{-CELL}\n{TB_X+CELL/2}\n{TB_Y+SIZE-CELL/2}\n',encoding='ascii')
    legend=Image.new('RGB',(256,64))
    draw=ImageDraw.Draw(legend)
    for i,color in enumerate(mask_palette.tolist()):draw.rectangle([i*64,0,(i+1)*64-1,63],fill=tuple(color))
    legend.save(SOURCE/'mapLegend.png')
    names=['cp_gravel','cp_conifer_common1','cp_grass','cp_grass_tall']
    cfg='class Layers\n{\n'
    for name in names:cfg+=f'    class {name} {{ material = "DZ\\surfaces\\data\\terrain\\{name}.rvmat"; }};\n'
    cfg+='};\nclass Legend\n{\n    picture = "DayZ_Baltic_12km_dev\\source\\mapLegend.png";\n    class Colors\n    {\n'
    for name,color in zip(names,mask_palette.tolist()):cfg+=f'        {name}[] = {{{{{color[0]},{color[1]},{color[2]}}}}};\n'
    cfg+='    };\n};\n'
    (SOURCE/'layers.cfg').write_text(cfg,encoding='ascii')
    for name in ['roads','rivers','coastline','border']:write_shape(name,layers[name],'line')
    write_shape('water',layers['water'],'polygon');write_shape('places',layers['places'],'point')
    write_shape('ocean',[(ocean,{'osm_id':'derived/coastline','name':'Gulf of Finland'})],'polygon')
    water_union=unary_union([g for g,_ in layers['water']]).difference(ocean)
    write_shape('water_coverage_union',[(water_union,{'osm_id':'derived/water-coverage','name':'Coverage only; no shared water level'})],'polygon')
    # Record larger water bodies and their original surface elevations, without flattening.
    lakes=[]
    for geom,props in sorted(layers['water'],key=lambda item:item[0].area,reverse=True)[:100]:
        mask=rasterize([(geom,1)],out_shape=(N,N),transform=GAME_TRANSFORM,dtype='uint8').astype(bool)&~sea
        if mask.sum()<4:continue
        z=dsm[mask]
        lakes.append({'osm_id':props.get('osm_id'),'name':props.get('name:en',props.get('name','')),
          'water_type':props.get('water',props.get('waterway','unknown')),'game_area_m2':geom.area,
          'cells':int(mask.sum()),'dsm_median_egm2008':float(np.median(z)),
          'dsm_p10_p90':np.percentile(z,[10,90]).tolist(),
          'physical_surface_m':float(np.median(z)*contract['z_physical_factor']),
          'relief3x_surface_m':float(np.median(z)*contract['z_physical_factor']*3),
          'water_asset_status':'NOT_PLACED; GIS surface reference only'})
    save_json(EVIDENCE/'water-body-inventory.json',lakes)
    save_json(EVIDENCE/'prototype-summary.json',{'terrain_variants':terrain_stats,
      'ocean_cells':int(sea.sum()),'inland_water_cells':int((water&~sea).sum()),
      'worldcover_unclassified_cells':int((cover==0).sum()),
      'worldcover_unclassified_non_ocean_cells':int(((cover==0)&~sea).sum()),
      'land_area_km2':float((~allwater).sum()*CELL**2/1e6),
      'prototype_edits':['Ocean-only synthetic bathymetry: 0.08 m depth per metre from shore, capped 12 m.',
        'Dry-land minimum terrain 0.25 m to avoid accidental global-sea flooding in preview; inland water excluded from this floor, per-cell delta rasters retained.',
        'Inland water surfaces are GIS references only; no terrain-wide sea flattening, no water objects or beds generated.'],
      'satellite':'Provisional WorldCover colorization, not aerial imagery or final artwork.',
      'worldcover_zero_policy':'Original zeros preserved in GIS; magenta preview unless covered by a water polygon, gravel in material prototype.',
      'runtime':'NOT_TESTED'} )
    print('IMPORT CANDIDATE COMPLETE',flush=True)

if __name__=='__main__':main()
