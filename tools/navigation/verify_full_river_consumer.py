"""Apply the existing physical boat verifier independently to each full-river log."""
from pathlib import Path
import argparse
import hashlib
import json
import rasterio
from verify_regional_boat_consumer import verify

sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()


def check(reference,folder,height):
    results=[]
    logs={}
    prefix=reference.get('log_prefix','baltic_fullriver_v1_')
    if prefix not in ('baltic_fullriver_v1_','baltic_fullriver_v2_'):
        raise ValueError('Unknown bounded log prefix')
    for case in reference['cases']:
        path=folder/f'{prefix}{case["case"]}.log'
        if not path.exists():
            results.append(dict(case=case['case'],river=case['river'],status='INCOMPLETE',reason='Missing case log'))
            continue
        single=dict(reference,cases=[case])
        data=verify(single,path.read_text(encoding='utf-8-sig').splitlines(),height)
        logs[path.name]=sha(path)
        results.append(dict(case=case['case'],river=case['river'],part=case['part'],length_m=case['length_m'],
                            status='PASS' if data['status'].startswith('PASS_') else 'FAIL_OR_INCOMPLETE',
                            physical=data,log_sha256=sha(path)))
    passed=all(x['status']=='PASS' for x in results)
    return dict(status='PASS_EMPTY_BOAT_SELECTED_MAIN_CHANNEL_COVERAGE' if passed else 'FAIL_OR_INCOMPLETE',
                cases=results,logs_sha256=logs,
                passing_segment_m=sum(x['length_m'] for x in results if x['status']=='PASS'),
                distinct_planned_channel_m=sum(x['length_m'] for x in reference['channels']),
                all_planned_intervals_pass=passed,limits=reference['limits'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference',type=Path,required=True)
    parser.add_argument('--folder',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists():raise ValueError('Preserve prior evidence')
    reference=json.loads(args.reference.read_text())
    for path,digest in reference['mission'].items():
        if sha(Path(path))!=digest:raise ValueError('Frozen mission changed: '+path)
    terrain=Path(reference['terrain'])
    if sha(terrain)!=reference['terrain_sha256']:raise ValueError('Frozen terrain changed')
    with rasterio.open(terrain) as ds:height=ds.read(1)
    report=check(reference,args.folder,height)
    report.update(reference_sha256=sha(args.reference),terrain_sha256=sha(terrain))
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],cases=[dict(case=x['case'],status=x['status']) for x in report['cases']],
                         distinct_planned_channel_m=report['distinct_planned_channel_m']),indent=2))
    raise SystemExit(0 if report['status'].startswith('PASS_') else 1)
