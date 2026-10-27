"""Consume bound native configuration observations, never infer loader behavior."""
import argparse
import json
import math
from pathlib import Path


def paths(probe):
    return ['CfgWorlds BalticTrial Navmesh filterIsolatedIslandsOnLoad',
            'CfgWorlds BalticTrial Navmesh GenParams filterIsolatedIslands',
            'CfgWorlds ChernarusPlus Navmesh filterIsolatedIslandsOnLoad',
            'CfgWorlds ChernarusPlus Navmesh GenParams filterIsolatedIslands',
            'CfgWorlds BalticTrial Navmesh GenParams tileWidth',
            'CfgWorlds ChernarusPlus Navmesh GenParams tileWidth',
            'CfgWorlds BalticTrial startTime', 'CfgWorlds ChernarusPlus description',
            'CfgWorlds BalticTrial Navmesh __missing_'+probe]


def require(condition, reason):
    if not condition: raise ValueError(reason)


def boolean(value):
    require(value in ('true', 'false', '0', '1'), 'Boolean encoding')
    return value in ('true', '1')


def evaluate(text, probe):
    rows = [row.split(';') for row in text.splitlines() if row.strip()]
    require(rows and rows[0] == ['BALTIC_NAV_CONFIG_TYPES_V1', 'BalticTrial', probe, '9'], 'Header/world/UUID')
    require(rows[-1] == ['END', '9'] and len(rows) == 11, 'Incomplete or additional records')
    observations = []
    for i, path in enumerate(paths(probe)):
        row = rows[i+1]
        require(len(row) == 9 and row[:3] == ['C', str(i), path], 'Row identity/order/schema')
        item = dict(index=i, path=path, exists=boolean(row[3]), native_type=int(row[4]), text_ok=boolean(row[5]), text=row[6], integer=int(row[7]), floating=float(row[8]))
        require(math.isfinite(item['floating']), 'Nonfinite numeric observation')
        observations.append(item)
    missing = [r['path'] for r in observations[:8] if not r['exists']]
    require(not missing, 'Absent positive control/field: '+', '.join(missing))
    negative = observations[8]
    require(not negative['exists'] and negative['native_type'] == -1 and not negative['text_ok'] and negative['text'] == '' and negative['integer'] == negative['floating'] == 0, 'Missing-field negative control')
    for index, value in ((2, 1), (3, 1), (4, 8), (5, 50)):
        require(observations[index]['integer'] == observations[index]['floating'] == value, 'Invalid numeric positive control: '+str(index))
    for index, value in ((6, '12:00'), (7, 'Chernarus')):
        require(observations[index]['text_ok'] and observations[index]['text'] == value, 'Invalid text positive control: '+str(index))
    differences = [r for r in observations[:2] if r['integer'] != 1 or r['floating'] != 1]
    return dict(status='OBSERVED_SCRIPT_NUMERIC_CONVERSION_DIFFERENCE' if differences else 'NO_SCRIPT_NUMERIC_CONVERSION_DIFFERENCE', acceptance_eligible=False, observation_count=9, controls='PASS', observations=observations, different_baltic_flags=[r['path'] for r in differences], limits=['Only script-facing getters observed; native navmesh loader conversion and filtering remain unproven.', 'GenParams was not applied to regenerate this NM.', 'No RAM measurement, navigation rerun, optimization or tolerance change.'])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--log', type=Path, required=True)
    ap.add_argument('--probe-id', required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    require(not args.out.exists(), 'Fresh result required')
    try: result = evaluate(args.log.read_text(encoding='utf-8-sig'), args.probe_id)
    except (ValueError, IndexError) as error: result = dict(status='INCONCLUSIVE_INVALID_CONFIG_CAPTURE', acceptance_eligible=False, error=str(error))
    args.out.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))
    return 2 if result['status'].startswith('INCONCLUSIVE') else 0


if __name__ == '__main__': raise SystemExit(main())
