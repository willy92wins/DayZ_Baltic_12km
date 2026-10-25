"""Publish the frozen map outline and editable planning layers, not placed assets."""
import json
from pathlib import Path
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.colors import LinearSegmentedColormap
import shapefile
from shapely.geometry import box, shape, Point, mapping
from shapely.affinity import scale
from shapely.ops import transform

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools'))
from geo_common import game_xy, GAME_CRS, MERC_TO_WGS, XMIN, YMIN, SCALE
from prepare_regional_outline import sha, save


def rings(g):
    if g.is_empty:
        return
    if g.geom_type == 'Polygon':
        yield list(g.exterior.coords)
        for ring in g.interiors:
            yield list(ring.coords)
    elif g.geom_type in ('LineString', 'LinearRing'):
        yield list(g.coords)
    else:
        for part in g.geoms:
            yield from rings(part)


def main():
    out = ROOT/'derived/outline-v3'
    if out.exists():
        receipt = json.loads((ROOT/'evidence/regional-outline-v3/outline-manifest.json').read_text())
        if any(sha(ROOT/f['path']) != f['sha256'] for f in receipt['files']):
            raise ValueError('Existing planning layer changed; do not overwrite')
    ref = ROOT/'tests/regional_outline_v3/reference.npz'
    if sha(ref) != 'b5ca00409f0814285c82a1fe6688fe49719574eadde415de08443ffedcbc574d':
        raise ValueError('Frozen regional reference drift')
    r = np.load(ref)
    design = json.loads((ROOT/'evidence/navigation/selective-relief-v1/design.json').read_text(encoding='utf-8'))
    old = json.loads((ROOT/'evidence/regional-outline-v1/outline_tb.geojson').read_text(encoding='utf-8'))
    reserve = shape(old['features'][0]['geometry'])
    sx, sy, sw, sh = np.array(design['closeup_xywh_km'])*1000
    frame = box(200000, 0, 212288, 12288)
    spb = box(200000+sx, sy, 200000+sx+sw, sy+sh)
    fit = json.loads((ROOT/'evidence/narva/evidence/narva-fit.json').read_text())
    narva = Point(*fit['bridge_centre_tb']).buffer(400)
    features = [('frame', 'Approved 12.288 km frame', frame),
                ('spb', 'Complete closeup, same XY scale', spb),
                ('reserve', 'Conservation envelope, not legal boundary', reserve),
                ('narva', 'Preserved navigation pilot', narva)]
    for zone in design['zones']:
        x, y = np.array(zone['centre_game_km'])*1000
        dx, dy = np.array(zone['ellipse_diameters_km'])*500
        features.append(('relief_'+zone['id'], 'Study zone, measured heights govern',
                         scale(Point(200000+x, y).buffer(1, quad_segs=64), xfact=dx, yfact=dy)))
    out.mkdir(parents=True, exist_ok=True)
    groups = {'areas': features, 'roads': []}
    for f in old['features'][1:]:
        g = shape(f['geometry']).intersection(frame)
        groups['roads'].append(('road', 'Reference alignment, no finished grade', g))
    # POLYLINE rings are an intentional Terrain Builder planning overlay.
    records = {}
    for name, items in groups.items():
        count = 0
        with shapefile.Writer(str(out/name), shapeType=shapefile.POLYLINE, encoding='utf-8') as w:
            w.field('role', 'C', 24); w.field('status', 'C', 80)
            for role, status, g in items:
                for line in rings(g):
                    w.line([line]); w.record(role, status); count += 1
        (out/f'{name}.prj').write_text(GAME_CRS, encoding='ascii')
        (out/f'{name}.cpg').write_text('UTF-8', encoding='ascii')
        with shapefile.Reader(str(out/name), encoding='utf-8') as reader:
            if len(reader) != count or reader.shapeType != shapefile.POLYLINE:
                raise ValueError('Planning layer reread mismatch')
            for s in reader.iterShapes():
                a = np.array(s.points)
                if not np.isfinite(a).all() or (a[:,0] < 199999.999).any() or (a[:,0] > 212288.001).any() or (a[:,1] < -.001).any() or (a[:,1] > 12288.001).any():
                    raise ValueError('Planning layer outside approved frame')
        records[name] = count
    def inverse(x,y,z=None):
        return MERC_TO_WGS.transform((np.asarray(x)-200000)/SCALE+XMIN, np.asarray(y)/SCALE+YMIN)
    collection = {'type':'FeatureCollection', 'features':[
        {'type':'Feature', 'properties':{'role':role,'status':status}, 'geometry':mapping(transform(inverse,g))}
        for role,status,g in features]}
    save(out/'areas_wgs84.geojson', collection)
    # Geography is shown from the native height sample footprint, with water
    # explicitly labelled as reference extent rather than accepted water level.
    fig, ax = plt.subplots(figsize=(12,13), layout='constrained')
    h = r['candidate']
    ax.set_facecolor('#b3d7e6')
    land_colors = LinearSegmentedColormap.from_list('baltic_land', ['#d6dfbd','#85ab70','#446e49','#ad9069'])
    ax.imshow(np.ma.masked_where(r['water'], h), origin='upper',
              extent=(-.003,12.285,-.003,12.285), cmap=land_colors, vmin=0, vmax=115)
    road_lines = [(np.array(line)-[200000,0])/1000 for _,_,g in groups['roads'] for line in rings(g)]
    ax.add_collection(LineCollection(road_lines, colors='#d8a969', linewidths=.5, alpha=.9))
    colors = {'frame':'#1a252d','spb':'#2b559a','reserve':'#c52a87','narva':'#6431a1','relief_A':'#8c542f','relief_B':'#8c542f'}
    for role, _, g in features:
        for line in rings(g):
            a = (np.array(line)-[200000,0])/1000
            ax.plot(a[:,0],a[:,1], color=colors[role], lw=1.8, ls='--' if role.startswith('relief') else '-')
    geo = json.loads((ROOT/'evidence/georef-v0.json').read_text())
    for p in geo['points']:
        if p['name'] not in ['San Petersburgo','Narva','Luga','Gatchina','Sosnovy Bor','Novgorod','Gdov']:
            continue
        x,y=game_xy(p['lon'],p['lat'])
        ax.plot(float(x)/1000,float(y)/1000,'o',ms=3,color='#182a30')
        ax.annotate(p['name'],(float(x)/1000,float(y)/1000),xytext=(4,5),textcoords='offset points',fontsize=9,
                    bbox={'facecolor':'white','alpha':.85,'edgecolor':'none','pad':2})
    ax.text(8.2,5.3,'MSHINSKOYE\nReserva · bosque / humedal',ha='center',fontsize=10,
            bbox={'facecolor':'white','alpha':.85,'edgecolor':'none','pad':4})
    ax.text(5.1,8.1,'A · colinas',fontsize=10)
    ax.text(3.7,1.8,'B · relieve sur',fontsize=10)
    ax.set(xlim=(0,12.288),ylim=(0,12.288),xlabel='Este en el juego (km)',ylabel='Norte en el juego (km)',aspect='equal')
    ax.set_xticks(range(13)); ax.set_yticks(range(13)); ax.grid(alpha=.12)
    legend=[Line2D([0],[0],color=colors[k],lw=2,label=t) for k,t in [('spb','Closeup íntegro de San Petersburgo'),('reserve','Envolvente de conservación'),('narva','Piloto de Narva preservado')]]
    legend += [Line2D([0],[0],color='#d8a969',lw=2,label='Conexiones principales de referencia'),
               Patch(facecolor='#b3d7e6',label='Agua de referencia; cotas regionales pendientes')]
    ax.legend(handles=legend,loc='upper left',fontsize=8,framealpha=.93)
    fig.suptitle('BÁLTICO · OUTLINE REGIONAL V3\n12,288 × 12,288 km · terreno y reservas de trazado',fontsize=17)
    fig.supxlabel('Relieve nativo persistido: máximo 109,57 m. Sin población ni árboles colocados.\nLímites de diseño trazables; no equivalen a agua, carreteras ni navegación regional aceptadas.',fontsize=10)
    fig.savefig(ROOT/'evidence/regional-outline-v3/outline.png',dpi=160)
    plt.close(fig)
    save(ROOT/'evidence/regional-outline-v3/outline-manifest.json', {
        'status':'PASS_PLANNING_LAYER_EXPORT', 'reference_sha256':sha(ref), 'records':records,
        'tb_origin':[200000,0], 'game_size_m':12288, 'grid_vertices_bounds':[200000,0,212282,12282],
        'files':[{ 'path':str(f.relative_to(ROOT)), 'bytes':f.stat().st_size,'sha256':sha(f)} for f in sorted(out.iterdir())],
        'limits':['SHP uses local engineering metres; areas_wgs84.geojson uses WGS84.',
                  'Areas are design protections and zones. Roads are reference lines, not constructed or graded.',
                  'Water and vegetation are preserved references, not completed regional gameplay.']})
    print(json.dumps(records))


if __name__ == '__main__':
    main()
