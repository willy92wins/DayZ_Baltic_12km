"""Read-only regional constraints for terrain-first work; no navigation acceptance."""
import json
from collections import defaultdict
import numpy as np
import shapefile
from shapely import make_valid
from shapely.geometry import shape, box, mapping
from shapely.ops import unary_union
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from waterway_common import ROOT, BASE_SHA, RIVERS, sha, river_features, river_group, tb_geometry


def parts(g, kind):
    if g.geom_type == kind:
        yield g
    elif hasattr(g, 'geoms'):
        for child in g.geoms:
            yield from parts(child, kind)


def main():
    folder = ROOT/'evidence/navigation'
    audit_path = folder/'baseline-waterways.json'
    audit = json.loads(audit_path.read_text())
    if audit['native_sha256'] != BASE_SHA or audit['river_source_sha256'] != sha(RIVERS):
        raise ValueError('Baseline river audit is stale')
    water_file = ROOT/'derived/gis/osm_water_wgs84.geojson'
    inventory_file = ROOT/'evidence/water-body-inventory.json'
    water_data = json.loads(water_file.read_text(encoding='utf-8'))
    inventory = {r['osm_id']: r for r in json.loads(inventory_file.read_text())}
    water = []
    named = {}
    frame = box(200000, 0, 212282, 12282)
    for f in water_data['features']:
        geom = make_valid(tb_geometry(shape(f['geometry']))).intersection(frame)
        water.extend(parts(geom, 'Polygon'))
        oid = f['properties'].get('osm_id')
        if oid in inventory and inventory[oid]['game_area_m2'] > 100000:
            named[oid] = (geom, inventory[oid])
    ocean_path = ROOT/'derived/tb/source/vectors/ocean.shp'
    with shapefile.Reader(str(ocean_path)) as reader:
        ocean = unary_union([make_valid(shape(s.__geo_interface__)) for s in reader.iterShapes()])
    # Union before measuring area: large lakes can be mapped by nested relations.
    wet = unary_union(water+[ocean]).intersection(frame)
    dry = frame.difference(wet)
    islands = [p for p in parts(dry, 'Polygon') if not p.intersects(frame.boundary)]
    grouped = defaultdict(list)
    for f in river_features():
        group = river_group(f['properties'])
        if group:
            g = tb_geometry(shape(f['geometry'])).intersection(frame)
            grouped[group].extend(parts(g, 'LineString'))
    result = {}
    conflict_features = []
    for name, lines in grouped.items():
        axis = unary_union(lines)
        core = axis.buffer(12)
        support = axis.buffer(12+6*np.sqrt(2))
        hits = []
        for i, island in enumerate(islands):
            overlap = support.intersection(island).area
            if overlap > .01:
                hits.append({'island_index': i, 'island_area_m2': island.area,
                             'core_overlap_m2': core.intersection(island).area,
                             'grid_support_overlap_m2': overlap})
                conflict_features.append({'type':'Feature', 'geometry':mapping(island),
                    'properties':{'river':name, **hits[-1]}})
        rows = [r for r in audit['samples'] if r['river'] == name]
        result[name] = {
            'unique_axis_length_m': axis.length,
            'reference_samples': len(rows),
            'samples_width_below_24m': sum(r['reference_wet_width_m'] < 24 for r in rows),
            'samples_width_below_18m': sum(r['reference_wet_width_m'] < 18 for r in rows),
            'samples_width_below_12m': sum(r['reference_wet_width_m'] < 12 for r in rows),
            'samples_without_water_polygon': sum(r['reference_wet_width_m'] == 0 for r in rows),
            'wet_core_area_outside_reference_m2': core.difference(wet).area,
            'island_conflicts_if_uniform_widening': hits,
        }
    overlaps = []
    ids = list(named)
    for i, oid in enumerate(ids):
        a, _ = named[oid]
        for other in ids[i+1:]:
            b, _ = named[other]
            overlap = a.intersection(b).area
            if overlap > 1000:
                overlaps.append({'a':oid, 'b':other, 'overlap_m2':overlap,
                                 'fraction_of_smaller':overlap/min(a.area,b.area)})
    lakes = [{**r, 'within_frame_area_m2':g.area} for g,r in named.values()]
    report = {
        'status':'CONSTRAINTS_ONLY_NO_TERRAIN_CHANGED',
        'source_hashes':{'river':sha(RIVERS),'water':sha(water_file),
                       'inventory':sha(inventory_file),'baseline_audit':sha(audit_path),
                       'ocean_shp':sha(ocean_path)},
        'rivers':result, 'large_water_bodies':lakes,
        'overlapping_water_relations':overlaps,
        'unique_water_area_within_frame_m2':wet.area,
        'enclosed_dry_components_from_water_union':len(islands),
        'limits':[
            'River names include branches; this is not a connected travel route.',
            'Widths are sampled from reference polygons, not engine wet width.',
            'Island conflicts concern uniform 24m widening plus conservative grid support; no widening applied.',
            'Enclosed dry components include tiny polygon slivers; confirm against reference before calling each one a real island.',
            'DSM lake levels are inherited source references, not final engineering levels or bathymetry.',
            'No terrain, native project, water objects or navigation modified.']}
    (folder/'regional-hydrology-constraints.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (folder/'river-island-conflicts.geojson').write_text(json.dumps({'type':'FeatureCollection',
        'coordinate_system':'local engineering TB metres; not EPSG:4326',
        'features':conflict_features},ensure_ascii=False)+'\n',encoding='utf-8')

    fig,(ax,side)=plt.subplots(1,2,figsize=(14,10),gridspec_kw={'width_ratios':[1.7,1]},layout='constrained')
    for p in parts(wet,'Polygon'):
        a=np.asarray(p.exterior.coords)
        ax.fill((a[:,0]-200000)/1000,a[:,1]/1000,color='#abd8e8',linewidth=0)
        for hole in p.interiors:
            a=np.asarray(hole.coords)
            ax.fill((a[:,0]-200000)/1000,a[:,1]/1000,color='#eeeade',linewidth=0)
    colors={'Narva':'#b45c1b','Neva':'#2467a2','Delta Neva':'#863aac','Luga':'#43865c'}
    for name,lines in grouped.items():
        ax.add_collection(LineCollection([(np.asarray(line.coords)-[200000,0])/1000 for line in lines],
            colors=colors[name],linewidths=1.3,label=name))
    pin=[r for r in audit['samples'] if r['reference_wet_width_m'] < 12]
    ax.scatter([r['x']/1000 for r in pin],[r['z']/1000 for r in pin],s=3,c='#b02f39',label='Referencia <12m',zorder=3)
    ax.plot(2.417143,6.889885,'ko',markersize=5)
    ax.annotate('Piloto Narva',xy=(2.417143,6.889885),xytext=(.2,7.8),arrowprops={'arrowstyle':'->'},fontsize=9)
    ax.set(xlim=(0,12.282),ylim=(0,12.282),xlabel='Este del juego (km)',ylabel='Norte del juego (km)',
           title='Hidrografía de referencia y estrechamientos')
    ax.set_facecolor('#eeeade'); ax.set_aspect('equal');ax.legend(loc='lower right',fontsize=8)
    side.axis('off')
    text=['TERRENO ANTES DEL MAPEADO','',
          '1. Fondos, anchos y niveles de agua',
          '2. Orillas, islas y accesos terrestres',
          '3. Importación y pruebas en motor',
          '4. Navmesh base del WRP validado','',
          'MUESTRAS DE REFERENCIA <24m']
    for name in ('Narva','Neva','Delta Neva','Luga'):
        r=result[name]
        text.append(f"{name}: {r['samples_width_below_24m']} / {r['reference_samples']}")
    text += ['', 'PENDIENTE: NIVELES DE LAGOS',
             'Peipus / embalse Narva / Ilmen',
             'El DSM mide superficie, no fondo.',
             'No bajar todos los lagos al mar.','',
             'SAN PETERSBURGO',
             'Conservar islas y brazos del delta.',
             'Revisar conflictos antes de ensanchar.','',
             'Solo auditoría GIS; no prueba de juego.',
             'Las muestras no prueban continuidad.',
             'La navmesh se regenera tras el mapeado.']
    side.text(.02,.96,'\n'.join(text),va='top',fontsize=10.5,linespacing=1.5)
    fig.suptitle('Baltic 12,288 km · preparación regional del terreno',fontsize=16)
    for ext in ('png','pdf'):
        fig.savefig(folder/f'regional-hydrology-constraints.{ext}',dpi=160)
    compact = {name:{k:v for k,v in row.items() if k != 'island_conflicts_if_uniform_widening'}
               for name,row in result.items()}
    print(json.dumps({'rivers':compact,'overlaps':overlaps},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
