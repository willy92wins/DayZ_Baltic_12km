"""Clone V33 editable after all joint V29 offline consumers accept the ASC."""
from pathlib import Path
import hashlib, json, shutil

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'tb/regional_outline_smoothing_v33'
TARGET = ROOT/'tb/regional_road_network_v29'
CANDIDATE = ROOT/'tests/regional_road_network_v29'
EVIDENCE = ROOT/'evidence/foundation-followup-2026-10-01/road-v29-native'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    assert not TARGET.exists() and not EVIDENCE.exists()
    asc = CANDIDATE/'baltic_road_network_v29.asc'
    digest = 'ed6cdaa5a1b9100a6f74041e9338f1c21f100a6686f596c73f79f33c4b8662c6'
    assert sha(asc) == digest
    required = {
        'independent-consumer.json': 'PASS_OFFLINE_EDITABLE_DRY_NETWORK_GEOMETRY',
        'continuous-outline.json': 'PASS_OFFLINE_OUTLINE_GEOMETRY',
        'joint-hydrology.json': 'PASS_OFFLINE_JOINT_HYDROLOGY_AND_PROTECTED_LAND',
        'landmarks-controls-physical-contract.json': 'PASS_OUTLINE_LANDMARKS_AND_CONTROLS',
        'land-controls.json': 'PASS_FULL_NETWORK_POSITIVE_AND_NEGATIVES',
        'joint-hydrology-controls.json': 'PASS_REAL_JOINT_HYDROLOGY_AND_FOUR_NEGATIVES',
    }
    gates = {}
    for name, status in required.items():
        p = CANDIDATE/name; gate = json.loads(p.read_text())
        assert gate['status'] == status, name
        assert gate.get('candidate_sha256', gate.get('asc_sha256')) == digest, name
        assert all(v is True for v in gate.get('checks', {}).values()), name
        gates[name] = sha(p)
    assert sha(SOURCE/'6.wrp') == 'cbe04e06043a7136ce754e265d3da04a93257d6b321060fdc79bbb91afb9e492'
    paths = list(SOURCE.rglob('*'))
    assert not any(p.is_symlink() or p.is_junction() for p in paths)
    before = {p.relative_to(SOURCE).as_posix(): sha(p) for p in paths if p.is_file()}
    shutil.copytree(SOURCE, TARGET)
    for name, expected in before.items():
        assert sha(SOURCE/name) == expected and sha(TARGET/name) == expected, name
    shutil.copyfile(asc, TARGET/'road_v29.asc')
    assert sha(TARGET/'road_v29.asc') == digest
    EVIDENCE.mkdir()
    report = dict(status='PASS_COMPLETE_EDITABLE_COPY_NOT_IMPORTED', source=str(SOURCE),
                  target=str(TARGET), source_files=len(before), source_hashes=before,
                  added_asc_sha256=digest, offline_gates=gates,
                  next='Native Save As road_v29.tv4p, set isolated mapframe root before Rebuild; imported ASC alone does not change the world.')
    (EVIDENCE/'editor-clone.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k != 'source_hashes'}), flush=True)


if __name__ == '__main__':
    main()
