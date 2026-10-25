"""Bind existing, unchanged local camera probes to the final V29 world."""
from pathlib import Path
import copy
import hashlib
import json
import rasterio
from waterway_common import sample

ROOT = Path(__file__).resolve().parents[2]
EV = ROOT/'evidence/foundation-followup-2026-10-01'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    asc = ROOT/'tests/regional_road_network_v29/baltic_road_network_v29.asc'
    assert sha(asc) == 'ed6cdaa5a1b9100a6f74041e9338f1c21f100a6686f596c73f79f33c4b8662c6'
    receipt_path = ROOT/'build-output/road_v29_freshnav/verification.json'
    receipt = json.loads(receipt_path.read_text())
    assert receipt['status'] == 'PASS_NAVMESH_PACKED_BYTE_PARITY'
    world = Path('P:/Mods/@DayZ_Baltic_RoadV29/Addons/narva_trial.pbo')
    assert sha(world) == receipt['pbo_sha256']
    with rasterio.open(asc) as dataset:
        heights = dataset.read(1)
    reports = []
    for group in ('neva', 'reserve', 'south'):
        parent_name = 'outline-v33-visual-'+group+('-repeat' if group == 'neva' else '')
        parent = EV/parent_name/'reference.json'
        before = json.loads(parent.read_text())
        ref = copy.deepcopy(before)
        probes = list((Path(ref['deployed_mod'])/'Addons').glob('*.pbo'))
        assert len(probes) == 1 and sha(probes[0]) == ref['probe_pbo_sha256']
        mission = Path(ref['deployed_mission'])/'init.c'
        assert sha(mission) == ref['mission_sha256']
        stem = 'visual_native_'+group+'_v4'
        script = ROOT/f'packages/foundation-{stem}/baltic_foundation_{stem}/scripts/5_Mission/BalticRenderProbe.c'
        assert sha(script) == ref['script_sha256']
        x, z = ref['anchor']['xz']
        anchor_height = float(sample(heights, x+200000, z))
        assert anchor_height >= 1.25
        ref['anchor']['terrain_y'] = anchor_height
        ref.update(status='FROZEN_ROAD_V29_VISUAL_PROTOCOL_NOT_RUN',
                   parent_reference_sha256=sha(parent), terrain_sha256=sha(asc),
                   world_pbo_sha256=receipt['pbo_sha256'],
                   compiled_wrp_sha256=receipt['wrp_sha256'],
                   navmesh_sha256=receipt['navmesh_sha256'],
                   deployed_world=str(world), package_receipt_sha256=sha(receipt_path),
                   limits=['Same cameras, probe, mission and criteria; final V29 world and navigation.',
                           'Telemetry does not accept pixels or multiplayer capacity.',
                           'Capture through Sky if native DDS is absent.'])
        assert ref['poses'] == before['poses']
        out = EV/f'road-v29-visual-{group}'
        assert not out.exists(), 'Preserve prior evidence'
        out.mkdir()
        (out/'reference.json').write_text(json.dumps(ref, indent=2)+'\n', encoding='utf-8')
        reports.append(dict(group=group, reference_sha256=sha(out/'reference.json'),
                            anchor_ground_m=anchor_height, poses=len(ref['poses'])))
    print(json.dumps(reports))


if __name__ == '__main__':
    main()
