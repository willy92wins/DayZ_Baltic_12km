"""Plot a design overlay on existing GIS. Never write terrain or runtime files."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import rasterio
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
from matplotlib.patches import Ellipse, Rectangle

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools'))
from geo_common import game_xy


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    out = ROOT/'evidence/navigation/selective-relief-v1'
    out.mkdir(parents=True, exist_ok=True)
    paths = {
        'relief3x': ROOT/'source/baltic_relief3x_2048_6m.asc',
        'ocean': ROOT/'derived/gis/ocean_mask_game.tif',
        'inland_water': ROOT/'derived/gis/inland_water_mask_game.tif',
        'landcover': ROOT/'derived/gis/worldcover_2021_3857.tif',
        'georef': ROOT/'evidence/georef-v0.json',
        'approval': ROOT/'evidence/aprobacion.json',
        'coordinate_contract': ROOT/'evidence/coordinate-contract.json',
    }
    hashes = {k: digest(p) for k, p in paths.items()}
    arrays = {}
    for name in ['relief3x', 'ocean', 'inland_water', 'landcover']:
        with rasterio.open(paths[name]) as src:
            arrays[name] = src.read(1)
    z, cover = arrays['relief3x'], arrays['landcover']
    if any(a.shape != (2048, 2048) for a in arrays.values()):
        raise ValueError('Unexpected source dimensions')
    if not np.isfinite(z).all():
        raise ValueError('Non-finite source heights')
    water = (arrays['ocean'] != 0) | (arrays['inland_water'] != 0) | (cover == 80)
    wetland = cover == 90
    geo = json.loads(paths['georef'].read_text(encoding='utf-8'))
    r, f = geo['detail_pixel'], geo['frame_pixel']
    closeup = [(r['x']-f['x'])/f['width']*12.288,
               (f['y']+f['height']-r['y']-r['height'])/f['height']*12.288,
               r['width']/f['width']*12.288,
               r['height']/f['height']*12.288]
    zones = [
        {'id': 'A', 'name': 'Interior al oeste de Gatchina',
         'centre_game_km': [6.1, 7.85], 'ellipse_diameters_km': [4.0, 3.0],
         'selected_crest_target_m': [80, 140]},
        {'id': 'B', 'name': 'Sur, entre Peipus y Luga',
         'centre_game_km': [4.55, 1.75], 'ellipse_diameters_km': [4.3, 2.9],
         'selected_crest_target_m': [100, 160]},
    ]
    reserve_design = {
        'name': 'Mshinskoye — conservación y biomas',
        'centre_game_km': [8.2, 5.2], 'ellipse_diameters_km': [2.5, 2.8],
        'boundary_status': 'CONSERVATIVE_DESIGN_ENVELOPE_NOT_VERIFIED_RESERVE_BOUNDARY',
        'priority': 'Water, wetlands and natural area override proposed uplifts',
        'vegetation_intent': 'Dense forest pockets, transitional woodland, clearings and wetlands',
        'placement_stage': 'After terrain and base navigation; P10/P13',
    }
    x = (np.arange(2048)+.5)*.006
    y = 12.288-(np.arange(2048)+.5)*.006
    xx, yy = np.meshgrid(x, y)
    dry = ~water & ~wetland
    for zone in zones:
        cx, cy = zone['centre_game_km']
        dx, dy = zone['ellipse_diameters_km']
        if not (0 <= cx-dx/2 < cx+dx/2 <= 12.288 and
                0 <= cy-dy/2 < cy+dy/2 <= 12.288):
            raise ValueError('Design envelope outside approved map')
        selection = (((xx-cx)/(dx/2))**2+((yy-cy)/(dy/2))**2 <= 1) & dry
        zone['source3x_dry_cells'] = int(selection.sum())
        zone['source3x_dry_height_p50_p90_p99_max_m'] = [
            *np.percentile(z[selection], [50, 90, 99]).tolist(),
            float(z[selection].max())]

    fig, (ax, side) = plt.subplots(1, 2, figsize=(14, 10),
                                  gridspec_kw={'width_ratios': [1.9, 1]})
    fig.patch.set_facecolor('#f5f3ed')
    reduced = z[::4, ::4]
    rgb = LightSource(azdeg=315, altdeg=42).shade(
        reduced, cmap=plt.get_cmap('YlGn'), vmin=0, vmax=33,
        vert_exag=5, dx=24, dy=24, blend_mode='soft')
    rgb[water[::4, ::4]] = [0.57, .77, .84, 1]
    rgb[wetland[::4, ::4] & ~water[::4, ::4]] = [.49, .66, .59, 1]
    ax.imshow(rgb, extent=(0, 12.288, 0, 12.288), origin='upper')
    ax.add_patch(Rectangle(closeup[:2], *closeup[2:], fill=False,
                           ec='#325c99', lw=1.4, ls='--'))
    ax.add_patch(Ellipse(reserve_design['centre_game_km'],
                        *reserve_design['ellipse_diameters_km'],
                        fill=False, ec='#125848', lw=2, ls='--'))
    ax.text(closeup[0]+.12, closeup[1]+closeup[3]-.2,
            'CLOSEUP CONSERVADO', va='top', color='#24416c', fontsize=9,
            bbox={'facecolor': 'white', 'edgecolor': 'none', 'alpha': .88})
    for zone in zones:
        colour = '#963f1c' if zone['id'] == 'A' else '#7c3881'
        cx, cy = zone['centre_game_km']
        dx, dy = zone['ellipse_diameters_km']
        ax.add_patch(Ellipse((cx, cy), dx, dy, fill=False, ec=colour, lw=2))
        lo, hi = zone['selected_crest_target_m']
        ax.text(cx, cy, f"{zone['id']}  ·  {lo}–{hi} m\ncrestas propuestas",
                ha='center', va='center', fontsize=11, weight='bold', color=colour,
                bbox={'facecolor': '#fffaf0', 'edgecolor': 'none', 'alpha': .93, 'pad': 5})
    labels = {'Narva': (6, 7), 'Kingisepp': (7, -13), 'Gatchina': (7, -12),
              'Luga': (7, 7), 'San Petersburgo': (-70, 13),
              'Sosnovy Bor': (-35, 8), 'Gdov': (7, 5), 'Tosno': (7, -12)}
    for point in geo['points']:
        gx, gy = game_xy(point['lon'], point['lat'])
        gx, gy = float(gx)/1000, float(gy)/1000
        ax.scatter([gx], [gy], s=16, c='#25372b', zorder=5)
        ax.annotate(point['name'], (gx, gy),
                    xytext=labels.get(point['name'], (6, 6)),
                    textcoords='offset points', fontsize=8,
                    bbox={'facecolor': 'white', 'edgecolor': 'none', 'alpha': .85})
    # Existing screenshot-based natural-area reference, not a legal boundary.
    reserve = ((740+20)/1135*12.288, (1099-624)/1135*12.288)
    ax.annotate('RESERVA PRIORITARIA\nBosque denso + claros + humedales', reserve,
                xytext=(15, 14), textcoords='offset points', fontsize=9,
                arrowprops={'arrowstyle': '-', 'color': '#254539'},
                bbox={'facecolor': '#f5f3ed', 'edgecolor': 'none', 'alpha': .9})
    ax.text(.45, 5.65, 'NARVA / FRONTERA\nCruce y cauce protegidos', fontsize=9,
            color='#344034', bbox={'facecolor': 'white', 'edgecolor': 'none', 'alpha': .88})
    ax.set(xlim=(0, 12.288), ylim=(0, 12.288), xlabel='Este · km de juego',
           ylabel='Norte · km de juego', aspect='equal')
    ax.set_xticks(range(0, 13, 2)); ax.set_yticks(range(0, 13, 2))
    side.axis('off')
    blocks = [
        ('CRITERIO APROBADO', 'Exagerar Z por zonas y jugabilidad.\nEncuadre, agua y conexiones conservados.'),
        ('COTAS PROPUESTAS', 'Interior ondulado: lomos de 30–70 m.\nA: crestas de 80–140 m.\nB: crestas de 100–160 m.\nHitos aislados: hasta 180–200 m\nsi encajan con los perfiles y accesos.'),
        ('RESERVA Y BIOMAS', 'Núcleos de bosque muy denso,\nclaros, transiciones y humedales.\nVerde: envolvente de conservación;\nperímetro real por contrastar.\nCotas del agua: diseño separado.'),
        ('CARRETERAS', 'Rasantes propias por valles y pasos.\nObjetivo inicial: 6% principal / 8% secundaria.\nTransiciones suaves y prueba con vehículo.\nSon objetivos, no límites del motor.'),
        ('QUÉ MUESTRA ESTE PLANO', 'Fondo: relieve ×3 existente, máx. 32,6 m.\nEl sombreado está exagerado para leerlo.\nElipses: áreas de estudio, no máscaras finales.\nLas alturas nuevas aún no están aplicadas.'),
    ]
    pos = .96
    for heading, body in blocks:
        side.text(0, pos, heading, transform=side.transAxes, fontsize=11,
                  weight='bold', color='#223c31', va='top')
        side.text(0, pos-.042, body, transform=side.transAxes, fontsize=10,
                  linespacing=1.5, color='#37443d', va='top')
        pos -= .112 + body.count('\n')*.024
    fig.suptitle('BÁLTICO · RELIEVE SELECTIVO PARA JUGABILIDAD', x=.055,
                 ha='left', fontsize=19, weight='bold', color='#233b31')
    fig.text(.055, .025, 'Propuesta de diseño · no importada en Terrain Builder · no valida navegación ni rendimiento.\n'
             'Fuentes existentes: Copernicus GLO-30, ESA WorldCover 2021 y referencias geográficas del proyecto.',
             fontsize=8, color='#536057')
    fig.subplots_adjust(left=.055, right=.985, top=.91, bottom=.09, wspace=.14)
    fig.savefig(out/'zonificacion.png', dpi=160, facecolor=fig.get_facecolor())
    fig.savefig(out/'zonificacion.pdf', facecolor=fig.get_facecolor())
    plt.close(fig)
    # Verify that plotting did not modify any input.
    if hashes != {k: digest(p) for k, p in paths.items()}:
        raise ValueError('Source changed during plotting')
    record = {
        'status': 'DESIGN_ONLY_SELECTIVE_Z_AUTHORIZED_NUMERIC_TARGETS_PROPOSED',
        'date': '2026-09-30',
        'user_decision': 'podemos exagerar la altura de alguna zona en concreto olvidandonos de la escala en pos de jugabilidad',
        'source_sha256': hashes,
        'source_paths': {k: str(p.relative_to(ROOT)) for k, p in paths.items()},
        'zones': zones, 'closeup_xywh_km': closeup,
        'nature_reserve_design': reserve_design,
        'proposal_acceptance': 'User accepts zonal proposal as starting point and requires dense woodland pockets and multiple biomes; final heights remain engineering targets',
        'regional_rolling_crest_targets_m': [30, 70],
        'optional_landmark_crest_targets_m': [180, 200],
        'road_grade_design_targets_percent': {'primary': 6, 'secondary': 8},
        'terrain_modified': False, 'sources_unchanged': True,
        'limits': ['Areas are schematic study envelopes, not edit masks.',
                   'Source statistics exclude raster water/wetland but do not certify dry ground in engine.',
                   'Source3x is not the deployed native0.2 terrain.',
                   'Lake levels, river beds, final profiles and sight lines remain to be designed.',
                   'No runtime, navmesh or performance acceptance.'],
    }
    (out/'design.json').write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps({'status': record['status'], 'zones': zones,
                      'sources_unchanged': True}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
