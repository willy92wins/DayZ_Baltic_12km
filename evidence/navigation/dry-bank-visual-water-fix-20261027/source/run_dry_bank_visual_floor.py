"""Bounded own-child runner: timeout/failure cannot become an exit-zero PASS."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
import time

def bounded(command, cwd, output, seconds):
    start=time.monotonic();timed_out=False
    with (output/'stdout.log').open('wb') as out,(output/'stderr.log').open('wb') as err:
        child=subprocess.Popen(command,cwd=cwd,stdout=out,stderr=err,creationflags=0x08000000)
        try:rc=child.wait(timeout=seconds)
        except subprocess.TimeoutExpired:
            timed_out=True;child.terminate();child.wait(timeout=30);rc=124
    result=dict(returncode=rc,timeout=timed_out,seconds=time.monotonic()-start)
    (output/'completion.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return rc

def main():
    p=argparse.ArgumentParser()
    for name in ('context','output','candidate-output'):p.add_argument('--'+name,required=True,type=Path)
    args=p.parse_args();args.output.mkdir(exist_ok=False)
    ctx=json.loads(args.context.read_text(encoding='utf-8-sig'))
    root=Path(__file__).parent
    rc=bounded([sys.executable,'-I',str(root/'pilot_dry_bank_visual_floor.py'),'--context',str(args.context),
                '--output',str(args.candidate_output)],ctx['worktree'],args.output,900)
    if rc:return rc
    report=args.candidate_output/'author-report.json';candidate=args.candidate_output/'candidate-surfaces.npz'
    if not report.is_file() or not candidate.is_file():return 3
    payload=json.loads(report.read_text(encoding='utf-8-sig'))
    if payload['status']!='AUTHORED_PENDING_INDEPENDENT_CHECK':return 3
    if hashlib.sha256(candidate.read_bytes()).hexdigest()!=payload['candidate_sha256']:return 3
    # CLI consumer has no access to author's free mask or PASS booleans.
    command=[sys.executable,'-I',str(root/'verify_dry_bank_visual_floor.py'),'--baseline',ctx['paths']['source'],
             '--candidate',str(candidate),'--context',str(args.context),'--output',str(args.output/'result.json')]
    validation=args.output/'validation';validation.mkdir()
    return bounded(command,ctx['worktree'],validation,300)

if __name__=='__main__':sys.exit(main())
