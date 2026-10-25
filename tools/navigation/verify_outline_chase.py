"""Audit the physical consumer independently of navmesh query heights."""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

import numpy as np
import rasterio
from waterway_common import ROOT, sample, sha


def vector(value):
    if not re.fullmatch(r'<[^<>]+>', value):
        raise ValueError('Malformed vector')
    values = [float(n) for n in value[1:-1].split(',')]
    if len(values) != 3 or not all(map(math.isfinite, values)):
        raise ValueError('Nonfinite/malformed vector')
    return values


def verify(text, ref, height):
    lines = text.splitlines()
    open_ground = ref.get('contract') == 'open_ground_v4'
    versions = (4,) if open_ground else (1,2,3)
    if lines[:3] not in [
        [f'BALTIC_OUTLINE_CHASE_V{v}', 'world=BalticTrial', 'event;t;stage;x;y;z;d;cross;health;mind;target_entity'] for v in versions
    ]:
        raise ValueError('Wrong fixture or world')
    rows, goals = [], {}
    index = 3
    while index < len(lines):
        parts = lines[index].split(';')
        if parts[0] == 'GOAL':
            stage = int(parts[1])
            if len(parts) != 5 or stage in goals:
                raise ValueError('Malformed/duplicate goal')
            goals[stage] = vector(parts[2])
            vector(parts[3]); vector(parts[4])
            index += 1
            continue
        if len(parts) != 11:
            raise ValueError('Malformed event')
        if parts[0] not in ('SPAWN', 'SAMPLE', 'NOISE', 'REACHED', 'SETTLE_BEGIN', 'SETTLE', 'COMPLETE_ALL_STAGES'):
            raise ValueError('Failed/unknown fixture event: '+parts[0])
        numbers = list(map(float, parts[1:10]))
        if not all(map(math.isfinite, numbers)) or numbers[1] != int(numbers[1]) or numbers[-1] != int(numbers[-1]):
            raise ValueError('Nonfinite or noninteger event')
        if index+1 >= len(lines):
            raise ValueError('Missing prey record')
        prey = lines[index+1].split(';')
        if len(prey) != 5 or prey[:3] != ['PREY', parts[1], parts[2]]:
            raise ValueError('Prey identity/time mismatch')
        row = dict(event=parts[0], t=numbers[0], stage=int(numbers[1]), p=numbers[2:5], axis=numbers[5], cross=numbers[6], health=numbers[7], mind=int(numbers[8]), prey=vector(prey[3]), goal=vector(prey[4]))
        if rows and row['t'] < rows[-1]['t']:
            raise ValueError('Nonmonotonic clock')
        rows.append(row)
        index += 2
    if set(goals) != {0, 1, 2} or rows[-1]['event'] != 'COMPLETE_ALL_STAGES' or rows[-1]['stage'] != 3:
        raise ValueError('Incomplete stages')
    if sum(r['event']=='COMPLETE_ALL_STAGES' for r in rows) != 1:
        raise ValueError('Duplicate completion')
    issues, stages = [], []
    previous_end = -1
    for i, contract in enumerate(ref['stages']):
        group = [r for r in rows if r['stage'] == i]
        active = [r for r in group if r['event'] in ('SPAWN', 'SAMPLE', 'NOISE', 'REACHED')]
        settled = [r for r in group if r['event'] == 'SETTLE']
        if not active or active[0]['event'] != 'SPAWN' or active[-1]['event'] != 'REACHED':
            raise ValueError('Incomplete consumer stage')
        if any(sum(r['event']==e for r in active) != 1 for e in ('SPAWN', 'REACHED')) or active[0]['t'] <= previous_end:
            raise ValueError('Duplicate or unordered stage')
        previous_end = active[-1]['t']
        if sum(r['event']=='SAMPLE' for r in active) < 2:
            raise ValueError('No continuous consumer evidence')
        if any(math.dist(r['goal'], goals[i]) > .001 for r in group):
            raise ValueError('Goal changed during stage')
        goal_axis = contract['goal_axis_m']
        if math.hypot(goals[i][0]-5184.0-1.0*goal_axis, goals[i][2]-7644.0+0.0*goal_axis) > .003:
            raise ValueError('Goal differs from frozen coordinate')
        p = np.array([r['p'] for r in active])
        d = (p[:,0]-5184.0)*1.0-(p[:,2]-7644.0)*0.0
        cross = (p[:,0]-5184.0)*0.0+(p[:,2]-7644.0)*1.0
        if max(abs(d-np.array([r['axis'] for r in active]))) > .015 or max(abs(cross-np.array([r['cross'] for r in active]))) > .015:
            raise ValueError('Recorded axes disagree with world position')
        road = sample(height, p[:,0]+200000, p[:,2])
        relative_y = p[:,1]-road
        drift = max(math.dist(r['prey'], r['goal']) for r in active)
        gap = max(b['t']-a['t'] for a,b in zip(active,active[1:]))
        duration = active[-1]['t']-active[0]['t']
        # Native values immediately after CreateObjectEx have been observed
        # outside the enum. Never credit such a value as stimulus response.
        # Vanilla sync range: P:/scripts/4_world/entities/creatures/infected/
        # zombiebase.c:54 is -1..4; -1 is an uninitialized sentinel.
        mind_samples = [r['mind'] for r in active if r['event']=='SAMPLE' and r['t'] >= active[0]['t']+1]
        passed = {
            'spawn_at_frozen_position': math.hypot(d[0]-contract['spawn_axis_m'],cross[0]) < .02,
            'positive_health': all(r['health']>0 for r in active),
            'physical_surface': bool(np.all((relative_y >= -.2) & (relative_y <= .5))),
            'fixed_prey': drift <= 2,
            'continuous_samples': gap <= 1,
            'within_timeout': duration <= ref['stage_timeout_s'],
            'known_mind_states_after_first_second': bool(mind_samples) and all(0 <= mind <= 4 for mind in mind_samples),
            'responded_to_stimulus': any(1 <= mind <= 4 for mind in mind_samples),
        }
        path_length = float(np.linalg.norm(np.diff(p, axis=0), axis=1).sum())
        direct_distance = math.dist(p[0], goals[i])
        goal_distance = math.dist(p[-1], goals[i])
        if open_ground:
            passed['reached_target_3d'] = goal_distance <= ref['goal_radius_m'] + ref['logged_position_tolerance_m']
            passed['bounded_path_length'] = path_length <= ref['path_max_length_factor'] * direct_distance
        else:
            passed['reached_frozen_axis'] = d[-1] >= contract['reach_axis_m']-.01 if i < 2 else d[-1] <= contract['reach_axis_m']+.01
            passed['within_road_corridor'] = bool(max(abs(cross)) <= 4)
        settlement_drift = None
        if ref.get('target_settlement_s'):
            final_settle = [r for r in settled if r['t'] >= active[0]['t']-5]
            settlement_drift = max((math.dist(r['prey'],r['goal']) for r in final_settle), default=None)
            passed['stable_before_spawn'] = len(final_settle) >= 20 and settlement_drift is not None and settlement_drift <= 2
        passed = {name: bool(ok) for name,ok in passed.items()}
        for check, ok in passed.items():
            if not ok: issues.append(f'stage{i}:{check}')
        stages.append(dict(stage=i, checks=passed, duration_s=duration, actor_samples=len(active), max_sample_gap_s=gap, axis_range_m=[float(min(d)),float(max(d))], maximum_lateral_m=float(max(abs(cross))), health_min=min(r['health'] for r in active), roadway_vertical_difference_m=[float(min(relative_y)),float(max(relative_y))], prey_max_drift_m=drift, settlement_drift_m=settlement_drift))
        stages[-1].update(path_length_m=path_length, direct_distance_m=direct_distance, final_distance_to_goal_m=goal_distance)
    return dict(status='FAIL_CONSUMER_ACCEPTANCE' if issues else 'PASS_NATIVE_AI_LOCAL_AND_BOTH_SUMMIT_TRAVERSES', issues=issues, stages=stages, limits=['One infected at a time and one client; not player capacity.', 'Only the tested summit corridor; no regional route acceptance.', 'Position records alone cannot establish movement authority; mission source has been inspected for overrides.', 'Graph sample-height validation is a separate gate for each navmesh version.'])


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--log', type=Path, required=True)
    ap.add_argument('--reference', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args=ap.parse_args()
    if args.out.exists(): raise ValueError('Fresh output required')
    reference = json.loads(args.reference.read_text())
    if reference.get('contract') == 'open_ground_v4' and sha(args.reference) != 'bc4108f85a07c89bd012daf74517acd5e609ed15597fa06a6fe1da04619fe7b5':
        raise ValueError('Frozen open-ground contract changed')
    asc=ROOT/'tests/regional_outline_v3/baltic_regional_outline_v3.asc'
    if sha(asc) != '3e2f6a9643ba4a8c58a86534c75de6033b7dbdf7a3de5d09a5ea46ff66680ac6': raise ValueError('Frozen height source drift')
    with rasterio.open(asc) as ds: heights=ds.read(1)
    raw=args.log.read_bytes()
    try: result=verify(raw.decode('utf-8-sig'),reference,heights)
    except (ValueError,KeyError,IndexError) as exc: result=dict(status='FAIL_PROBE_EVIDENCE',reason=str(exc))
    result.update(log_sha256=hashlib.sha256(raw).hexdigest(),reference_sha256=sha(args.reference),height_sha256=sha(asc))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result,indent=2))
    return 0 if result['status'].startswith('PASS') else 1


if __name__=='__main__':
    raise SystemExit(main())
