"""Independent known-footprint and physical-consumer gates for the 6m pond trial."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np


def verify(raw, static=False):
    lines=raw.decode('utf-8-sig').splitlines()
    rows=list(csv.reader(lines,delimiter=';'))
    header='BALTIC_STATIC_WATER_V1' if static else 'BALTIC_ELEVATED_WATER_V1'
    water=[r for r in rows if r and r[0]=='WATER']
    expected={(stage,x,y,z) for stage in ('BEFORE','AFTER') for x in range(400,601,25)
              for z in range(2900,3201,25) for y in range(0,10,3)}
    keys=[(r[1],int(r[2]),int(r[3]),int(r[4])) for r in water if len(r)==10]
    checks={'header':bool(lines and lines[0]==header),
            'complete':bool(lines and lines[-1]=='END;DISTANCE_SAFETY_STOP'),
            'exact_grid':len(keys)==len(expected) and set(keys)==expected,
            'finite':all(np.isfinite([float(v) for v in r[2:6]+r[8:10]]).all() for r in water)}
    terrain=[];inside=[];outside=[]
    for r in water:
        stage,x,y,z=r[1],int(r[2]),int(r[3]),int(r[4])
        terrain.append(abs(float(r[5])-1.39)<.0001)
        wet=424<=x<=576 and 2924<=z<=3176 and (static or stage=='AFTER')
        if wet:
            inside.append(r[7]=='true' and abs(float(r[9])-6)<.001 and abs(float(r[8])+y-6)<1)
        else:
            outside.append(r[7]=='false' and float(r[9])<2)
    checks.update(terrain_unchanged=bool(terrain and all(terrain)),
                  inside_surface=bool(inside and all(inside)),outside_control=bool(outside and all(outside)))
    headers=[r for r in rows if r and r[0]=='COLUMNS']
    boat=[r for r in rows if r and r[0]=='B']
    if len(headers)!=1 or not boat or any(len(r)!=len(headers[0]) for r in boat):
        checks['boat_schema']=False
        return {'status':'FAIL','checks':checks}
    names=headers[0][1:]; data=[]
    for r in boat:
        d={}
        for key,value in zip(names,r[1:]):
            if key in {'engine','active','authority','proxy'}:
                if value not in ('true','false'):raise ValueError('Malformed boolean')
                d[key]=value=='true'
            else:d[key]=float(value)
        data.append(d)
    numeric=np.array([[v for v in d.values() if not isinstance(v,bool)] for d in data])
    t=np.array([d['t'] for d in data]);xy=np.array([[d['x'],d['z']] for d in data])
    gaps=np.diff(t);travel=np.linalg.norm(np.diff(xy,axis=0),axis=1)
    displacement=float(np.linalg.norm(xy[-1]-xy[0]))
    powered=[d['engine'] and d['rpm']>800 and d['gear']!=d['neutral'] and
             d['prop_omega']>.01 and d['horizontal_speed']>.5 for d in data]
    settled=[d for d in data if d['t']>=3]
    checks.update(boat_schema=True,finite_motion=bool(np.isfinite(numeric).all()),
        continuity=bool(len(gaps)>50 and np.all((gaps>0)&(gaps<=1))),
        no_position_jumps=bool(np.all(travel<=10*gaps+.1)),
        buoyancy=all(4<d['y']<8 for d in settled),
        no_damage=all(d['health']>=599 for d in data),
        authoritative=all(d['authority'] and not d['proxy'] for d in data),
        controls_measured=all(b['input_calls']>a['input_calls'] for a,b in zip(data,data[1:])),
        propulsion=sum(powered)>=40,
        both_tile_joints_crossed=min(d['z'] for d in data)<3005 and max(d['z'] for d in data)>3080,
        stayed_on_water=all(424<d['x']<576 and 2924<d['z']<3176 for d in data),
        useful_travel=displacement>85)
    return {'status':'PASS_ELEVATED_POND_AND_EMPTY_BOAT' if all(checks.values()) else 'FAIL',
            'checks':checks,'log_sha256':hashlib.sha256(raw).hexdigest(),'static_wrp':static,
            'water_samples':len(water),'boat_samples':len(data),'displacement_m':displacement,
            'powered_samples':sum(powered),'health_min':min(d['health'] for d in data),
            'max_gap_s':float(gaps.max()),'limits':['One flat tile array; no sloping water, crew, rendering or regional navigation acceptance.']}


def main():
    p=argparse.ArgumentParser();p.add_argument('--log',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--static',action='store_true')
    a=p.parse_args();r=verify(a.log.read_bytes(),a.static)
    a.out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(r,indent=2));raise SystemExit(0 if r['status'].startswith('PASS_') else 1)


if __name__=='__main__':main()
