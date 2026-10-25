"""Analytic shoreline/hole controls and real boat-consumer gate for tiled water."""
from pathlib import Path
import argparse,csv,hashlib,json
import numpy as np
ROOT=Path(__file__).resolve().parents[2]

def verify(raw,static=False,version=1):
    rows=list(csv.reader(raw.decode('utf-8-sig').splitlines(),delimiter=';'))
    header=f'BALTIC_STATIC_SHAPE_V{version}' if static else 'BALTIC_SHAPE_BOAT_V3'
    checks={'header':rows[0]==[header],'complete':rows[-1]==['END','DISTANCE_SAFETY_STOP']}
    water=[r for r in rows if r[0]=='WATER'];hole=[r for r in rows if r[0]=='HOLE'];sea=[r for r in rows if r[0]=='SEA']
    expected={(stage,x,y,z) for stage in ('BEFORE','AFTER') for x in range(400,601,25) for y in range(0,10,3) for z in range(2900,3201,25)}
    keys=[(r[1],int(r[2]),int(r[3]),int(r[4])) for r in water if len(r)==10]
    checks['water_grid']=len(keys)==len(expected) and set(keys)==expected
    hits=[];outside=[]
    for r in water:
        if len(r)!=10:return {'status':'FAIL','checks':dict(checks,water_schema=False)}
        x,z=int(r[2]),int(r[4]);stage=r[1]
        if x in (450,550,650) or z in (2950,3050,3150):continue
        wet=(static or stage=='AFTER') and 450<x<650 and 2950<z<3150 and (x<550 or z<3050)
        (hits if wet else outside).append(r[7]==str(wet).lower() and (abs(float(r[9])-6)<.001 if wet else float(r[9])<2))
    checks.update(wet=bool(hits and all(hits)),dry_exterior=bool(outside and all(outside)))
    keys=[tuple(map(int,r[1:3])) for r in hole if len(r)==5]
    checks['hole_grid']=len(keys)==529 and set(keys)=={(x,z) for x in range(-110,111,10) for z in range(-110,111,10)}
    hgood=[];hdry=[]
    for r in hole:
        if len(r)!=5:return {'status':'FAIL','checks':dict(checks,hole_schema=False)}
        x,z=map(int,r[1:3])
        if abs(x) in (20,100) or abs(z) in (20,100):continue
        wet=abs(x)<100 and abs(z)<100 and (abs(x)>20 or abs(z)>20)
        (hgood if wet else hdry).append(r[4]==str(wet).lower() and (abs(float(r[3])-6)<.001 if wet else float(r[3])<2))
    checks.update(hole_wet_control=bool(hgood and all(hgood)),hole_dry_control=bool(hdry and all(hdry)))
    sw=[r for r in rows if r[0]=='W'];checks['sea_grid']=len(sea)==6 and len(sw)==1
    if checks['sea_grid']:
        actual_sea=float(sw[0][3]);sg=[]
        for r in sea:
            i,dx=int(r[1]),int(r[2]);target=max(actual_sea,[.45,.75,1.25][i]) if dx==0 else actual_sea
            sg.append(float(r[3])<0 and r[5]=='true' and r[6]==str(dx==0).lower() and abs(float(r[4])-target)<.001)
        checks['ocean_priority']=all(sg)
    heads=[r for r in rows if r[0]=='COLUMNS'];boat=[r for r in rows if r[0]=='B']
    checks['boat_schema']=len(heads)==1 and len(boat)>60 and all(len(r)==len(heads[0]) for r in boat)
    metrics={}
    if checks['boat_schema']:
        data=[dict(zip(heads[0][1:],r[1:])) for r in boat]
        col=lambda key:np.array([float(d[key]) for d in data])
        t=col('t');x=col('x');y=col('y');z=col('z');health=col('health');dt=np.diff(t)
        speed=np.hypot(np.diff(x),np.diff(z));travel=float(np.hypot(x[-1]-x[0],z[-1]-z[0]))
        powered=sum(d['engine']=='true' and float(d['rpm'])>800 and d['gear']!=d['neutral'] and float(d['prop_omega'])>.01 and float(d['horizontal_speed'])>.5 for d in data)
        checks.update(finite=bool(np.isfinite([t,x,y,z,health]).all()),continuity=bool(np.all((dt>0)&(dt<=1))),
            no_jumps=bool(np.all(speed<=10*dt+.1)),buoyancy=bool(np.all(abs(y[t>3]-6)<.7)),
            damage_free=bool(np.all(health>=599)),controls=bool(np.all(np.diff(col('input_calls'))>0)),
            authority=all(d['authority']=='true' and d['proxy']=='false' for d in data),propulsion=powered>=40,travel=travel>85,
            stayed_on_geometry=bool(np.all((x>450)&(x<550)&(z>2950)&(z<3150))),
            crossed_joints=bool(z[0]<3005 and z[-1]>3080))
        metrics={'boat_samples':len(boat),'displacement_m':travel,'minimum_health':float(health.min()),'powered_samples':powered}
    return {'status':'PASS_TILED_CONTOUR_HOLE_AND_EMPTY_BOAT' if all(checks.values()) else 'FAIL','checks':checks,**metrics,
            'water_samples':len(water),'hole_samples':len(hole),'sha256':hashlib.sha256(raw).hexdigest(),
            'static_wrp':static,'limits':['One test site and empty boat. Native editor persistence, regional geometry and client rendering remain separate gates.']}

if __name__=='__main__':
    ev=ROOT/'evidence/regional-foundation-v1'
    ap=argparse.ArgumentParser();ap.add_argument('--static',action='store_true');ap.add_argument('--version',type=int,default=1);args=ap.parse_args()
    name=f'static-shape-v{args.version}' if args.static else 'shape-boat-v3'
    report=verify((ev/f'{name}.log').read_bytes(),args.static,args.version)
    (ev/f'{name}.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2));raise SystemExit(0 if report['status'].startswith('PASS') else 1)
