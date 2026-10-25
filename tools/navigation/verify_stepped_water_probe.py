"""Known tile footprint/level oracle and independent physical-consumer thresholds."""
import csv,hashlib,json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]


def verify(raw):
    rows=list(csv.reader(raw.decode('utf-8-sig').splitlines(),delimiter=';'))
    checks={'header':bool(rows and rows[0]==['BALTIC_STEPPED_WATER_V1']),
            'complete':bool(rows and rows[-1]==['END','DISTANCE_SAFETY_STOP'])}
    waters=[r for r in rows if r and r[0]=='WATER']
    expected={(stage,x,y,z) for stage in ('BEFORE','AFTER') for x in range(400,601,25)
              for y in range(0,10,3) for z in range(2900,3201,25)}
    keys=[(r[1],int(r[2]),int(r[3]),int(r[4])) for r in waters if len(r)==10]
    checks['exact_water_grid']=len(keys)==len(expected) and set(keys)==expected
    inside=[]; outside=[]; terrain=[]
    for row in waters:
        if len(row)!=10:return {'status':'FAIL','checks':dict(checks,water_schema=False)}
        stage,x,y,z=row[1],int(row[2]),int(row[3]),int(row[4])
        terrain.append(abs(float(row[5])-1.39)<.001)
        wet=stage=='AFTER' and 462<=x<=538 and 2962<=z<=3138
        if wet:
            # Grid points here are tile centres; no overlap ambiguity at them.
            target=6+.002*(z-3000)
            inside.append(row[7]=='true' and abs(float(row[9])-target)<.002 and abs(float(row[8])+y-target)<.5)
        else:
            outside.append(row[7]=='false' and float(row[9])<2)
    checks.update(terrain_unchanged=all(terrain),inside_surface=bool(inside and all(inside)),outside_control=bool(outside and all(outside)))
    headers=[r for r in rows if r and r[0]=='COLUMNS']
    boat=[r for r in rows if r and r[0]=='B']
    checks['boat_schema']=len(headers)==1 and len(boat)>60 and all(len(r)==len(headers[0]) for r in boat)
    if not checks['boat_schema']:return {'status':'FAIL','checks':checks}
    keys=headers[0][1:]
    data=[dict(zip(keys,r[1:])) for r in boat]
    num=lambda key:np.array([float(d[key]) for d in data])
    t=num('t'); x=num('x'); z=num('z'); y=num('y'); health=num('health')
    dt=np.diff(t); ds=np.hypot(np.diff(x),np.diff(z))
    target=6+.05*np.floor((z-3000+12.5)/25)
    powered=[d['engine']=='true' and float(d['rpm'])>800 and d['gear']!=d['neutral'] and
             float(d['prop_omega'])>.01 and float(d['horizontal_speed'])>.5 for d in data]
    displacement=float(np.hypot(x[-1]-x[0],z[-1]-z[0]))
    checks.update(finite=bool(np.isfinite(np.array([t,x,z,y,health])).all()),
        continuity=bool(np.all((dt>0)&(dt<=1))),no_jumps=bool(np.all(ds<=10*dt+.1)),
        buoyancy=bool(np.all(np.abs(y[t>3]-target[t>3])<.7)),no_damage=bool(np.all(health>=599)),
        authoritative=all(d['authority']=='true' and d['proxy']=='false' for d in data),
        controls_progress=bool(np.all(np.diff(num('input_calls'))>0)),
        propulsion=sum(powered)>=40,travel=displacement>85,
        four_joints_crossed=bool(z.min()<3005 and z.max()>3080),
        stayed_on_footprint=bool(np.all((x>462)&(x<538)&(z>2962)&(z<3138))))
    return {'status':'PASS_FIVE_CM_STEPS_EMPTY_BOAT' if all(checks.values()) else 'FAIL','checks':checks,
            'log_sha256':hashlib.sha256(raw).hexdigest(),'water_samples':len(waters),'boat_samples':len(boat),
            'displacement_m':displacement,'minimum_health':float(health.min()),'powered_samples':sum(powered),
            'limits':['Uphill only, empty boat, diagnostic dynamic array. No WRP, crew, rendering or regional-water acceptance.']}


if __name__=='__main__':
    folder=ROOT/'evidence/regional-foundation-v1'
    raw=(folder/'stepped-water-v1.log').read_bytes()
    result=verify(raw)
    (folder/'stepped-water-v1.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['status'].startswith('PASS_') else 1)
