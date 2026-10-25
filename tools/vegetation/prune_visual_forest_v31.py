"""Apply only the new pilot's measured forest exclusion, preserving other bytes.

Consumes a support review with no failures except pilot_bed_margin. Creates a
fresh staged candidate; density/context gates must still judge the changed XY set.
"""
import argparse,hashlib,json,shutil,struct
from pathlib import Path
import numpy as np


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def prefix(f):
    h=f.read(24);magic,tx,tz,nx,nz,cell=struct.unpack('<4s4If',h);assert magic==b'0WZD'
    f.seek(nx*nz*4+tx*tz*2,1);n=struct.unpack('<I',f.read(4))[0]
    for _ in range(n):
        while True:
            size=struct.unpack('<I',f.read(4))[0]
            if not size:break
            f.seek(size,1)
    end=f.tell();f.seek(0);return f.read(end)


def objects(f):
    while True:
        header=f.read(56);assert len(header)==56
        ident,length=struct.unpack_from('<2I',header,48)
        if not length:
            assert not f.read(1),'trailing data';return header
        raw=f.read(length);assert len(raw)==length
        yield ident,raw.decode('ascii').rstrip('\0').lower(),header+raw


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('source');ap.add_argument('output');a=ap.parse_args();S=Path(a.source);out=Path(a.output);assert not out.exists()
    review=json.loads((S/'forest-support-review-full.json').read_text());assert review['status']=='FAIL'
    assert all(v==0 for k,v in review['counts'].items() if k!='pilot_bed_margin')
    drop=set(review['violations']['pilot_bed_margin']);assert len(drop)==review['counts']['pilot_bed_margin']>0
    stage=S/'root/dayz_baltic_12km_dev/tb/narva_trial';src=stage/'baltic_trial.wrp';assert sha(src)==review['source_wrp_sha256']
    report=json.loads((S/'stage-report.json').read_text());assert report['forest'] and report['wrp_sha256']==sha(src)
    refpath=Path(report['forest_reference']['path']);assert sha(refpath)==report['forest_reference']['sha256'];models=json.loads(refpath.read_text())['models']
    target=out/'root/dayz_baltic_12km_dev/tb/narva_trial';target.parent.mkdir(parents=True)
    shutil.copytree(stage,target,ignore=shutil.ignore_patterns('baltic_trial.wrp'))
    expected=hashlib.sha256();count=0;removed=[]
    with src.open('rb') as f,(target/'baltic_trial.wrp').open('wb') as dest:
        pre=prefix(f);dest.write(pre);iterator=objects(f)
        while True:
            try:ident,name,raw=next(iterator)
            except StopIteration as stop:terminator=stop.value;dest.write(terminator);break
            if ident in drop:
                assert name in models,'refuse removal of non-forest object'
                removed.append(dict(id=ident,model=name,matrix=list(struct.unpack_from('<12f',raw))))
            else:dest.write(raw);expected.update(raw);count+=1
    assert {o['id'] for o in removed}==drop
    actual=hashlib.sha256();actual_count=0
    with (target/'baltic_trial.wrp').open('rb') as f:
        assert prefix(f)==pre;iterator=objects(f)
        while True:
            try:ident,name,raw=next(iterator)
            except StopIteration as stop:assert stop.value==terminator;break
            assert ident not in drop;actual.update(raw);actual_count+=1
    assert actual_count==count and actual.digest()==expected.digest()
    for name in ('baseline-config.bin','baseline-config.cpp','decode-config.log'):shutil.copy2(S/name,out/name)
    changed=np.load(S/'forest-height-delta.npy');keep=~np.isin(changed[:,0],list(drop));np.save(out/'forest-height-delta.npy',changed[keep])
    report.update(wrp_sha256=sha(target/'baltic_trial.wrp'),remaining_objects=report['remaining_objects']-len(drop),forest_height_adjustments=int(keep.sum()),
                  forest_excluded=len(drop),parent_visual_stage=str(S),exclusion_reason='same base_radius_plan * scale + 0.5 m clearance, against the complete saved pilot bed including caps')
    (out/'stage-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    result=dict(status='PRUNED_PENDING_CONSUMER',removed=removed,removed_count=len(drop),retained_count=count,retained_record_bytes_sha256=actual.hexdigest(),
                source_wrp_sha256=sha(src),wrp_sha256=report['wrp_sha256'],source_review_sha256=sha(S/'forest-support-review-full.json'),
                limits=['Other object records, all terrain/materials and config preserved byte for byte.','Support consumer must be rerun; XY/density/context gates and compilation remain pending.'])
    (out/'forest-exclusion.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='removed'},indent=2))


if __name__=='__main__':main()
