from pathlib import Path
import importlib.util,json,hashlib
import numpy as np
R=Path(__file__).parent;path=R/'verify_pilot_bank_profiles_geos_20261028.py'
s=importlib.util.spec_from_file_location('oracle',path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
h=np.zeros((2048,2048));water=np.array([[4.,0.,6.],[8.,0.,6.]])
row=np.array([[1.,1.,6.],[6.,1.,6.],[11.,1.,6.]])
checks=[]
def check(name,row,water,h,expected):
    got,_=m.row(row,water,h);delta=abs(got-np.array(expected))
    assert delta.max()<=1e-12,(name,got,expected)
    checks.append(dict(name=name,expected=expected,actual=got.tolist(),max_residual=float(delta.max())))
check('flat_exposed',row,water,h,[1,1,1,5,5,5,5,3,3])
hidden=row.copy();hidden[:,1]=-1
check('flat_hidden',hidden,water,h,[-1,-1,-1,0,0,0,0,0,0])
wet=row.copy();wet[:,1]=.01;w=water.copy();w[:,1]=.02
check('above_ground_below_section_water',wet,w,h,[.01,.01,-.01,5,5,0,0,0,0])
h[:]=2;h[2046,1]=0
row=np.array([[0.,1.,6.],[3.,1.,6.],[12.,1.,6.]])
water=np.array([[2.,0.,6.],[4.,0.,6.]])
check('native_valley_between_stored_vertices',row,water,h,[-1,1,1,0,6,0,6,0,5])

h[:]=0
row=np.array([[1.,1.,6.],[6.,1.,6.],[11.,1.,6.]])
water=np.array([[4.5,0.,6.],[8.5,0.,6.]])
check('offset_actual_water_edges',row,water,h,[1,1,1,5,5,5,5,3.5,2.5])
source=dict(bed=np.zeros((2,39,3)),water=np.zeros((2,2,3)),station=np.array([0.,1.]))
grid=np.zeros((18,39,3));cap=np.ones(18,bool);cap[8:10]=False
f=dict(grid=grid.copy(),baseline_grid=grid.copy(),candidate_grid=grid.copy(),water=np.zeros((18,2,3)),extra_cap=cap,station=np.r_[np.arange(-8,0,dtype=float),source['station'],np.arange(2,10,dtype=float)])
m.source_guard(f,source,source)
mutants=[]
for name,ix in [('grid',(8,0,1)),('water',(8,0,1)),('candidate_grid',(8,0,1)),('extra_cap',(8,))]:
 q={k:v.copy() for k,v in f.items()};q[name][ix]=1
 try:m.source_guard(q,source,source)
 except ValueError as e:mutants.append(dict(field=name,rejected=str(e)))
 else:raise AssertionError('mutant escaped:'+name)
out=R/'pilot-bank-profile-consumer-fixtures-r2-20261028.json';assert not out.exists()
out.write_text(json.dumps(dict(status='FIVE_ANALYTIC_CONTROLS_AND_FOUR_LINEAGE_MUTANTS_PASS',consumer_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),checks=checks,lineage_mutants=mutants),indent=2)+'\n')
print('5 analytic controls +4 source-lineage mutants PASS')
