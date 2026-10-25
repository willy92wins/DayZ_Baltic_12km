"""Stage the accepted literal TB export without changing the existing trial."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    native = ROOT / 'tb/narva_navigation_v3/baltic_navigation_native_reopened_v2.wrp'
    expected = '9625ecf593c9c17288942d98ccf06933081bbcaffb367bb307146aa338cf9b5b'
    if sha(native) != expected:
        raise ValueError('Accepted export changed')
    for name, status in [('native-reopened-height-v2.json', 'PASS_NATIVE_HEIGHT_IMPORT'), ('native-reopened-bridge-v2.json', 'PASS_NATIVE_BRIDGE_LAYOUT')]:
        report = json.loads((ROOT / 'evidence/navigation' / name).read_text())
        if report['status'] != status or report['wrp_sha256'] != expected:
            raise ValueError('Native gate does not match export')
    source = ROOT / 'packages/baltic-navigation-v3/source/BalticTrialWorld'
    package = ROOT / 'packages/baltic-navigation-native-v1'
    if package.exists():
        raise ValueError('Fresh package required')
    files = sorted(p for p in source.rglob('*') if p.is_file())
    if any(p.is_symlink() or p.is_junction() for p in source.rglob('*')):
        raise ValueError('Source reparse point')
    manifest = {str(p.relative_to(source)).replace('\\', '/'): sha(p) for p in files}
    stage = package / 'source/BalticTrialWorld'
    shutil.copytree(source, stage)
    shutil.copyfile(native, stage / 'baltic_trial.wrp')
    for relative, digest in manifest.items():
        if sha(stage / relative) != (expected if relative == 'baltic_trial.wrp' else digest):
            raise ValueError('Unexpected stage change: ' + relative)
    shutil.copytree(ROOT / 'packages/baltic-navigation-v3/tools', package / 'tools')
    receipt = {'status': 'NATIVE_EXPORT_STAGED', 'wrp_sha256': expected,
               'unchanged_source_files': len(manifest) - 1,
               'bootstrap_navmesh_sha256': sha(stage / 'navmesh/baltic_trial.nm'),
               'limits': ['Navigation still stale until regenerated; no runtime acceptance.']}
    (package / 'stage-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
