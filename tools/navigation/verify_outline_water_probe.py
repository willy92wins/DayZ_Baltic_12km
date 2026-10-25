"""Consume the frozen 24-point dynamic-water protocol without changing the scene."""
from pathlib import Path
import argparse, hashlib, json, math


def verify(text, reference):
    lines = text.splitlines()
    if not lines or lines[0] != 'BALTIC_OUTLINE_WATER_V1;BalticTrial':
        raise ValueError('Missing exact protocol/world header')
    points = reference['points']
    if len(points) != 24 or [p['index'] for p in points] != list(range(24)):
        raise ValueError('Wrong frozen point set')
    epochs = []
    complete = None
    max_ground_error = 0.0
    dry_margin = math.inf
    wet_depth = math.inf
    counts = {p['kind']: 0 for p in points}
    current = None
    def numbers(fields):
        values = [float(v) for v in fields]
        if not all(math.isfinite(v) for v in values):
            raise ValueError('Non-finite protocol data')
        return values
    for line in lines[1:]:
        fields = line.split(';')
        if complete is not None:
            raise ValueError('Data after completion')
        if fields[0] == 'SEA' and len(fields) == 8:
            if current is not None and current['count'] != 24:
                raise ValueError('Incomplete point epoch')
            t, tick, low, high, sea, wave_max, wave = numbers(fields[1:])
            if not (20 <= t <= 190 and low <= sea <= high and wave_max >= 0):
                raise ValueError('Invalid sea/window range')
            if epochs and not (0 < t-epochs[-1]['time'] <= 1 and tick > epochs[-1]['tick']):
                raise ValueError('Non-monotone clock or measurement gap')
            current = dict(time=t, tick=tick, count=0, sea=sea, maximum=high)
            epochs.append(current)
        elif fields[0] == 'S' and len(fields) == 10:
            t, index = numbers(fields[1:3])
            if current is None or index != current['count'] or t != current['time'] or index >= 24:
                raise ValueError('Wrong epoch/order or duplicate point')
            p = points[int(index)]
            if not fields[3].startswith('<') or not fields[3].endswith('>'):
                raise ValueError('Malformed native vector')
            xyz = numbers(fields[3][1:-1].split(','))
            ground, nofake, fake, depth = numbers(fields[4:8])
            if len(xyz) != 3 or max(abs(xyz[0]-p['xz'][0]),abs(xyz[2]-p['xz'][1])) > .001:
                raise ValueError('Frozen sample moved')
            if abs(xyz[1]-ground-10) > .005:
                raise ValueError('Unexpected query height')
            if fields[8] not in ('true','false') or fields[9] not in ('true','false'):
                raise ValueError('Malformed water classification')
            error = abs(ground-p['ground_m'])
            max_ground_error = max(max_ground_error,error)
            if error > .005:
                raise ValueError('Runtime terrain differs from accepted source')
            water = fields[8] == 'true' or fields[9] == 'true'
            if p['kind'].startswith('dry_'):
                margin = ground-max(nofake,fake)
                dry_margin = min(dry_margin,margin)
                if water or margin < .10:
                    raise ValueError('Dry sample flooded or dynamic freeboard below 10cm')
            elif p['kind'] == 'wet_control':
                clearance = min(nofake,fake)-ground
                wet_depth = min(wet_depth,clearance)
                if not water or clearance < .15:
                    raise ValueError('Wet control lost water or 15cm depth')
            else:
                raise ValueError('Unexpected sample class')
            counts[p['kind']] += 1
            current['count'] += 1
        elif fields[0] == 'COMPLETE' and len(fields) == 2:
            complete = numbers(fields[1:])[0]
            if not 198 <= complete <= 205:
                raise ValueError('Wrong completion time')
        else:
            raise ValueError('Unexpected protocol row')
    if (complete is None or current is None or current['count'] != 24 or len(epochs) < 600
            or epochs[0]['time'] > 21 or epochs[-1]['time'] < 189):
        raise ValueError('Incomplete bounded measurement window')
    return dict(status='PASS_LOCAL_DYNAMIC_WATER',epochs=len(epochs),samples=sum(counts.values()),
                first_s=epochs[0]['time'],last_s=epochs[-1]['time'],complete_s=complete,
                ground_max_error_m=max_ground_error,minimum_dry_freeboard_m=dry_margin,
                minimum_wet_depth_m=wet_depth,classes=counts,
                observed_sea_range_m=[min(e['sea'] for e in epochs),max(e['sea'] for e in epochs)],
                limits=['Only the frozen 24 local positions and observed time window.',
                        'Not a global ocean/fake-wave maximum, visual acceptance or regional navmesh test.'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log',type=Path,required=True)
    parser.add_argument('--reference',type=Path,required=True)
    parser.add_argument('--reference-sha256',required=True)
    parser.add_argument('--out',type=Path,required=True)
    a=parser.parse_args()
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert sha(a.reference)==a.reference_sha256 and not a.out.exists()
    try:
        report=verify(a.log.read_text(encoding='utf-8-sig'),json.loads(a.reference.read_text()))
    except ValueError as error:
        report=dict(status='FAIL_LOCAL_DYNAMIC_WATER',reason=str(error))
    report.update(log_sha256=sha(a.log),reference_sha256=sha(a.reference))
    a.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
    raise SystemExit(0 if report['status'].startswith('PASS') else 1)


if __name__=='__main__':main()
