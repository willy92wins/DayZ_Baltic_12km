"""Independent native-grid V-banks on the second (inverse) elbow leg.
Equal-width mirrored fixtures: -2.6/+1.0 must fail the asymmetric band;
-1.0/+2.6 must pass. Real model faces and transform, no generator imports.
The short wet span isolates the flat central face and normal orientation only.
Usage: script.py baseline_run fresh_output_dir
"""
import copy,json,pathlib,subprocess,sys
import numpy as np
src,out=map(pathlib.Path,sys.argv[1:3]);out.mkdir(exist_ok=False)
recs=json.loads((src/'kit-records.json').read_text())
record=copy.deepcopy(next(r for r in recs if r['site']=='98.0-1' and r['model'].endswith('short_slanted_inv.p3d')))
record['site']='normal-sign'
matrix=np.array(record['matrix']);scale=float(np.linalg.norm(matrix[3:6]));x,y,z=matrix[9:12]
assert abs(x/6-round(x/6))<1e-8 and abs(matrix[0]-scale)<1e-8 and abs(matrix[8]-scale)<1e-8
water=y+.2869*scale
rows=[]
for name,left,right,want in [('left_outside',2.6,1.0,1),('mirrored_inside',1.0,2.6,0)]:
    run=out/name;run.mkdir()
    data={k:v for k,v in np.load(src/'terrain-kit.npz').items()}
    dx=np.arange(2048)*6-x
    row=water-.3+np.where(dx<0,.3*(-dx)/(left*scale),.3*dx/(right*scale))
    data['heights']=np.tile(row.astype(np.float32),(2048,1))
    np.savez(run/'terrain-kit.npz',**data)
    site=dict(site='normal-sign',lattice=[[float(x),float(z-6)],[float(x),float(z+6)]],wet_span=[6.0,6.4])
    (run/'kit-records.json').write_text(json.dumps([record]));(run/'kit-report.json').write_text(json.dumps(dict(sites=[site])))
    cmd=[sys.executable,'-I',str(pathlib.Path(__file__).with_name('gate_g2_width.py')),str(run)]
    proc=subprocess.run(cmd,capture_output=True,text=True);(run/'gate.log').write_text(proc.stdout+proc.stderr)
    result=json.loads((run/'gate-g2.json').read_text())['normal-sign']
    rows.append(dict(case=name,exit=proc.returncode,expected_exit=want,passed=proc.returncode==want,
                     width=result.get('width_p10_50_90'),outside=result.get('edge_outside_band_share'),samples=result.get('sections')))
result=dict(passed=all(r['passed'] for r in rows),cases=rows)
(out/'negative-sign.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
sys.exit(0 if result['passed'] else 1)
