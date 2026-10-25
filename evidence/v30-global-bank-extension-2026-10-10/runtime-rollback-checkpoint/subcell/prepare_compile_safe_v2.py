from pathlib import Path
import hashlib,json,re,subprocess,sys
P=Path(__file__).resolve().parent
old=P/'mission/BalticEV95SubcellFlagsV1.BalticTrial/init.c'
raw=old.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='0dd6ea5e4672f1330a45264841f4a9f14c7654aea660b77a54ae8fd059b3310b'
out=P/'runtime-v2'
out.mkdir(exist_ok=True)
mission=out/'BalticEV95SubcellFlagsV2.BalticTrial'
mission.mkdir(exist_ok=True)
assert not any(mission.iterdir()), 'Refuse to replace generated mission'
text=raw.decode('utf-8').replace('SubcellFlagsV1','SubcellFlagsV2').replace('SUBCELL_FLAGS_V1','SUBCELL_FLAGS_V2').replace('subcell_flags_probe_20261010.log','subcell_flags_probe_v2_20261010.log')
# Split only top-level plus signs, preserving nested arithmetic expressions.
def terms(s):
    depth=0; quoted=False; start=0; result=[]
    for i,c in enumerate(s):
        if c=='"': quoted=not quoted
        if not quoted:
            if c in '([': depth+=1
            elif c in ')]': depth-=1
            elif c=='+' and depth==0:
                result.append(s[start:i].strip());start=i+1
    result.append(s[start:].strip())
    return result
changes=[]
pattern=re.compile(r'(?m)^( +)(Emit\((.*?)\)|(?:(string) )?(row) = ((?:"[^"]*"|[^;"])*));',re.S)
def replace(m):
    indent=m[1]
    if m[3] is not None:
        ts=terms(m[3])
        if len(ts)<=5:return m[0]
        name='logRecord'+str(len(changes))
        lines=[indent+'string '+name+' = '+ts[0]+';']
        lines.extend(indent+name+' = '+name+' + '+s+';' for s in ts[1:])
        lines.append(indent+'Emit('+name+');')
    else:
        ts=terms(m[6])
        if len(ts)<=5:return m[0]
        prefix='string ' if m[4] else ''
        lines=[indent+prefix+'row = '+ts[0]+';']
        lines.extend(indent+'row = row + '+s+';' for s in ts[1:])
    changes.append({'before':m[0],'after':'\n'.join(lines)})
    return '\n'.join(lines)
text=pattern.sub(replace,text)
assert len(changes)==7,len(changes)
src=mission/'init.c'
src.write_text(text,encoding='utf-8',newline='\n')
points=P/'mission/BalticEV95SubcellFlagsV1.BalticTrial/points.csv'
(mission/'points.csv').write_bytes(points.read_bytes())
validator=Path('C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py')
r=subprocess.run([sys.executable,str(validator),str(src)],capture_output=True,text=True)
lint=json.loads(r.stdout);assert r.returncode==0 and lint['status']=='PASS' and lint['info']['files_scanned']==1
(out/'lint.json').write_text(json.dumps(lint,indent=2),encoding='utf-8')
record={'reason':'Prevent measured Formula too complex compile failure; checklist E32/E33; no changed sampling logic','source_v1_sha256':hashlib.sha256(raw).hexdigest(),'source_v2_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'points_sha256':hashlib.sha256(points.read_bytes()).hexdigest(),'changes':changes,'log_name':'baltic_ev95_subcell_flags_probe_v2_20261010.log','mission':str(mission),'runtime_executed':False}
(out/'preparation.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in record.items() if k!='changes'},indent=2))

