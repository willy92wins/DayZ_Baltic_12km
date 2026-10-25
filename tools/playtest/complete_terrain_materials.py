"""Complete this terrain's empty detail slots after Terrain Builder Generate Layers.

Measured A/B/A in Buldozer 1.29: the same terrain renders black blocks when its
generated N variants have empty Stage3..10 textures; completing those bindings
with the existing four-material palette removes the blocks. This is a scoped
workaround, not a general Terrain Builder material converter.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re

PALETTE = {
    3: r'dz\surfaces\data\terrain\cp_gravel_nopx.paa',
    4: r'dz\surfaces\data\terrain\cp_gravel_ca.paa',
    5: r'dz\surfaces\data\terrain\cp_conifer_common1_nopx.paa',
    6: r'dz\surfaces\data\terrain\cp_conifer_common1_ca.paa',
    7: r'dz\surfaces\data\terrain\cp_grass_nopx.paa',
    8: r'dz\surfaces\data\terrain\cp_grass_ca.paa',
    9: r'dz\surfaces\data\terrain\cp_grass_tall_nopx.paa',
    10: r'dz\surfaces\data\terrain\cp_grass_tall_ca.paa',
}
STAGE = re.compile(r'(class Stage(\d+)\s*\{\s*texture\s*=\s*")([^"]*)(")')


def tile_palettes(files):
    """Resolve each tile's compact palette from TB's non-N variant labels."""
    groups = {}
    for path in files:
        match = re.fullmatch(r'P_(\d{3}-\d{3})_((?:L0[0-3]|N)(?:_(?:L0[0-3]|N))*)\.rvmat', path.name, re.I)
        if not match:
            raise ValueError(f'Unexpected material name: {path.name}')
        labels = match[2].upper().split('_')
        slots = groups.setdefault(match[1], [None] * len(labels))
        if len(slots) != len(labels):
            raise ValueError(f'Inconsistent palette size: {path.name}')
        for i, label in enumerate(labels):
            if label != 'N':
                value = int(label[1:])
                if slots[i] is not None and slots[i] != value:
                    raise ValueError(f'Conflicting palette slot: {path.name}')
                slots[i] = value
    palettes = {}
    for tile, slots in groups.items():
        if any(n is None for n in slots) or slots != sorted(set(slots)):
            raise ValueError(f'Unresolved or reordered palette: {tile}')
        palettes[tile] = {3 + 2*i + channel: PALETTE[3 + 2*value + channel]
                          for i, value in enumerate(slots) for channel in (0, 1)}
    return palettes


def complete(data, label, palette=None):
    palette = PALETTE if palette is None else palette
    text = data.decode('utf-8-sig')
    if text.count('PixelShaderID="TerrainX";') != 1 or 'class Stage14' in text:
        raise ValueError(f'Unexpected shader contract: {label}')
    found = [(int(m[1]), m[2]) for m in STAGE.findall(text)]
    details = [(n, texture) for n, texture in found if n >= 3]
    # TB compacts the palette when a tile uses fewer surfaces.
    # Never add missing stages: fill only existing, verified bindings.
    if len(details) not in (2, 4, 6, 8) or [n for n, _ in details] != list(range(3, 3 + len(details))):
        raise ValueError(f'Unexpected stage layout: {label}')
    for n, texture in details:
        if n not in palette or (texture and texture.lower() != palette[n]):
            raise ValueError(f'Palette changed at Stage{n}: {label}')
    slots = sum(not t for _, t in details)
    if not slots:
        return data, 0
    def replace(m):
        n = int(m[2])
        return m[1] + palette[n] + m[4] if n in palette and not m[3] else m[0]
    fixed = STAGE.sub(replace, text).encode('utf-8')
    return fixed, slots


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--layers', type=Path, required=True)
    ap.add_argument('--vanilla-root', type=Path, default=Path('P:/'))
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--backup', type=Path)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    layers = args.layers.resolve(strict=True)
    files = sorted(layers.glob('*.rvmat'))
    if not files:
        raise ValueError('No material files; zero files is not a pass')
    if args.out.exists():
        raise ValueError('Fresh report path required')
    for texture in PALETTE.values():
        if not (args.vanilla_root / texture.replace('\\', '/')).is_file():
            raise ValueError(f'Missing vanilla texture: {texture}')
    prepared = []
    palettes = tile_palettes(files)
    for path in files:
        original = path.read_bytes()
        palette = palettes[path.name.split('_')[1]]
        fixed, slots = complete(original, path.name, palette)
        if len([m for m in STAGE.findall(original.decode('utf-8-sig')) if int(m[1]) >= 3]) != len(palette):
            raise ValueError(f'Filename and stage layout disagree: {path.name}')
        prepared.append((path, original, fixed, slots))
    changed = [x for x in prepared if x[3]]
    if args.apply and changed:
        if args.backup is None or args.backup.exists():
            raise ValueError('A new backup directory is required before any edit')
        backup = args.backup.resolve()
        if backup == layers or layers in backup.parents:
            raise ValueError('Backup must be outside the generated layers')
        backup.mkdir(parents=True)
        for path, original, _, _ in changed:
            (backup / path.name).write_bytes(original)
        for path, original, fixed, _ in changed:
            if path.read_bytes() != original:
                raise ValueError(f'Concurrent change; refusing overwrite: {path}')
            path.write_bytes(fixed)
    result = {
        'status': 'APPLIED' if args.apply else 'DRY_RUN',
        'layers': str(layers), 'files_checked': len(files),
        'changed_materials': len(changed), 'filled_slots': sum(x[3] for x in changed),
        'files': [{'name': p.name, 'slots': n,
                   'before': hashlib.sha256(old).hexdigest(),
                   'after': hashlib.sha256(new).hexdigest()} for p, old, new, n in changed],
        'limits': 'Only verified per-tile subsets of the fixed Baltic four-material palette and TerrainX are accepted. Run before Buldozer/build after Generate Layers.'
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'files'}, indent=2))


if __name__ == '__main__':
    main()
