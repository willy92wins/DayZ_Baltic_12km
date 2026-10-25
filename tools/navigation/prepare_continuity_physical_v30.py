"""Freeze physical consumers for the five V30 nav-height findings and a control."""
from pathlib import Path
import hashlib
import json

import numpy as np
import rasterio
from waterway_common import sample

ROOT = Path(__file__).resolve().parents[2]
BUILD = Path('E:/DayZ-Baltic-Build')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    nav_path = BUILD / 'v30-continuity-dedup-package/nav-fixture/reference.json'
    previous_path = ROOT / 'evidence/overnight-2026-10-01/regional-chase-v3/reference.json'
    template_path = ROOT / 'missions/BalticRegionalChaseV3.BalticTrial/init.c'
    asc = BUILD / 'v30-watercourse-continuity/baltic_terrain_v30.asc'
    expected_asc = 'dacc8e553ed70d1828d7c6bcf755533953765c09f730601dae1a6557c1a01431'
    if sha(asc) != expected_asc:
        raise ValueError('Changed continuity terrain')
    nav = json.loads(nav_path.read_text())
    previous = json.loads(previous_path.read_text())
    with rasterio.open(asc) as ds:
        heights = ds.read(1)
    names = ['lagoon', 'hills', 'changed_bank_01', 'changed_bank_02', 'changed_bank_03', 'changed_bank_05']
    cases = []
    for name in names:
        matched = [q for q in nav['queries'] if q['name'] == name]
        if len(matched) != 1:
            raise ValueError('Nonunique frozen route: ' + name)
        q = matched[0]
        for reverse in (False, True):
            endpoints = [q['start'], q['end']]
            if reverse:
                endpoints.reverse()
            points = []
            for point in endpoints:
                x, _, z = point
                y = float(sample(heights, np.array([x + 200000]), np.array([z]))[0])
                points.append(np.array([x, y + .05, z], dtype='float32').astype(float).tolist())
            cases.append(dict(case=len(cases), name=name, reverse=reverse, kind='ground',
                              start=points[0], goal=points[1], source_query=name,
                              role='control' if name == 'lagoon' else 'nav_height_finding'))
    mission = ROOT / 'missions/BalticV30ContinuityPhysicalV1.BalticTrial'
    out = BUILD / 'v30-continuity-physical-v1'
    if mission.exists() or out.exists():
        raise ValueError('Fresh output required')
    code = template_path.read_text()
    replacements = {
        'BalticRegionalChaseMission': 'BalticV30ContinuityPhysicalMission',
        'baltic_regional_chase_v3.log': 'baltic_v30_continuity_physical_v1.log',
        'BALTIC_REGIONAL_CHASE_V3': 'BALTIC_V30_CONTINUITY_PHYSICAL_V1',
        'm_Starts.Count()!=26': 'm_Starts.Count()!=12',
        'm_Time>3500': 'm_Time>1800',
        'SetDate(2026, 9, 29, 12, 0)': 'SetDate(2026, 10, 2, 12, 0)',
    }
    for old, new in replacements.items():
        if old not in code:
            raise ValueError('Template anchor missing: ' + old)
        code = code.replace(old, new)
    long_record = 'FPrintln(m_Log,"A;"+m_Case+";"+m_Time+";"+marker+";"+pos.ToString()+";"+prey.ToString()+";"+m_Goal.ToString()+";"+health+";"+mind+";"+ground+";"+road);'
    if code.count(long_record) != 1:
        raise ValueError('Record anchor changed')
    code = code.replace(long_record, '''string record="A;"+m_Case+";"+m_Time+";"+marker;
        record=record+";"+pos.ToString()+";"+prey.ToString();
        record=record+";"+m_Goal.ToString()+";"+health;
        record=record+";"+mind+";"+ground+";"+road;
        FPrintln(m_Log,record);''')
    mission.mkdir(parents=True)
    out.mkdir(parents=True)
    (mission / 'init.c').write_text(code, encoding='utf-8')
    rows = [str(c['case']) + ';' + ' '.join(f'{v:.9g}' for v in c['start']) + ';' +
            ' '.join(f'{v:.9g}' for v in c['goal']) for c in cases]
    (mission / 'cases.csv').write_text('\n'.join(rows) + '\n', encoding='ascii')
    ref = dict(status='PREPARED_NOT_RUN', log_header='BALTIC_V30_CONTINUITY_PHYSICAL_V1',
               terrain=str(asc), terrain_sha256=expected_asc,
               source_nav_reference=str(nav_path), source_nav_reference_sha256=sha(nav_path),
               prior_consumer_reference_sha256=sha(previous_path), template_sha256=sha(template_path),
               criteria=previous['criteria'], bridge=previous['bridge'], cases=cases,
               mission={str(p): sha(p) for p in mission.iterdir()},
               limits=['Selected routes only; no map-wide acceptance.',
                       'Prior graph-height failures remain unchanged.',
                       'No infected motion override or teleport after spawn.',
                       'Single client, no player-capacity claim.'])
    (out / 'reference.json').write_text(json.dumps(ref, indent=2) + '\n')
    print(json.dumps(dict(mission=str(mission), reference=str(out / 'reference.json'), cases=len(cases))))


if __name__ == '__main__':
    main()
