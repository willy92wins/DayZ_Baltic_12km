"""Freeze the existing V10 regional sedan fixture before native execution."""
from pathlib import Path
import argparse, datetime, hashlib, json, sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/playtest'))
from attach_navmesh import read_pbo
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--reference', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    assert not a.out.exists()
    ref = json.loads(a.reference.read_text(encoding='utf-8'))
    mission = Path(ref['deployed_mission'])
    assert mission.parent==Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')
    assert mission.name in ['BalticRegionalDriveV1.BalticTrial','BalticRegionalDriveV2.BalticTrial']
    probe = Path('P:/Mods/@BalticDriveInputProbe/Addons/baltic_drive_input.pbo')
    expected = {**ref['inputs'], **ref['mission'], ref['terrain']: ref['terrain_sha256']}
    for source, digest in ref['mission'].items():
        expected[str(mission / Path(source).name)] = digest
    expected.update({
        str(probe): ref['input_pbo_sha256'],
        'P:/Mods/@DayZ_Baltic_FoundationV10Native/Addons/narva_trial.pbo': 'd1008dd6c882193706f06c5e7b8495ee1a357f5819a8574118784f7e90f18577',
        'P:/Mods/@DayZ_Baltic_FoundationV10Native/Addons/baltic_water.pbo': 'f9a5cdf7461ff09e80a102641289513896011a78b090fdbbd1056f9b985898d3',
    })
    actual = {p: sha(Path(p)) for p in expected}
    assert actual == expected, [p for p in expected if actual[p] != expected[p]]
    _, properties, entries = read_pbo(probe)
    assert entries['config.bin'].startswith(b'\0raP')
    script = next(Path(p) for p in ref['inputs'] if p.endswith('BalticDriveInput.c'))
    assert any(value == script.read_bytes() for name, value in entries.items() if name.endswith('.c'))
    result = dict(status='PASS_FROZEN_IDENTITY_NOT_RUNTIME', utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  reference_sha256=sha(a.reference), files=actual, probe_prefix=properties['prefix'],
                  launch=dict(project='DayZ_MCP', mode='server', mission=str(mission),
                              extra_mods=['@DayZ_Baltic_FoundationV10Native', '@BalticDriveInputProbe'],
                              no_base_mods=True, no_file_patching=True))
    a.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))

if __name__ == '__main__':
    main()
