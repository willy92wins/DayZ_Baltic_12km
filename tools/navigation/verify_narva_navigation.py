"""Conservative whole-triangle depth gate and independent negative controls."""
import argparse
import json
import math
from pathlib import Path
import numpy as np
import rasterio
from shapely.geometry import shape, Polygon
from waterway_common import ROOT, BASE_SHA, FIT, sha, read_base, sample


def intersecting_triangles(poly):
    xmin, zmin, xmax, zmax = poly.bounds
    for row in range(max(0, int((12282-zmax)//6)-1), min(2047, int((12282-zmin)//6)+2)):
        for col in range(max(0, int((xmin-200000)//6)-1), min(2047, int((xmax-200000)//6)+2)):
            for indices in (((row,col),(row,col+1),(row+1,col+1)),
                            ((row,col),(row+1,col),(row+1,col+1))):
                tri = Polygon([(200000+6*c,12282-6*r) for r,c in indices])
                if tri.intersection(poly).area > 1e-9:
                    yield indices


def depth_gate(h, triangles):
    # Conservative: require all three vertices even when a triangle only
    # partly intersects the check polygon. Convex interpolation cannot exceed
    # the highest vertex anywhere inside the triangle.
    ymax = max(float(h[r,c]) for tri in triangles for r,c in tri)
    return {'triangles': len(triangles), 'conservative_depth_min_m': .5-ymax,
            'pass': ymax <= -2.5}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    args = parser.parse_args()
    design_path = args.candidate/'design.json'
    design = json.loads(design_path.read_text())
    asc = args.candidate/'narva_navigation_v1.asc'
    if sha(asc) != design['candidate_sha256'] or design['source_sha256'] != BASE_SHA:
        raise ValueError('Frozen source or candidate drift')
    base = read_base()
    with rasterio.open(asc) as ds:
        h = ds.read(1)
    poly = shape(design['depth_check_polygon_tb'])
    triangles = list(intersecting_triangles(poly))
    depth = depth_gate(h, triangles)
    old = depth_gate(base, triangles)
    # An isolated shallow triangle must fail even when its neighbours pass.
    plugged = h.copy()
    tri = triangles[len(triangles)//2]
    plugged[tri[0]] = 0
    negative = depth_gate(plugged, triangles)
    fit = json.loads(FIT.read_text())
    centre = np.array(fit['bridge_centre_tb'])
    u = np.array(fit['axis_east_unit']); side = np.array([u[1], -u[0]])
    landings = []
    for sign in (-1, 1):
        along, width = np.meshgrid(np.linspace(sign*37.5,sign*49,47), np.linspace(-4,4,33))
        pp = centre[:,None,None]+u[:,None,None]*along+side[:,None,None]*width
        heights = sample(h, pp[0], pp[1])
        landings.append({'side':sign,'max_deck_gap_m':float(np.max(abs(heights-9)))})
    # Sample the full eight-metre road, not just its centreline.
    ramps = []
    for sign in (-1, 1):
        stations = np.arange(50,280.001,.25)*sign
        worst = 0.
        for offset in np.arange(-4,4.001,.5):
            pp = centre[:,None]+u[:,None]*stations+side[:,None]*offset
            heights = sample(h,pp[0],pp[1])
            worst = max(worst,float(np.max(abs(np.diff(heights))/.25)))
        ramps.append({'side':sign,'maximum_sampled_road_grade':worst})
    assets = json.loads((ROOT/'evidence/navigation/vanilla-assets.json').read_text())
    bridge = next(b for b in assets['bridges'] if Path(b['path']).stem=='bridge_metal_25')
    opening = next(c for c in bridge['corridors'] if c['width_m']==18)
    clear = opening['headroom_at_deck_9_water_1_m']
    with np.load(args.candidate/'delta.npz') as delta:
        mask = np.zeros(base.shape,dtype=bool);mask[delta['row'],delta['col']] = True
        outside_ok = np.array_equal(base[~mask],h[~mask])
        delta_ok = np.array_equal(base[mask],delta['before']) and np.array_equal(h[mask],delta['after'])
    checks = {'continuous_depth': depth['pass'], 'baseline_rejected': not old['pass'],
              'shallow_plug_rejected': not negative['pass'],
              'landings_at_deck': max(x['max_deck_gap_m'] for x in landings) <= .0051,
              'road_grade_le_6_percent': max(x['maximum_sampled_road_grade'] for x in ramps) <= .06,
              'model_clearance_ge_6m': clear >= 6,
              'outside_delta_unchanged': outside_ok, 'delta_records_match': delta_ok}
    result = {'status': 'PASS_OFFLINE_ONLY' if all(checks.values()) else 'FAIL',
              'checks': checks, 'candidate_sha256': sha(asc), 'design_sha256': sha(design_path),
              'depth': depth, 'baseline_depth': old, 'negative_plug_depth': negative,
              'landings': landings, 'ramps': ramps, 'model_central_opening_headroom_m': clear,
              'limit': 'Geometry prediction only. No runtime boat, driver, collision, physics, imported pose or navigation pass.'}
    (args.candidate/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if all(checks.values()) else 1)


if __name__=='__main__':
    main()
