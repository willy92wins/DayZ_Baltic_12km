"""Shared read-only source adapters for the local navigation engineering pass."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np
import rasterio
from shapely.geometry import shape, Point
from shapely.ops import unary_union, linemerge

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from geo_common import tb_geometry

BASE = ROOT / 'tests/regional_clearance_v1/baltic_regional_clearance_v1.asc'
BASE_SHA = 'd21cdf2c9e7bc7602f9d66e8a7ca0464258b0afccabe77c3ff26655b0bda6751'
RIVERS = ROOT / 'derived/gis/osm_rivers_wgs84.geojson'
FIT = ROOT / 'evidence/narva/evidence/narva-fit.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_base():
    if sha(BASE) != BASE_SHA:
        raise ValueError('Frozen current terrain changed')
    with rasterio.open(BASE) as ds:
        heights = ds.read(1)
    if heights.shape != (2048, 2048):
        raise ValueError('Unexpected grid')
    return heights


def sample(h, x, z):
    """TB eastings, game northings; engine-observed triangle registration."""
    col = (np.asarray(x)-200000)/6
    row = (12282-np.asarray(z))/6
    ci, ri = np.floor(col).astype(int), np.floor(row).astype(int)
    if np.any(ci < 0) or np.any(ri < 0) or np.any(ci >= 2047) or np.any(ri >= 2047):
        raise ValueError('Outside native grid interior')
    a, b = col-ci, row-ri
    return np.where(b <= a,
        h[ri, ci]*(1-a)+h[ri, ci+1]*(a-b)+h[ri+1, ci+1]*b,
        h[ri, ci]*(1-b)+h[ri+1, ci]*(b-a)+h[ri+1, ci+1]*a)


def river_features():
    return json.loads(RIVERS.read_text(encoding='utf-8'))['features']


def river_group(properties):
    names = {str(v).casefold() for k, v in properties.items() if k.startswith('name')}
    if names & {'narva river', 'narva jõgi', 'narva jõgi - нарва', 'нарва', 'река нарва'}:
        return 'Narva'
    if names & {'neva', 'нева'}:
        return 'Neva'
    if names & {'luga river', 'луга'}:
        return 'Luga'
    if names & {'большая нева', 'малая нева', 'большая невка', 'малая невка', 'средняя невка'}:
        return 'Delta Neva'
    return None


def narva_central_line():
    parts = [tb_geometry(shape(f['geometry'])) for f in river_features()
             if river_group(f['properties']) == 'Narva']
    merged = linemerge(unary_union(parts))
    lines = list(merged.geoms) if hasattr(merged, 'geoms') else [merged]
    centre = json.loads(FIT.read_text())['bridge_centre_tb']
    line = min(lines, key=lambda x: x.distance(Point(centre)))
    if line.distance(Point(centre)) > 1 or line.length < 180:
        raise ValueError('Unexpected Narva pilot axis')
    return line
