"""Negative controls on an actual completed local positive, without promoting bridge failures."""
from pathlib import Path
import argparse,hashlib,json
import rasterio
from verify_bridge_human_control import verify
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--reference',type=Path,required=True);ap.add_argument('--folder',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists()
    ref=json.loads(a.reference.read_text(encoding='utf-8'));terrain=Path(ref['terrain']);assert sha(terrain)==ref['terrain_sha256']
    with rasterio.open(terrain) as ds:height=ds.read(1)
    sp=a.folder/'engine.log';cp=a.folder/'client-input.log';s=sp.read_text(encoding='utf-8-sig');c=cp.read_text(encoding='utf-8-sig');base=s.splitlines()
    def accepted(r):return r['cases'][0]['status']=='PASS' and all(r['global_checks'][k] for k in ('server_header','client_header','client_end','no_parse_errors','no_actor_records'))
    original=verify(ref,s,c,height);assert base[-1].startswith('END;') and accepted(original)
    move=next(i for i,x in enumerate(base) if x.startswith('P;0;') and x.split(';')[3]=='MOVE_BEGIN')
    sample=next(i for i in range(move+1,len(base)) if base[i].startswith('P;0;') and base[i].split(';')[3]=='SAMPLE')
    end=next(i for i,x in enumerate(base) if x.startswith('P;0;') and x.split(';')[3]=='REACHED')
    def field(index,value,where=sample):
        rows=base.copy();parts=rows[where].split(';');parts[index]=str(value);rows[where]=';'.join(parts);return '\n'.join(rows)+'\n'
    def offset(v,d):
        parts=[float(x) for x in v[1:-1].split(',')];return '<'+', '.join(f'{x+y:.6f}' for x,y in zip(parts,d))+'>'
    p=base[sample].split(';')
    changes={
        'dead_human':(field(7,0),c),'unconscious':(field(17,'true'),c),'nonfinite':(field(7,'nan'),c),
        'wrong_ground':(field(12,offset(p[12],[0,1,0])),c),'floating':(field(5,offset(p[5],[0,2,0])),c),
        'teleport':(field(5,offset(p[5],[12,0,0])),c),'wrong_goal':(field(14,offset(p[14],[1,0,0])),c),
        'false_arrival':(field(5,base[move].split(';')[5],end),c),'unknown_marker':(field(3,'FORGED_PASS'),c),
        'backwards_clock':(field(2,0),c),'unexpected_actor':(field(4,'<1, 1, 1>'),c),
        'missing_movement':('\n'.join(base[:move]+base[move+1:])+'\n',c),
        'duplicate_movement':('\n'.join(base[:move]+[base[move]]+base[move:])+'\n',c),
        'missing_input':(s,'\n'.join(x for x in c.splitlines() if not(x.startswith('C;') and x.split(';')[2]=='1'))+'\n'),
        'client_missing_end':(s,'\n'.join(c.splitlines()[:-1])+'\n')}
    results=[]
    for name,(ss,cc) in changes.items():
        assert ss!=s or cc!=c;report=verify(ref,ss,cc,height);assert not accepted(report),name;json.dumps(report,allow_nan=False)
        results.append(dict(name=name,status='EXPECTED_REJECTION',source_sha256=hashlib.sha256(ss.encode()).hexdigest(),client_sha256=hashlib.sha256(cc.encode()).hexdigest()))
    out=dict(status='PASS_REAL_LOCAL_HUMAN_CONTROL_AND_15_NEGATIVES',full_run_status=original['status'],scope='Case0 only positive; not map or bridge acceptance',reference_sha256=sha(a.reference),server_sha256=sha(sp),client_sha256=sha(cp),controls=results)
    a.out.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(status=out['status'],negatives=len(results))))

if __name__=='__main__':main()
