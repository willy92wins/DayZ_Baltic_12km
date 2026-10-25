"""Four independent corruptions of absolute clocks from a real passing case."""
from pathlib import Path
import argparse,hashlib,json
from verify_river_singleton import clock_check

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--log',type=Path,required=True);ap.add_argument('--case',type=int,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists()
    rows=a.log.read_text(encoding='utf-8-sig').splitlines();positive=clock_check(rows,a.case);assert positive['passed']
    spawn=next(l for l in rows if l.startswith('ABS_SPAWN_MS;'));end=next(l for l in rows if l.startswith('ABS_END_MS;'))
    mutations={'missing_end':[l for l in rows if l!=end],'duplicate_spawn':rows+[spawn],'end_before_spawn':[f'ABS_END_MS;{a.case};0' if l==end else l for l in rows],'wrong_elapsed':[f'ABS_END_MS;{a.case};{positive["clocks"]["ABS_END_MS"]+10000}' if l==end else l for l in rows]}
    result=[]
    for label,data in mutations.items():
        observed=clock_check(data,a.case);assert not observed['passed'],label;result.append(dict(name=label,status='EXPECTED_REJECTION'))
    report=dict(status='PASS_REAL_CLOCK_AND_FOUR_NEGATIVES',case=a.case,source_sha256=hashlib.sha256(a.log.read_bytes()).hexdigest(),positive=positive,controls=result)
    a.out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(status=report['status'],case=a.case)))

if __name__=='__main__':main()
