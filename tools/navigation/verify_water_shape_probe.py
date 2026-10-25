"""Independent analytic L-versus-square footprint oracle; no generator imports."""
from pathlib import Path
import csv, hashlib, json

ROOT=Path(__file__).resolve().parents[2]

def verify(raw):
    rows=list(csv.reader(raw.decode('utf-8-sig').splitlines(),delimiter=';'))
    samples=[r for r in rows if r and r[0]=='S']
    expected={(i,x,z) for i in range(3) for x in range(-30,31,5) for z in range(-30,31,5)}
    actual=[tuple(map(int,r[1:4])) for r in samples if len(r)==10]
    checks={'header':rows[0]==['BALTIC_WATER_SHAPE_V1'],
            'end':rows[-1]==['END','SHAPE_SCAN_COMPLETE'],
            'grid':len(actual)==len(expected) and set(actual)==expected}
    good=[]; dry=[]
    for r in samples:
        if len(r)!=10:return {'status':'FAIL','checks':dict(checks,schema=False)}
        i,x,z=map(int,r[1:4])
        # Avoid triangle/outer edge classification tolerance in the engine.
        if abs(x)==25 or abs(z)==25 or (i<2 and (x==0 or z==0)):continue
        wet=abs(x)<25 and abs(z)<25 and (i==2 or x<0 or z<0)
        (good if wet else dry).append(r[9]==str(wet).lower() and (abs(float(r[7])-6)<.001 if wet else float(r[7])<2))
    checks.update(wet_control=bool(good and all(good)),dry_notch_and_exterior=bool(dry and all(dry)))
    return {'status':'PASS_CONCAVE_FOOTPRINT' if all(checks.values()) else 'FAIL','checks':checks,
            'samples':len(samples),'wet_controls':len(good),'dry_controls':len(dry),'sha256':hashlib.sha256(raw).hexdigest(),
            'limits':['Horizontal dynamic models only. Boat, enclosed holes, WRP and client rendering are separate gates.']}

if __name__=='__main__':
    ev=ROOT/'evidence/regional-foundation-v1'
    result=verify((ev/'water-shape-v1.log').read_bytes())
    (ev/'water-shape-v1.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['status'].startswith('PASS') else 1)
