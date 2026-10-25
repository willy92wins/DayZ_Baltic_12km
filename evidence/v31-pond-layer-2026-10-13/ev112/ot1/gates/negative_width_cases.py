"""Real-geometry width controls. Usage: script.py baseline fresh_out zero|slanted|diluted.
The diluted case deliberately demonstrates G2's aggregate limit, and requires
G7 to reject BOTH dry lateral controls of the one widened piece (>1000 total).
Other baseline failures cannot satisfy this targeted rejection.
"""
import copy,json,os,pathlib,subprocess,sys
import numpy as np
src,out=map(pathlib.Path,sys.argv[1:3]);mode=sys.argv[3];out.mkdir(exist_ok=False)
here=pathlib.Path(__file__).parent
rep=json.loads((src/'kit-report.json').read_text());allrecs=json.loads((src/'kit-records.json').read_text())
sid='100.0-0' if mode=='diluted' else '98.0-1'
assert json.loads((src/'gate-g2.json').read_text())[sid]['passed']
rep['sites']=[s for s in rep['sites'] if s['site']==sid]
recs=allrecs if mode=='diluted' else [r for r in allrecs if r['site']==sid]
proof=dict(mode=mode,baseline=str(src),site=sid)
if mode=='zero':recs=[r for r in recs if r['piece']=='stones']
if mode=='diluted':
    candidates=[r for r in recs if r['site']==sid and r['piece']!='stones']
    assert len(candidates)>1000
    straight=[r for r in candidates if r['model'].endswith('long_straight.p3d')]
    chosen=straight[len(straight)//2];chosen['matrix'][10]+=50
    proof.update(piece=chosen['piece'],pieces=len(candidates),height_delta=50)
if mode=='slanted':
    assert all('slanted' in r['model'] for r in recs if r['piece']!='stones')
    data={k:v for k,v in np.load(src/'terrain-kit.npz').items()}
    data['heights']=data['heights']-50
    np.savez(out/'terrain-kit.npz',**data)
else:os.link(src/'terrain-kit.npz',out/'terrain-kit.npz')
(out/'kit-records.json').write_text(json.dumps(recs));(out/'kit-report.json').write_text(json.dumps(rep))
proc=subprocess.run([sys.executable,'-I',str(here/'gate_g2_width.py'),str(out)],capture_output=True,text=True)
(out/'g2.log').write_text(proc.stdout+proc.stderr)
result=json.loads((out/'gate-g2.json').read_text())[sid]
proof.update(g2_exit=proc.returncode,g2_passed=result['passed'])
if mode=='diluted':
    own=next(p for p in result['local_width'] if p['piece']==chosen['piece'])
    assert own['width_p50']>12 and any(r['length_m']>10 for r in own['broad_runs']),own
    proof['wide_piece']=own
    os.link(src/'terrain-ev108.npz',out/'terrain-ev108.npz')
    fps=sorted((src/'bury-work').glob('fp*/footprint.npz'),key=lambda p:int(p.parent.name[2:]))
    target=out/'bury-work'/fps[-1].parent.name/'footprint.npz';target.parent.mkdir(parents=True);os.link(fps[-1],target)
    proc7=subprocess.run([sys.executable,'-I',str(here/'gate_g7_probe.py'),str(out)],capture_output=True,text=True)
    (out/'g7.log').write_text(proc7.stdout+proc7.stderr)
    points=json.loads((out/'probe/points.json.full.json').read_text())
    ids={p['id'] for p in points if p.get('site')==sid and p.get('piece')==chosen['piece'] and p['kind']=='kit_side'}
    result7=json.loads((out/'gate-g7.json').read_text())
    rejected={int(r[0]) for r in result7['failures'].get('dry_in_kit_sheet',{}).get('first',[])}
    proof.update(g7_exit=proc7.returncode,expected_dry_ids=sorted(ids),rejected_dry_ids=sorted(rejected),
                 passed=proc7.returncode==1 and len(ids)==2 and ids<=rejected)
else:
    proof['passed']=proc.returncode==1 and not result['passed']
    if mode=='zero':proof['passed'] &= result['sections']==0
    else:proof['passed'] &= result['width_p10_50_90'][1]>4
(out/'negative.json').write_text(json.dumps(proof,indent=2));print(json.dumps(proof))
sys.exit(0 if proof['passed'] else 1)
