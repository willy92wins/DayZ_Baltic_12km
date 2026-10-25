"""Prepare the observed ASC fallback in a fresh native project copy."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'tb/regional_road_network_v29'
TARGET = Path('E:/DayZ-Baltic-Build/editor-v30-delta/native-asc')
ASC = Path('E:/DayZ-Baltic-Build/v30-delta-candidate/baltic_terrain_v30.asc')
EV = ROOT / 'evidence/v30-native-editor-2026-10-02'


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def main():
    assert not TARGET.exists(), 'Fresh target required'
    assert sha(ASC) == '64d4f160b963c28b519a50c9c29564dbe9727facabf7b52d83970eef5b8e6eb4'
    paths = list(SOURCE.rglob('*'))
    assert not any(p.is_symlink() or p.is_junction() for p in paths)
    files = [p for p in paths if p.is_file()]
    before = {}
    TARGET.mkdir()
    for index, p in enumerate(files):
        relative = p.relative_to(SOURCE)
        digest = sha(p)
        destination = TARGET / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, destination)
        assert sha(destination) == digest and sha(p) == digest, str(relative)
        before[relative.as_posix()] = digest
        if index % 2000 == 0:
            print(f'Copied and verified {index}/{len(files)} files', flush=True)
    shutil.copyfile(ASC, TARGET / 'delta_v30.asc')
    assert sha(TARGET / 'delta_v30.asc') == sha(ASC)
    report = dict(status='PREPARED_ASC_FALLBACK_NOT_IMPORTED', source=str(SOURCE),
                  target=str(TARGET), files=len(before), source_hashes=before,
                  asc_sha256=sha(ASC), project_sha256=sha(TARGET / 'road_v29.tv4p'),
                  limits=['Opaque clone retains original absolute references.',
                          'Set isolated mapframe root before Rebuild; native Save As and full comparison required.',
                          'Old V29 water and materials have not been replaced yet.'])
    (EV / 'asc-clone.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'source_hashes'}), flush=True)


if __name__ == '__main__':
    main()
