"""Create one isolated Narva engineering candidate; keep regional baseline intact."""
import argparse
import json
import numpy as np
import rasterio
from shapely import points, distance, line_locate_point
from shapely.geometry import Point, mapping
from shapely.ops import substring
from waterway_common import ROOT, BASE_SHA, FIT, RIVERS, sha, read_base, narva_central_line, sample


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=__import__('pathlib').Path, required=True)
    parser.add_argument('--protect-channel', action='store_true', help='Clip approach embankments against the channel plus triangle support margin')
    parser.add_argument('--pin-landings', action='store_true', help='Pin support triangles at the two deck-to-terrain joints')
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError('Fresh candidate output required')
    base = read_base()
    line = narva_central_line()
    fit = json.loads(FIT.read_text())
    centre = np.array(fit['bridge_centre_tb'])
    along = np.array(fit['axis_east_unit'])
    across = np.array([along[1], -along[0]])
    rr, cc = np.mgrid[0:2048, 0:2048]
    xx, zz = 200000+6*cc, 12282-6*rr
    local_x = (xx-centre[0])*along[0] + (zz-centre[1])*along[1]
    local_z = (xx-centre[0])*across[0] + (zz-centre[1])*across[1]
    candidate = base.copy()
    # Wet reference is narrow after geographic compression. This explicit
    # gameplay channel follows its existing axis, with grid support margin.
    roi = (np.abs(xx-centre[0]) < 180) & (np.abs(zz-centre[1]) < 210)
    row, col = np.where(roi)
    pp = points(xx[roi], zz[roi])
    offset = distance(pp, line)
    station = line_locate_point(line, pp)
    width_blend = np.clip((34-offset)/(34-(12+6*np.sqrt(2))), 0, 1)
    end_blend = np.clip(np.minimum(station, line.length-station)/22, 0, 1)
    weight = width_blend*end_blend
    # 0.15m allowance beyond minimum depth3m at low sea0.5m.
    bed = -2.65
    candidate[row, col] = np.minimum(base[row, col], base[row, col]*(1-weight)+bed*weight)

    # Three25m spans. Flat landings, gentle independent approach profiles and
    # support padding so all triangles under an8m road meet the desired grade.
    deck, flat_end, ramp_end = 9., 50., 280.
    endpoints = []
    for sign in (-1, 1):
        end = centre + along*(sign*ramp_end)
        end_y = float(sample(base, end[0], end[1]))
        endpoints.append({'side': sign, 'x_tb': end[0], 'z': end[1], 'y': end_y})
        active = (sign*local_x >= 28.5) & (sign*local_x < ramp_end+12) & (np.abs(local_z) < 29)
        d = sign*local_x[active]
        t = np.clip((d-flat_end)/(ramp_end-flat_end), 0, 1)
        ease = t*t*(3-2*t)
        profile = deck+(end_y-deck)*ease
        shoulder = np.clip((29-np.abs(local_z[active]))/(29-13), 0, 1)
        taper = np.clip((ramp_end+12-d)/12, 0, 1)
        w = shoulder*taper
        if args.protect_channel:
            river_distance = distance(points(xx[active], zz[active]), line)
            w *= np.clip((river_distance-(12+6*np.sqrt(2)))/10, 0, 1)
        candidate[active] = candidate[active]*(1-w)+profile*w
    if args.pin_landings:
        for sign in (-1, 1):
            dd, ww = np.meshgrid(np.arange(37.5, 50.001, .25)*sign, np.arange(-4,4.001,.25))
            sx = centre[0]+along[0]*dd+across[0]*ww
            sz = centre[1]+along[1]*dd+across[1]*ww
            col = (sx-200000)/6; row = (12282-sz)/6
            ci, ri = np.floor(col).astype(int), np.floor(row).astype(int)
            upper = row-ri <= col-ci
            candidate[ri,ci] = deck
            candidate[ri+1,ci+1] = deck
            candidate[np.where(upper,ri,ri+1),np.where(upper,ci+1,ci)] = deck
    candidate = np.round(candidate, 4).astype(np.float32)
    changed = candidate != base
    if not changed.any() or changed.sum() > 3000:
        raise ValueError('Unexpected intervention size')
    # Only this explicitly bounded local design can change vertices.
    bound = (np.abs(local_x) <= 305) & (np.abs(local_z) <= 235)
    if np.any(changed & ~bound):
        raise ValueError('Changes outside pilot boundary')
    args.out.mkdir(parents=True)
    asc = args.out/'narva_navigation_v1.asc'
    with asc.open('w', encoding='ascii', newline='\n') as handle:
        handle.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n')
        np.savetxt(handle, candidate, fmt='%.4f')
    with rasterio.open(asc) as ds:
        persisted = ds.read(1)
    if not np.array_equal(persisted, candidate):
        raise ValueError('ASC roundtrip mismatch')
    np.savez_compressed(args.out/'delta.npz', row=np.where(changed)[0], col=np.where(changed)[1],
                        before=base[changed], after=candidate[changed])
    fairway = substring(line, 40, line.length-40).buffer(12, cap_style='flat')
    objects = []
    for offset in (-25, 0, 25):
        pos = centre + along*offset
        objects.append({'model': 'dz/structures/roads/bridges/bridge_metal_25.p3d',
                        'x': float(pos[0]-200000), 'z': float(pos[1]),
                        'yaw_deg': fit['heading_from_north_degrees'],
                        'scale': 1., 'target_deck_y': deck,
                        'engine_origin_y_candidate': deck-8.05488395690918})
    design = {'status': 'OFFLINE_CANDIDATE_NOT_IMPORTED', 'source_sha256': BASE_SHA,
              'candidate_sha256': sha(asc), 'river_source_sha256': sha(RIVERS),
              'bridge_fit_sha256': sha(FIT), 'river_axis_tb': mapping(line),
              'protect_channel_from_approach_embankments': args.protect_channel,
              'pin_landing_support_triangles': args.pin_landings,
              'depth_check_polygon_tb': mapping(fairway),
              'changed_vertices': int(changed.sum()),
              'max_lower_m': float((candidate-base).min()), 'max_raise_m': float((candidate-base).max()),
              'untouched_vertices_identical': bool(np.array_equal(candidate[~changed], base[~changed])),
              'channel_depth_target_m': 3., 'bed_target_y': bed, 'water_min_max_m': [.5, 1.],
              'channel_width_target_m': 24., 'bridge_central_opening_target_m': 18.,
              'bridge_clear_height_target_m': 6., 'bridge_objects': objects,
              'approach_endpoints': endpoints, 'approach_flat_end_m': flat_end, 'approach_end_m': ramp_end,
              'medium_vessel_design_envelope_not_measured_asset': {'length': 12, 'beam': 4, 'draft': 1.5, 'air_draft': 4.5},
              'limits': ['Local pilot only, ends blend into unprepared river.',
                         'No claim of full Narva/Neva/Luga navigation.',
                         'Satellite still depicts the old thin river; local water/road artwork must be updated.',
                         'Native save/reopen, engine collision, boat physics, land crossing and navmesh pending.']}
    (args.out/'design.json').write_text(json.dumps(design, indent=2)+'\n')
    print(json.dumps({k:v for k,v in design.items() if k not in ('river_axis_tb','depth_check_polygon_tb')}, indent=2))


if __name__ == '__main__':
    main()
