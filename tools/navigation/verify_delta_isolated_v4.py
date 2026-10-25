"""Frozen V3 physical/event checks plus an independent no-overlap clock gate."""
from pathlib import Path
import argparse,hashlib,json
import rasterio
from verify_full_river_v3 import check

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--reference',required=True,type=Path);ap.add_argument('--folder',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args();assert not a.out.exists()
    ref=json.loads(a.reference.read_text(encoding='utf-8'));assert [x['case'] for x in ref['cases']]==[8,10]
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    for path,digest in {**ref['mission'],ref['terrain']:ref['terrain_sha256']}.items():assert sha(Path(path))==digest,path
    with rasterio.open(ref['terrain']) as ds:h=ds.read(1)
    report=check(ref,a.folder,h);clocks={};parse_ok=True
    for case in [8,10]:
        clocks[case]={}
        for line in (a.folder/f'{ref["log_prefix"]}{case}.log').read_text(encoding='utf-8').splitlines():
            fields=line.split(';')
            if fields[0] in ['ABS_SPAWN_MS','ABS_END_MS']:
                if len(fields)!=3 or int(fields[1])!=case or fields[0] in clocks[case]:parse_ok=False;continue
                clocks[case][fields[0]]=int(fields[2])
    valid=parse_ok and all(set(v)=={'ABS_SPAWN_MS','ABS_END_MS'} and v['ABS_END_MS']>v['ABS_SPAWN_MS'] for v in clocks.values())
    isolated=valid and clocks[10]['ABS_SPAWN_MS']>clocks[8]['ABS_END_MS']
    report.update(status='PASS_TWO_ISOLATED_DELTA_SEGMENTS' if isolated and all(x['status']=='PASS' for x in report['cases']) else 'FAIL_OR_INCOMPLETE',clock_schema=valid,isolated=isolated,server_clocks_ms=clocks,reference_sha256=sha(a.reference))
    a.out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:report[k] for k in ['status','isolated','server_clocks_ms']}));raise SystemExit(0 if report['status'].startswith('PASS_') else 1)

if __name__=='__main__':main()
