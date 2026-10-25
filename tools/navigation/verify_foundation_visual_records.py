"""Verify fixed-camera telemetry and restoration; report client counters descriptively.

This cannot accept appearance. The captured pixels still need visual inspection.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import re
import statistics


def vec(text):
    if not re.fullmatch(r'<-?\d+\.\d{6},\s*-?\d+\.\d{6},\s*-?\d+\.\d{6}>', text):
        raise ValueError('Precise camera vector required')
    return [float(x) for x in text[1:-1].split(',')]


def distance(a, b):
    return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))


def blocks(text, prefix='BALTIC_FOUNDATION_VISUAL_V2'):
    result = {}
    current = None
    for line in text.splitlines():
        if line.startswith(prefix+' '):
            marker, elapsed = line.removeprefix(prefix+' ').split(' elapsed=')
            if marker in result:
                raise ValueError('Duplicate camera marker')
            current = dict(elapsed=float(elapsed))
            result[marker] = current
        elif line:
            if current is None or '=' not in line:
                raise ValueError('Malformed camera log')
            name, value = line.split('=',1)
            if name in current:
                raise ValueError('Duplicate camera field')
            current[name] = value
    return result


def verify_camera(text, reference):
    data = blocks(text, reference.get('camera_header', 'BALTIC_FOUNDATION_VISUAL_V2'))
    capture_event = reference.get('capture_event', 'CAPTURE_REQUEST')
    capture_at = float(reference.get('capture_at_phase_s',25))
    if not math.isfinite(capture_at) or capture_at<3:
        raise ValueError('Invalid frozen capture time')
    if any(capture_at>=p['end_s']-p['start_s'] for p in reference['poses']):
        raise ValueError('Capture time outside frozen pose')
    expected = {'START','COMPLETE_RESTORED_SETTLED'}
    for pose in reference['poses']:
        expected.update(f'{event}_{pose["phase"]}' for event in ('POSE','SETTLED',capture_event))
    if set(data) != expected:
        raise ValueError('Incomplete/unknown camera markers')
    issues = []
    for pose in reference['poses']:
        phase = pose['phase']
        direction = [b-a for a,b in zip(pose['position'],pose['target'])]
        length = math.sqrt(sum(x*x for x in direction))
        direction = [x/length for x in direction]
        for event in ('SETTLED',capture_event):
            record = data[f'{event}_{phase}']
            checks = dict(world=record['world']=='BalticTrial',
                          position=distance(vec(record['camera']),pose['position'])<=0.003,
                          direction=distance(vec(record['direction']),direction)<=0.0001,
                          camera_active=record['camera_active']=='true',camera_frozen=record['camera_frozen']=='true',
                          fov=abs(float(record['current_fov'])-1.04719755)<=0.0001,
                          time=pose['start_s']+3<=record['elapsed']<pose['end_s'],
                          view=float(record['requested_view_distance'])==pose['view_requested'])
            near = float(record['original_near_plane']) if pose['nearplane_requested']=='original' else pose['nearplane_requested']
            checks['nearplane'] = abs(float(record['near_plane'])-near)<=0.00001
            weather = [float(x) for x in record['weather'].split(';')]
            checks['weather'] = len(weather)==4 and abs(weather[0]-.1)<=.025 and all(abs(x)<=.001 for x in weather[1:])
            if event==capture_event:
                checks['capture_time'] = abs(record['elapsed']-pose['start_s']-capture_at)<=2
            issues.extend(f'{event}_{phase}:{name}' for name,passed in checks.items() if not passed)
    original = data['POSE_0']
    restored = data['COMPLETE_RESTORED_SETTLED']
    restoration = dict(position=distance(vec(restored['camera_native_position']),vec(original['saved_position']))<=0.000002,
                       orientation=distance(vec(restored['camera_native_orientation']),vec(original['saved_orientation']))<=0.000002,
                       nearplane=abs(float(restored['near_plane'])-float(original['original_near_plane']))<=0.00001,
                       fov=abs(float(restored['current_fov'])-float(original['saved_fov']))<=0.0001,
                       active=restored['camera_active']==original['saved_active'],frozen=restored['camera_frozen']==original['saved_frozen'],
                       view=float(restored['requested_view_distance'])==reference['restoration_view_distance'],
                       time=reference['finish_s']<=restored['elapsed']<=reference['finish_s']+2)
    issues.extend('restoration:'+name for name,passed in restoration.items() if not passed)
    return dict(status='PASS_CAMERA_TELEMETRY_AND_RESTORE' if not issues else 'FAIL_CAMERA_TELEMETRY',
                issues=issues,poses=len(reference['poses']),restoration=restoration,
                limit='Actual images require separate visual review; the view distance getter is not exposed and requested value is not an observed effective range.')


def summarize_metrics(text, reference):
    window=reference.get('metrics_window_phase_s',[10,40])
    capture_at=float(reference.get('capture_at_phase_s',25))
    if len(window)!=2 or not all(map(math.isfinite,window)) or not 3<=window[0]<window[1]:
        raise ValueError('Invalid frozen metric window')
    if any(window[1]>=p['end_s']-p['start_s'] for p in reference['poses']):
        raise ValueError('Metric window outside frozen pose')
    lines = text.splitlines()
    if not lines or lines[0]!=reference.get('metrics_header', 'BALTIC_FOUNDATION_CLIENT_METRICS_V2'):
        raise ValueError('Wrong client metrics header')
    groups = {pose['phase']:[] for pose in reference['poses']}
    previous = -1
    for line in lines[1:]:
        fields = line.split(';')
        columns = reference.get('metrics_columns', 10)
        if columns not in (9,10) or len(fields)!=columns or fields[0]!='F':
            raise ValueError('Malformed client metric')
        phase = int(fields[1])
        numbers = [float(x) for x in fields[2:-1]]
        if phase not in groups or not all(map(math.isfinite,numbers)) or numbers[0]<=previous:
            raise ValueError('Wrong phase or metric clock')
        previous = numbers[0]
        pose = reference['poses'][phase]
        if distance(vec(fields[-1]),pose['position'])>.003:
            raise ValueError('Metrics came from another camera')
        elapsed = numbers[0]-pose['start_s']
        if not window[0]<=elapsed<=window[1]+.01:
            raise ValueError('Metrics outside frozen window')
        if capture_at-2<=elapsed<=capture_at+3:
            continue
        groups[phase].append(numbers)
    reports=[]
    for phase, values in groups.items():
        if len(values)<20:
            raise ValueError('Insufficient client metrics outside capture interval')
        # Numbers: elapsed, native tick, lastFPS, avg64, min64, max64, globalFPS.
        valid = all(all(x>0 for x in row[2:]) and row[4]<=row[3]+.1<=row[5]+.2 for row in values)
        if not valid:
            raise ValueError('Native counters failed basic ranges')
        reports.append(dict(phase=phase,name=reference['poses'][phase]['name'],samples=len(values),
                            avg64_median=statistics.median(row[3] for row in values),
                            avg64_range=[min(row[3] for row in values),max(row[3] for row in values)],
                            native_min64_min=min(row[4] for row in values),native_max64_max=max(row[5] for row in values),
                            global10_median=statistics.median(row[6] for row in values) if len(values[0])==7 else None))
    return dict(status='COMPLETE_CLIENT_NATIVE_COUNTER_MEASUREMENT',phases=reports,
                limits=['Counters reported by the client APIs; not headless server throughput.',
                        'One client, empty terrain, local machine and diagnostic aerial views; not multiplayer capacity.',
                        'Frozen capture interval (-2 to +3s) omitted before summarizing. No performance threshold was predeclared.'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference',type=Path,required=True)
    parser.add_argument('--folder',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists(): raise ValueError('Preserve prior evidence')
    reference=json.loads(args.reference.read_text())
    report={}
    for key, function, path in [('camera',verify_camera,args.folder/'camera.log'),
                               ('metrics',summarize_metrics,args.folder/'client-metrics.log')]:
        try: report[key]=function(path.read_text(encoding='utf-8-sig'),reference)
        except (ValueError,KeyError,IndexError) as error: report[key]=dict(status='FAIL',reason=str(error))
    report['sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [args.reference,args.folder/'camera.log',args.folder/'client-metrics.log']}
    args.out.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(report,indent=2))
    raise SystemExit(0 if report['camera']['status'].startswith('PASS') and report['metrics']['status'].startswith('COMPLETE') else 1)
