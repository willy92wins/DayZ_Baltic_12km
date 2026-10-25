"""Summarize external process counters; never reinterpret these as player FPS."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def summarize(rows):
    if len(rows) != 170 or [r['sample'] for r in rows] != list(range(170)):
        raise ValueError('Incomplete process measurement')
    if len({(r['process_id'],r['start_utc']) for r in rows}) != 1:
        raise ValueError('Process identity changed')
    for a,b in zip(rows,rows[1:]):
        duration=b['elapsed_s']-a['elapsed_s']
        if not .9 <= duration <= 3 or b['cpu_total_s'] < a['cpu_total_s']:
            raise ValueError('Clock gap or regressing CPU counter')
    for r in rows:
        if not all(math.isfinite(r[k]) and r[k] > 0 for k in ['elapsed_s','working_set_bytes','private_bytes']):
            raise ValueError('Invalid measurement')
    def interval(part):
        a,b=part[0],part[-1]
        duration=b['elapsed_s']-a['elapsed_s']
        return {'samples':len(part),'elapsed_interval_s':[a['elapsed_s'],b['elapsed_s']],
                'wall_s':duration,'cpu_s':b['cpu_total_s']-a['cpu_total_s'],
                'mean_cpu_percent_of_one_logical_core':100*(b['cpu_total_s']-a['cpu_total_s'])/duration,
                'working_set_mib_range':[min(r['working_set_bytes'] for r in part)/1048576,max(r['working_set_bytes'] for r in part)/1048576],
                'private_mib_range':[min(r['private_bytes'] for r in part)/1048576,max(r['private_bytes'] for r in part)/1048576]}
    return {'status':'PASS_COMPLETE_HOST_PROCESS_MEASUREMENT','full':interval(rows),
            'after_editor_closed':interval([r for r in rows if 60<=r['elapsed_s']<=140]),
            'limits':['Single development host, no players/CE/AI; no capacity conclusion.',
                      'CPU is total process CPU divided by wall time, expressed relative to one logical core.',
                      'Second interval excludes the earlier Terrain Builder closure; it is not an independent run.']}


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    if args.out.exists(): raise ValueError('Fresh output required')
    raw=args.input.read_bytes()
    result=summarize([json.loads(line) for line in raw.decode('utf-8-sig').splitlines()])
    result['input_sha256']=hashlib.sha256(raw).hexdigest()
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
