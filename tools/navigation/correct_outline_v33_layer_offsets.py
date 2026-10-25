"""Bounded V33 ALB1 offset experiment; native export remains the consumer."""
from pathlib import Path
import hashlib, json, math, struct, sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/playtest'))
from verify_texture_grid_change import read
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def derive(layer, baseline, observed):
    old={o['id']:o for o in baseline['objects']}
    new={o['id']:o for o in observed['objects']}
    assert len(old)==len(new)==10161 and old.keys()==new.keys()
    result=bytearray(layer);patches=[];touched=set()
    for ident,b in old.items():
        n=new[ident];assert b['name']==n['name']
        before=bytes.fromhex(b['matrix']);after=bytes.fromhex(n['matrix'])
        assert before[:40]==after[:40] and before[44:]==after[44:], 'Nonvertical pose change'
        y0=struct.unpack_from('<f',before,40)[0];y1=struct.unpack_from('<f',after,40)[0]
        delta=y0-y1
        assert math.isfinite(delta) and abs(delta)<=3.326
        if not delta:continue
        local=ident&0xffffff;needle=struct.pack('<I',local);pos=0;candidates=[]
        while (pos:=layer.find(needle,pos))>=0:
            if pos>=36 and pos+4<=len(layer):
                v=struct.unpack_from('<dd5fI',layer,pos-36)
                if (all(math.isfinite(x) for x in v) and 200000<=v[0]<=212288
                        and 0<=v[1]<=12288 and .5<=v[5]<=2 and abs(v[6])<200):
                    candidates.append((pos,v))
            pos+=4
        assert len(candidates)==1, ('Ambiguous layer record',ident,len(candidates))
        pos,v=candidates[0]
        native=struct.unpack('<12f',before)
        assert abs(v[0]-200000-native[9])<=16 and abs(v[1]-native[11])<=16
        assert v[7]==local
        replacement=struct.pack('<f',v[6]+delta)
        assert math.isfinite(struct.unpack('<f',replacement)[0])
        span=set(range(pos-4,pos));assert not touched&span;touched|=span
        result[pos-4:pos]=replacement
        patches.append(dict(id=ident,model=b['name'],offset=pos-4,old=v[6],
                            new=struct.unpack('<f',replacement)[0],observed_delta_y=y1-y0))
    assert len(patches)==4952
    changed={i for i,(a,b) in enumerate(zip(layer,result)) if a!=b}
    assert len(result)==len(layer) and changed<=touched
    return bytes(result),patches,len(changed)

def main():
    ev=ROOT/'evidence/foundation-followup-2026-10-01/outline-v33-native'
    layer=ROOT/'tb/regional_outline_smoothing_v33/outline_v33.Layers/default.tv4l'
    baseline=ROOT/'tb/regional_foundation_v10/02_reopened_v10.wrp'
    observed=ROOT/'tb/regional_outline_smoothing_v33/4.wrp'
    assert sha(layer)=='9092835794239f30c05c0397dc45bcd07033bb107ecd2209e7a06d7ec7b84119'
    assert sha(baseline)=='cdd6838f522a5b66b729db7c6bda39b0a5a41eb256fb26804eb39f5479ef905a'
    assert sha(observed)=='c46b8568d8a990ed5703b1a40a308c9812c25c9166fb78f1e48c49247c3e9e09'
    original=layer.read_bytes();result,patches,changed=derive(original,read(baseline),read(observed))
    backup=ev/'before-relative-offset-correction.tv4l';assert not backup.exists()
    backup.write_bytes(original);assert backup.read_bytes()==original
    assert layer.read_bytes()==original
    layer.write_bytes(result);assert layer.read_bytes()==result
    report=dict(status='LAYER_OFFSETS_CORRECTED_PENDING_NATIVE_CONSUMER',layer=str(layer),
                before_sha256=sha(backup),after_sha256=sha(layer),changed_bytes=changed,
                fields=len(patches),patches=patches,
                limits=['Local ALB1 layout inferred from these files; no general format claim.',
                        'Actual native export, save/reopen persistence and runtime required.'])
    (ev/'relative-offset-correction.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='patches'}))

if __name__=='__main__':main()
