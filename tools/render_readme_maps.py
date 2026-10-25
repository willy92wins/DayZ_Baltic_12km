"""Render geographic README illustrations from the project's existing GIS data.

These are source-region maps, not screenshots or gameplay/loot-zone proofs.
Run with the locked GIS environment; inputs and output hashes are recorded.
"""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.collections import LineCollection
from matplotlib.colors import to_rgb
import numpy as np
from pyproj import Transformer
import rasterio
from shapely.geometry import shape, box
from shapely.ops import transform


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    inputs = [root / 'evidence/aprobacion.json']
    approval = json.loads(inputs[0].read_text(encoding='utf-8'))
    if approval['status'] != 'USER_APPROVED_GEOGRAPHIC_SCOPE_V0':
        raise ValueError('Expected the approved geographic scope')
    projection = Transformer.from_crs(4326, 3857, always_xy=True)
    polygon = np.array(approval['frame_polygon_lonlat_approximate'])
    west, south = projection.transform(*polygon.min(axis=0))
    east, north = projection.transform(*polygon.max(axis=0))
    gis = args.data_root / 'derived/gis'
    args.output.mkdir(parents=True, exist_ok=True)
    cover_path = gis / 'worldcover_2021_3857.tif'
    inputs.append(cover_path)
    with rasterio.open(cover_path) as src:
        if src.crs.to_epsg() != 3857 or not np.allclose(
                tuple(src.bounds), (west, south, east, north), atol=.01, rtol=0):
            raise ValueError('WorldCover raster does not match the approved crop')
        cover = src.read(1)

    # Categorical land-cover data, rendered here as new cartography.
    bg, ink, muted, water, accent = '#0c2027', '#f3eedb', '#9ab3b4', '#1e5264', '#edbc75'
    palette = {0: water, 10: '#3d6252', 20: '#61765b', 30: '#8c956e',
               40: '#b0a97a', 50: '#cfbd9b', 60: '#929780', 70: '#e4dfcb',
               80: water, 90: '#607e71', 95: '#496b60', 100: '#86947c'}
    rgb = np.empty((*cover.shape, 3))
    for value in np.unique(cover):
        if int(value) not in palette:
            raise ValueError(f'Unknown WorldCover class {value}')
        rgb[cover == value] = to_rgb(palette[int(value)])
    layers = {}
    for name in ('roads', 'rivers', 'border', 'coastline', 'water', 'places'):
        path = gis / f'osm_{name}_wgs84.geojson'
        inputs.append(path)
        features = json.loads(path.read_text(encoding='utf-8'))['features']
        layers[name] = [(transform(projection.transform, shape(f['geometry'])),
                         f['properties']) for f in features]

    def pieces(geom):
        if geom.geom_type in ('LineString', 'Polygon'):
            yield geom
        elif hasattr(geom, 'geoms'):
            for part in geom.geoms:
                yield from pieces(part)

    def canvas(ax, bounds, detail=False):
        clip = box(*bounds)
        ax.set_facecolor(water)
        ax.imshow(rgb, extent=(west, east, south, north), origin='upper',
                  interpolation='nearest', zorder=0)
        if detail:
            # Vector water preserves narrow channels at the closer map scale.
            for geom, _ in layers['water']:
                if geom.intersects(clip):
                    for part in pieces(geom):
                        if part.geom_type == 'Polygon':
                            x, y = part.exterior.xy
                            ax.fill(x, y, color=water, linewidth=0, zorder=1)
                            for ring in part.interiors:
                                x, y = ring.xy
                                ax.fill(x, y, color=palette[10], linewidth=0, zorder=1)
        for name, color, width, linestyle in (
                ('roads', '#d6cdb0', .42 if detail else .3, '-'),
                ('rivers', '#70acb7', .65 if detail else .45, '-'),
                ('coastline', '#729994', .55, '-'),
                ('border', accent, 1.5, (0, (4, 3)))):
            segments = []
            for geom, props in layers[name]:
                if name == 'roads' and props.get('highway') not in {
                        'motorway', 'trunk', 'primary', 'secondary',
                        'motorway_link', 'trunk_link', 'primary_link',
                        *({'tertiary', 'residential'} if detail else set())}:
                    continue
                if geom.intersects(clip):
                    segments.extend(np.asarray(p.coords) for p in pieces(geom)
                                    if p.geom_type == 'LineString')
            ax.add_collection(LineCollection(segments, colors=color,
                              linewidths=width, linestyles=linestyle, zorder=2))
        ax.set(xlim=(bounds[0], bounds[2]), ylim=(bounds[1], bounds[3]))
        ax.set_aspect('equal')
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_color('#36525a')
        ax.text(.96, .95, 'N ↑', transform=ax.transAxes, color=ink,
                ha='right', fontsize=12, weight='bold', zorder=5)

    labels_used = []

    def city(ax, english, label, offset=(8, 8), align='left', size=12):
        matches = [(g, p) for g, p in layers['places']
                   if p.get('name:en', p.get('name')) == english]
        if len(matches) != 1:
            raise ValueError(f'Ambiguous place {english}: {len(matches)}')
        g, props = matches[0]
        ax.scatter(g.x, g.y, s=26, c=accent, edgecolors=bg, zorder=5)
        ax.annotate(label, (g.x, g.y), xytext=offset, textcoords='offset points',
                    ha=align, color=ink, fontsize=size, weight='bold', zorder=6,
                    path_effects=[pe.withStroke(linewidth=4, foreground=bg)])
        labels_used.append({'label': label, 'osm_id': props['osm_id']})

    def note(ax, lon, lat, label, size=13):
        x, y = projection.transform(lon, lat)
        ax.text(x, y, label, color='#bdd7d8', fontsize=size, ha='center',
                style='italic', zorder=4,
                path_effects=[pe.withStroke(linewidth=2, foreground=water)])

    plt.rcParams.update({'font.family': 'DejaVu Sans'})
    fig = plt.figure(figsize=(16, 10.5), dpi=120, facecolor=bg)
    ax = fig.add_axes((.37, .075, .60, .89))
    canvas(ax, (west, south, east, north))
    city(ax, 'Saint Petersburg', 'SAN PETERSBURGO', (-10, -18), 'right', 12)
    city(ax, 'Narva', 'NARVA', (-12, 10), 'right', 13)
    city(ax, 'Kronstadt', 'Kotlin / Kronstadt', (-9, 12), 'right', 10)
    city(ax, 'Luga', 'Luga', (8, 7), size=11)
    note(ax, 28.60, 59.96, 'GOLFO DE FINLANDIA', 12)
    note(ax, 31.38, 60.12, 'Ládoga', 10)
    note(ax, 27.75, 58.48, 'Peipus', 11)
    note(ax, 31.41, 58.22, 'Ilmen', 10)
    fig.text(.045, .91, 'DAYZ  /  MAPA EN DESARROLLO', color=accent, fontsize=12)
    fig.text(.045, .80, 'BALTIC', color=ink, fontsize=56, weight='bold')
    fig.text(.047, .744, 'DOS ORILLAS.\nUN TERRITORIO EN DISPUTA.',
             color=ink, fontsize=16, linespacing=1.6)
    fig.text(.047, .58, '01  SAN PETERSBURGO', color=accent, fontsize=13, weight='bold')
    fig.text(.047, .515, 'La gran urbe, el Neva\ny la salida al Báltico.', color=ink, fontsize=14, linespacing=1.5)
    fig.text(.047, .40, '02  NARVA', color=accent, fontsize=13, weight='bold')
    fig.text(.047, .335, 'El río, la frontera\ny el foco del conflicto.', color=ink, fontsize=14, linespacing=1.5)
    fig.text(.047, .22, '12,288 × 12,288 km', color=ink, fontsize=20, weight='bold')
    fig.text(.047, .153, 'Región real condensada.\nHistoria alternativa. Supervivencia.', color=muted, fontsize=12, linespacing=1.6)
    fig.text(.045, .035, 'ÁREA DE INSPIRACIÓN  ·  Cartografía de referencia; no captura del juego.', color=muted, fontsize=10)
    fig.text(.97, .035, '© OpenStreetMap contributors  ·  ESA WorldCover 2021', color=muted, fontsize=9, ha='right')
    fig.savefig(args.output / 'baltic-region.png', facecolor=bg)
    plt.close(fig)

    fig = plt.figure(figsize=(16, 9), dpi=120, facecolor=bg)
    fig.text(.045, .94, 'LA GEOGRAFÍA DETRÁS DEL CONFLICTO', color=ink, fontsize=25, weight='bold')
    fig.text(.045, .895, 'Dos acercamientos al territorio real que inspira Baltic.', color=muted, fontsize=13)
    configs = [((.045, .18, .445, .65), (27.93, 59.25, 28.44, 59.51)),
               ((.525, .18, .445, .65), (29.57, 59.73, 30.65, 60.14))]
    axes = []
    for rect, bounds in configs:
        ax = fig.add_axes(rect)
        x0, y0 = projection.transform(bounds[0], bounds[1])
        x1, y1 = projection.transform(bounds[2], bounds[3])
        canvas(ax, (x0, y0, x1, y1), detail=True)
        axes.append(ax)
    city(axes[0], 'Narva', 'Narva', (-12, 12), 'right', 12)
    city(axes[0], 'Ivangorod', 'Ivangorod', (12, -16), size=12)
    city(axes[0], 'Narva-Jõesuu', 'Narva-Jõesuu', (10, 10), size=10)
    note(axes[0], 28.17, 59.29, 'Embalse de Narva', 11)
    city(axes[1], 'Saint Petersburg', 'San Petersburgo', (7, 10), size=12)
    city(axes[1], 'Kronstadt', 'Kotlin / Kronstadt', (5, 12), size=11)
    fig.text(.045, .135, 'NARVA  /  ESTONIA Y RUSIA', color=accent, fontsize=14, weight='bold')
    fig.text(.045, .098, 'El cruce entre dos orillas concentra la tensión del lore.', color=ink, fontsize=11)
    fig.text(.525, .135, 'SAN PETERSBURGO  /  RUSIA', color=accent, fontsize=14, weight='bold')
    fig.text(.525, .098, 'Islas, canales y una gran ciudad abierta al golfo.', color=ink, fontsize=11)
    fig.text(.045, .042, 'Línea discontinua: frontera OSM. Vías y agua de referencia; zonas de loot aún sin delimitar.', color=muted, fontsize=9)
    fig.text(.045, .019, '© OpenStreetMap contributors (ODbL) · ESA WorldCover 2021 (CC BY 4.0) · Colores cartográficos interpretativos.', color=muted, fontsize=9)
    fig.savefig(args.output / 'narva-saint-petersburg.png', facecolor=bg)
    plt.close(fig)

    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    manifest = {
        'purpose': 'Geographic illustrations; not gameplay captures or implemented loot zones',
        'source_crs': 'EPSG:3857', 'approved_bbox_lonlat': polygon.tolist(),
        'script_sha256': digest(Path(__file__)),
        'inputs': [{'path': str(p.relative_to(root) if p.is_relative_to(root)
                                  else p.relative_to(args.data_root)),
                    'sha256': digest(p)} for p in inputs],
        'place_labels': labels_used,
        'outputs': {p.name: digest(p) for p in args.output.glob('*.png')},
    }
    (args.output / 'map-sources.json').write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'outputs': list(manifest['outputs']), 'inputs': len(inputs)}))


if __name__ == '__main__':
    main()
