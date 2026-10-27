"""Read-only TESM9 prefix/coverage checks, anchored to installed Chernarus 1.30.

Observed reference: navmesh.nm SHA256 0b18d48d6c1e902e41b35b91588e84a3e3068a28df6d71cf6d74a6f80d29a163.
Only the observed TESM9 / VAND12 layout is accepted. This does not decode
polygon topology or establish engine loading, traversability or actor movement.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct


def inspect(data, expected_grid, tile_width=50.):
    if tile_width not in (8., 12.5, 25., 50.):
        raise ValueError('Unsupported explicit tile dimension')
    if len(data) < 48:
        raise ValueError('Truncated TESM header')
    magic, version, count, nx, nz = struct.unpack_from('<5I', data)
    if (magic, version) != (0x4d534554, 9):
        raise ValueError('Unsupported serialized version')
    if (nx, nz) != tuple(expected_grid) or count != nx * nz or min(nx, nz) <= 0:
        raise ValueError('Unexpected grid coverage')
    origin_x, origin_y, origin_z, width, depth = struct.unpack_from('<5f', data, 20)
    if (origin_x, origin_y, origin_z, width, depth) != (0., 0., 0., tile_width, tile_width):
        raise ValueError('Unexpected origin or tile dimensions')
    if struct.unpack_from('<I', data, 40)[0] != count:
        raise ValueError('Observed tile count fields disagree')
    parameter_u32_at_44 = struct.unpack_from('<I', data, 44)[0]
    base = 48 + 4 * count
    if base >= len(data):
        raise ValueError('Truncated offset table')
    offsets = struct.unpack_from(f'<{count}I', data, 48)
    if offsets[0] != 0 or any(a >= b for a, b in zip(offsets, offsets[1:])) or base + offsets[-1] >= len(data):
        raise ValueError('Invalid tile offsets')
    seen = set()
    refs = set()
    polygons = vertices = 0
    reference_encoding_matches_installed = True
    low, high = math.inf, -math.inf
    for index, offset in enumerate(offsets):
        start = base + offset
        end = base + offsets[index + 1] if index + 1 < count else len(data)
        if end - start <= 116:
            raise ValueError('Truncated tile header/payload')
        reference, length, reserved = struct.unpack_from('<QII', data, start)
        if not reference or reference in refs or reserved != 0 or length != end - start - 16:
            raise ValueError('Invalid tile reference or payload length')
        refs.add(reference)
        reference_encoding_matches_installed &= reference == ((1 << 48) | (index << 20))
        integers = struct.unpack_from('<15I', data, start + 16)
        values = struct.unpack_from('<10f', data, start + 76)
        if integers[:2] != (0x444e4156, 12):
            raise ValueError('Unsupported tile version')
        x, z = integers[2:4]
        if not (0 <= x < nx and 0 <= z < nz) or (x, z) in seen:
            raise ValueError('Invalid or duplicate tile coordinate')
        seen.add((x, z))
        if not all(math.isfinite(v) for v in values):
            raise ValueError('Nonfinite tile metadata')
        if any(abs(a - b) > .001 for a, b in zip((values[3], values[5], values[6], values[8]),
                                                (x * width, z * depth, (x + 1) * width, (z + 1) * depth))):
            raise ValueError('Tile bounds disagree with coordinates')
        if values[4] > values[7] or min(values[:3]) <= 0 or values[9] <= 0:
            raise ValueError('Invalid vertical bounds or positive tile parameters')
        polygons += integers[6]
        vertices += integers[7]
        low, high = min(low, values[4]), max(high, values[7])
    return dict(status='EMPIRICAL_V9_PREFIX_AND_COVERAGE_PASS', version=9, tile_version=12,
                tiles=len(seen), grid=[nx, nz], tile_width=tile_width, declared_polygons=polygons,
                declared_vertices=vertices, y_bounds=[low, high], bytes=len(data),
                header_parameter_u32_at_44=parameter_u32_at_44,
                reference_encoding_matches_installed=reference_encoding_matches_installed,
                sha256=hashlib.sha256(data).hexdigest(),
                limits=['Observed header, offset, payload-length, coordinate and bounds invariants only.',
                        'Polygon payload/topology not decoded. Engine load, useful paths and actors remain unverified.',
                        'Polygon/vertex totals are unverified sums of tile header declarations.',
                        'Header u32 at 44 and reference bit pattern are reported, not acceptance invariants.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('navmesh', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--expected-sha256', required=True)
    parser.add_argument('--grid', type=int, nargs=2, required=True)
    parser.add_argument('--tile-width', type=float, choices=(8., 12.5, 25., 50.), required=True)
    args = parser.parse_args()
    data = args.navmesh.read_bytes()
    if hashlib.sha256(data).hexdigest() != args.expected_sha256:
        raise ValueError('Input identity mismatch')
    if args.output.exists():
        raise ValueError('Output already exists')
    result = inspect(data, args.grid, args.tile_width)
    result['source'] = str(args.navmesh.resolve())
    result['inspector_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
