from pathlib import Path
import shutil
B=Path(__file__).parent;old=B.parent/'v30-volkhov-coupled-visible-20261009'
source=(old/'solve.py').read_text()
source=source.replace("xy=np.array([node['xz'] for node in gg['nodes']])","xy=np.array([node['xz'] for node in gg['nodes']])-np.array([c0*6,12282-r1*6])")
source=source.replace("lo=np.array([c0*6+.001,12282-r1*6+.001]);hi=np.array([c1*6-.001,12282-r0*6-.001])","lo=np.array([.001,.001]);hi=np.array([(c1-c0)*6-.001,(r1-r0)*6-.001])")
anchor="result=minimize(lambda x:np.mean((x-old[free])**2),old[free],method='SLSQP',"
replacement="""def central_jac(fun,x):
    columns=[]
    for k in range(len(x)):
        a=x.copy();b=x.copy();a[k]+=1e-5;b[k]-=1e-5
        columns.append((np.atleast_1d(fun(a))-np.atleast_1d(fun(b)))/2e-5)
    return np.asarray(columns).T
for constraint in constraints:
    constraint['jac']=lambda x,fn=constraint['fun']:central_jac(fn,x)
result=minimize(lambda x:np.mean((x-old[free])**2),old[free],jac=lambda x:2*(x-old[free])/len(free),method='SLSQP',"""
assert anchor in source;source=source.replace(anchor,replacement)
(B/'solve.py').write_text(source)
for name in ['verify.py','metrics.py']:shutil.copyfile(old/name,B/name)
