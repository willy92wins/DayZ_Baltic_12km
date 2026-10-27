"""Bind required benchmark files before launch and reject changes after capture.

The caller must attest the actual MCP run, loaded mod stack and process identity.
This tool hashes files; it does not discover what the engine loaded.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare(spec):
    if spec.get('world') not in ('BalticTrial','ChernarusPlus'):raise ValueError('Unsupported world')
    roles={k:str(Path(spec['artifacts'][k]).resolve()) for k in ('mission','executable','server_config')}
    if len(set(roles.values()))!=3 or Path(roles['mission']).name.lower()!='init.c':raise ValueError('Invalid artifact paths')
    packages={str(Path(p).resolve()):digest(p) for p in spec.get('packages',[])}
    if not packages:raise ValueError('Package stack required')
    inputs={p:digest(p) for p in roles.values()};inputs.update(packages)
    return dict(status='PRE_LAUNCH_BOUND',prepared_utc=datetime.now(timezone.utc).isoformat(),world=spec['world'],artifacts=roles,packages=packages,inputs=inputs,
                limits=['Caller must prove actual run identity, loaded package stack and absence of client/CE/AI.'])


def finish(snapshot,run_id,process_id,start_utc,engine,host):
    if snapshot.get('status')!='PRE_LAUNCH_BOUND':raise ValueError('Pre-launch snapshot required')
    if not isinstance(process_id,int) or process_id<=0 or not run_id or not start_utc:raise ValueError('Run identity required')
    before=datetime.fromisoformat(snapshot['prepared_utc'].replace('Z','+00:00'))
    started=datetime.fromisoformat(start_utc.replace('Z','+00:00'))
    if before.tzinfo is None or started.tzinfo is None or not before<=started<=datetime.now(timezone.utc):
        raise ValueError('Snapshot must precede process creation')
    for path,expected in snapshot['inputs'].items():
        if digest(path)!=expected:raise ValueError('Pre-launch input changed')
    report=dict(snapshot);report['artifacts']=dict(snapshot['artifacts']);report['inputs']=dict(snapshot['inputs'])
    for role,path in (('engine',engine),('host',host)):
        p=str(Path(path).resolve())
        if p in report['inputs']:raise ValueError('Capture aliases a bound artifact')
        report['artifacts'][role]=p;report['inputs'][p]=digest(p)
    report.update(status='CAPTURE_BOUND_NOT_YET_VALIDATED',run_id=run_id,process_id=process_id,start_utc=start_utc)
    return report


def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='mode',required=True)
    before=sub.add_parser('prepare');before.add_argument('--spec',type=Path,required=True)
    after=sub.add_parser('finish');after.add_argument('--snapshot',type=Path,required=True)
    for key in ('run-id','start-utc'):after.add_argument('--'+key,required=True)
    after.add_argument('--process-id',type=int,required=True)
    for key in ('engine','host'):after.add_argument('--'+key,type=Path,required=True)
    for child in (before,after):child.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    if a.out.exists():raise ValueError('Fresh output required')
    if a.mode=='prepare':report=prepare(json.loads(a.spec.read_text(encoding='utf-8-sig')))
    else:
        report=finish(json.loads(a.snapshot.read_text(encoding='utf-8-sig')),a.run_id,a.process_id,a.start_utc,a.engine,a.host)
        report['inputs'][str(a.snapshot.resolve())]=digest(a.snapshot)
    a.out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=report['status'],bound_files=len(report['inputs'])),indent=2))


if __name__=='__main__':main()
