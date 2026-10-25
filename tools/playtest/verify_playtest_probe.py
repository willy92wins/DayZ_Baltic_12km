"""Compare a complete real mission observation with the already measured V3 reference.
An offline fixture passing this parser is NOT evidence that a game ran.
"""
from pathlib import Path
import argparse,hashlib,json,math

def rows(text, prefix, columns, count):
    data=[[float(v) for v in line.split(';')[1:]] for line in text.splitlines() if line.startswith(prefix+';')]
    if len(data)!=count or any(len(row)!=columns or not all(map(math.isfinite,row)) for row in data):
        raise ValueError('Incomplete/nonfinite '+prefix)
    return data

def verify(log, baseline):
    lines=log.splitlines()
    if not lines or lines[0]!='BALTIC_TRIAL_OBSERVER_V1' or lines[-1]!='BALTIC_TRIAL_OBSERVER_COMPLETE':
        raise ValueError('Expected a complete mission observation, not a Buldozer trace')
    meta=dict(line.split('=',1) for line in lines if '=' in line)
    if meta.get('world','').lower()!='baltictrial': raise ValueError('Wrong world')
    shapes=[line.split('=',1)[1].replace('\\','/').lower() for line in lines if line.startswith('shape=')]
    if shapes.count('dz/structures/roads/bridges/bridge_metal_25.p3d')!=1: raise ValueError('Bridge missing/duplicated')
    if any('pond_50x50' in shape for shape in shapes): raise ValueError('Diagnostic pond unexpectedly present')
    maxima={}
    for prefix,cols,count,position_cols in [('G',3,289,2),('P',5,289,3),('E',6,34,4)]:
        actual=rows(log,prefix,cols,count); expected=rows(baseline,prefix,cols,count)
        if any(a[:position_cols]!=b[:position_cols] for a,b in zip(actual,expected)):
            raise ValueError('Sample coordinates/order changed: '+prefix)
        error=max(abs(a[i]-b[i]) for a,b in zip(actual,expected) for i in range(position_cols,cols))
        maxima[prefix]=error
        if error>.02: raise ValueError('Native surface differs by more than 2 cm: '+prefix+' '+str(error))
    return {'status':'PASS_MISSION_SURFACE_PARITY','max_error_m':maxima,'samples':612,
            'water_observation':{k:meta.get(k) for k in ['sea_level','center_is_sea','center_is_pond','center_water_depth']},
            'limits':['Requires actual fresh mission log as input; fixtures do not prove a run.',
                      'Surface parity does not prove player/vehicle traversal, render, inland water or CE.']}

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--log',type=Path,required=True)
    ap.add_argument('--baseline',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    try:
        result=verify(a.log.read_text(),a.baseline.read_text())
    except (ValueError,OSError) as exc:
        result={'status':'FAIL','reason':str(exc)}
    result['source_paths']={'log':str(a.log.resolve()),'baseline':str(a.baseline.resolve())}
    result['sha256']={k:hashlib.sha256(getattr(a,k).read_bytes()).hexdigest() for k in ['log','baseline'] if getattr(a,k).is_file()}
    a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['status']=='PASS_MISSION_SURFACE_PARITY' else 1)
