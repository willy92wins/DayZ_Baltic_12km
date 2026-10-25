"""Reject corrupted camera/metric records using an actual complete positive tour."""
from pathlib import Path
import argparse
import hashlib
import json
from verify_foundation_visual_records import verify_camera, summarize_metrics, blocks, vec


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--folder', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists(): raise ValueError('Preserve prior evidence')
    ref = json.loads(args.reference.read_text())
    camera = (args.folder/'camera.log').read_text(encoding='utf-8-sig')
    metrics = (args.folder/'client-metrics.log').read_text(encoding='utf-8-sig')
    if not verify_camera(camera, ref)['status'].startswith('PASS_'):
        raise ValueError('Actual passing camera run required')
    summarize_metrics(metrics, ref)

    prefix=ref.get('camera_header', 'BALTIC_FOUNDATION_VISUAL_V2')
    capture=ref.get('capture_event', 'CAPTURE_REQUEST')
    def field(text, marker, name, replacement):
        lines = text.splitlines()
        start = next(i for i, line in enumerate(lines) if line.startswith(prefix+' '+marker+' elapsed='))
        end = next((i for i in range(start+1, len(lines)) if lines[i].startswith(prefix+' ')), len(lines))
        matches = [i for i in range(start+1, end) if lines[i].startswith(name+'=')]
        if len(matches) != 1: raise ValueError('Unique field required')
        lines[matches[0]] = name+'='+replacement
        return '\n'.join(lines)+'\n'

    restored_position=vec(blocks(camera,prefix)['COMPLETE_RESTORED_SETTLED']['camera_native_position'])
    restored_position[0]+=1
    moved_restore='<'+', '.join(f'{v:.6f}' for v in restored_position)+'>'
    camera_mutations = {
        'wrong_camera': field(camera, 'SETTLED_0', 'camera', '<0.000000, 0.000000, 0.000000>'),
        'wrong_direction': field(camera, 'SETTLED_0', 'direction', '<0.000000, 0.000000, 0.000000>'),
        'wrong_world': field(camera, capture+'_0', 'world', 'ChernarusPlus'),
        'rain': field(camera, capture+'_0', 'weather', '0.1;1;0;0'),
        'wrong_nearplane': field(camera, 'SETTLED_0', 'near_plane', '20'),
        'camera_inactive': field(camera, 'SETTLED_0', 'camera_active', 'false'),
        'restore_pose': field(camera, 'COMPLETE_RESTORED_SETTLED', 'camera_native_position', moved_restore),
        'missing_restoration': camera[:camera.index(prefix+' COMPLETE_RESTORED_SETTLED')],
        'duplicate_marker': camera+camera[camera.index(prefix+' COMPLETE_RESTORED_SETTLED'):],
    }
    capture_line=next(line for line in camera.splitlines() if line.startswith(prefix+' '+capture+'_0 elapsed='))
    wrong_capture_line=capture_line.split(' elapsed=')[0]+' elapsed='+str(float(capture_line.split(' elapsed=')[1])+5)
    camera_mutations['wrong_capture_time']=camera.replace(capture_line,wrong_capture_line,1)
    metric_lines = metrics.splitlines()
    selected = next(i for i, line in enumerate(metric_lines) if line.startswith('F;0;'))
    def metric_field(index, value):
        lines = metric_lines.copy(); row = lines[selected].split(';'); row[index] = value; lines[selected] = ';'.join(row)
        return '\n'.join(lines)+'\n'
    metric_mutations = {
        'missing_phase': '\n'.join(line for line in metric_lines if not line.startswith('F;0;'))+'\n',
        'nonfinite_counter': metric_field(4, 'nan'),
        'zero_counter': metric_field(4, '0'),
        'wrong_metric_camera': metric_field(ref.get('metrics_columns',10)-1, '<0.000000, 0.000000, 0.000000>'),
        'duplicate_sample': '\n'.join(metric_lines[:selected]+[metric_lines[selected]]+metric_lines[selected:])+'\n',
    }
    window=ref.get('metrics_window_phase_s',[10,40])
    metric_mutations['before_frozen_metric_window']=metric_field(2,str(ref['poses'][0]['start_s']+window[0]-1))
    late=metric_lines.copy();last=next(i for i in range(len(late)-1,0,-1) if late[i].startswith('F;0;'))
    row=late[last].split(';');row[2]=str(ref['poses'][0]['start_s']+window[1]+1);late[last]=';'.join(row)
    metric_mutations['after_frozen_metric_window']='\n'.join(late)+'\n'
    results=[]
    for category, mutations, original, function in [('camera', camera_mutations, camera, verify_camera),
                                                       ('metrics', metric_mutations, metrics, summarize_metrics)]:
        for name, text in mutations.items():
            if text.strip() == original.strip(): raise ValueError('Unchanged negative control: '+name)
            rejected=False; detail=''
            try:
                report=function(text, ref)
                rejected=report['status'].startswith('FAIL')
                detail=report.get('issues', [])
            except (ValueError, KeyError, IndexError) as error:
                rejected=True; detail=str(error)
            if not rejected: raise ValueError('False acceptance: '+name)
            results.append(dict(category=category, name=name, status='EXPECTED_REJECTION', detail=detail,
                                log_sha256=hashlib.sha256(text.encode()).hexdigest()))
    result=dict(status='PASS_REAL_CAMERA_METRICS_AND_NEGATIVES', controls=results,
                reference_sha256=hashlib.sha256(args.reference.read_bytes()).hexdigest(),
                source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [args.folder/'camera.log',args.folder/'client-metrics.log']},
                limit='Telemetry checks only. These controls do not accept image appearance or performance.')
    args.out.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(status=result['status'], negatives=len(results))))


if __name__ == '__main__':
    main()
