"""Archive exact-run RPT/script logs using the recorded lifecycle identities."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import re


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--identity',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    run=json.loads(args.identity.read_text())
    if not run.get('run_id') or not run.get('processes'):
        raise ValueError('One recorded lifecycle run required')
    receipt=args.out/'archive.json'
    if receipt.exists():raise ValueError('Preserve prior archive')
    planned=[]
    for process in run['processes']:
        role=process['role']
        if role not in ('server','client'):raise ValueError('Unknown process role')
        folder=Path('P:/DayZ_MCP_dev')/('_'+role)/'profiles'
        start=datetime.fromisoformat(process['creation_time_utc'].replace('Z','+00:00'))
        for pattern,label in [('DayZDiag_x64_*.RPT','RPT'),('script_*.log','script.log')]:
            candidates=[]
            for path in folder.glob(pattern):
                match=re.search(r'(\d{4}-\d\d-\d\d_\d\d-\d\d-\d\d)',path.name)
                if not match:continue
                # Filename uses the host's local timezone; lifecycle uses UTC.
                stamp=datetime.strptime(match[1],'%Y-%m-%d_%H-%M-%S').astimezone(timezone.utc)
                if -1<=(stamp-start).total_seconds()<=30:candidates.append(path)
            if len(candidates)!=1:
                raise ValueError(f'Nonunique {role} {label} for {start}: {candidates}')
            source=candidates[0]
            if role=='server' and label=='RPT':
                with source.open(errors='replace') as stream:header=stream.read(8192)
                if Path(run['mission']).name not in header:
                    raise ValueError('Server RPT mission differs from lifecycle')
            target=args.out/(role+'-'+label)
            if target.exists():raise ValueError(f'Preserve {target}')
            planned.append((source,target))
    args.out.mkdir(parents=True,exist_ok=True)
    records={}
    for source,target in planned:
        raw=source.read_bytes()
        with target.open('xb') as stream:stream.write(raw)
        digest=hashlib.sha256(raw).hexdigest()
        assert hashlib.sha256(target.read_bytes()).hexdigest()==digest
        records[str(source)]={'copy':target.name,'sha256':digest,'bytes':len(raw)}
    receipt.write_text(json.dumps({'run_id':run['run_id'],'archived_utc':datetime.now(timezone.utc).isoformat(),
        'identity_sha256':hashlib.sha256(args.identity.read_bytes()).hexdigest(),'files':records},indent=2)+'\n')
    print(json.dumps({'run_id':run['run_id'],'files':len(records),'receipt':str(receipt)}))


if __name__=='__main__':main()
