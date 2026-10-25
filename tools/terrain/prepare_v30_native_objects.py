"""Prepare native absolute-height CSV from canonical V30 WRP poses; no editor mutation."""
from pathlib import Path
import hashlib
import json

import numpy as np
from wrp0wzd import read

ROOT = Path(__file__).resolve().parents[2]
WRP = Path('E:/DayZ-Baltic-Build/editor-v30-delta/world/baltic_trial.wrp')
OUT = WRP.parent.parent / 'water_objects_v30_absolute.txt'
RECEIPT = ROOT / 'evidence/v30-native-editor-2026-10-02/water-import-preparation.json'


def main():
    digest = hashlib.sha256(WRP.read_bytes()).hexdigest()
    assert digest == '6e12e9c8ea26483b032914bc3b214661ccd2191b86b5182ec857ff109c02ec4e'
    assert not OUT.exists() and not RECEIPT.exists()
    objects = read(WRP)['objects']
    water = [o for o in objects if o['name'].startswith('baltic_water_v30\\')]
    assert len(water) == 17622 and len(objects) - len(water) == 9
    rows, models = [], {}
    for o in water:
        matrix = o['matrix']
        assert matrix[:9] == [1., 0., 0., 0., 1., 0., 0., 0., 1.]
        assert np.isfinite(matrix).all()
        model = Path('P:/') / o['name'].replace('\\', '/')
        assert model.is_file()
        name = model.stem
        models[name] = str(model)
        x, y, z = matrix[9:]
        row = f'"{name}";{x + 200000:.17g};{z:.17g};0;0;0;1;{y:.17g};'
        fields = row.split(';')
        restored = np.array([float(fields[1])-200000, float(fields[7]), float(fields[2])], dtype=np.float32)
        assert np.array_equal(restored, np.array([x, y, z], dtype=np.float32))
        rows.append(row)
    OUT.write_bytes(('\n'.join(rows)+'\n').encode('ascii'))
    report = dict(status='PREPARED_NOT_NATIVE_IMPORTED', source=str(WRP), source_sha256=digest,
                  file=str(OUT), sha256=hashlib.sha256(OUT.read_bytes()).hexdigest(),
                  instances=len(rows), models=len(models), bridges_excluded=9,
                  format_reference='tools/navigation/verify_regional_water_assets.py:53-58,69-70',
                  coordinate_contract='Absolute height; X=200000+WRP X, Z=WRP Z, Y=WRP Y; identity rotations.',
                  decimal_roundtrip_float32_exact=True,
                  limits=['Native importer and save/reopen/export comparison still required.',
                          'Old and new water models share template basenames. Use only V30 templates for these rows.',
                          'Replace old water layer in the isolated editor, preserve all nine bridge records.',
                          'P:/baltic_water_v30 currently resolves to source MLOD; template/export offsets must be checked.'])
    RECEIPT.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('status', 'instances', 'models', 'sha256')}))


if __name__ == '__main__':
    main()
