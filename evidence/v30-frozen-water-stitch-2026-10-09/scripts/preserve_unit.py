"""Preserve scripts, compact evidence and generated-source archive without junction traversal."""
from pathlib import Path
import gzip,hashlib,io,json,zipfile
import numpy as np

B=Path('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009')
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-frozen-water-stitch-2026-10-09'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def put(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():assert path.read_bytes()==raw,('Preserve existing evidence',str(path))
    else:path.write_bytes(raw)
    assert path.read_bytes()==raw

def main():
    records=[]
    for source in sorted(B.iterdir()):
        if not source.is_file() or source.suffix not in ('.py','.ps1','.json','.jsonl','.csv','.log'):continue
        raw=source.read_bytes();kind='script' if source.suffix in ('.py','.ps1') else 'evidence'
        dest=E/('scripts' if kind=='script' else '')/source.name
        compressed=len(raw)>150000 and kind=='evidence'
        data=gzip.compress(raw,mtime=0) if compressed else raw
        if compressed:dest=dest.with_suffix(dest.suffix+'.gz')
        put(dest,data)
        assert (gzip.decompress(dest.read_bytes()) if compressed else dest.read_bytes())==raw
        records.append(dict(source=str(source),evidence=dest.relative_to(E).as_posix(),source_sha256=sha(source),stored_sha256=sha(dest),compressed=compressed))
    field=B/'preserved-field.npy';compressed_field=B/'preserved-field-archive.npz'
    if not compressed_field.exists():np.savez_compressed(compressed_field,field=np.load(field))
    assert np.load(compressed_field)['field'].tobytes()==np.load(field).tobytes()
    author=json.loads((B/'authoring.json').read_text());removed=set(json.loads((B/'removal-proof.json').read_text())['removed_instance_ids'])
    repairs={r['object_id']:r for r in json.loads((B/'halo-repair.json').read_text())['repairs']}
    files=[]
    for row in author['models']:
        if row['object_id'] in removed:continue
        root=B/('compile-r2' if row['object_id'] in repairs else 'compile')/'source/baltic_water_v30'
        files.append((row['new_model'],root/row['new_model']))
    for row in json.loads((B/'seam-authoring.json').read_text())['rows']:
        files.append((row['model'],B/'compile-seams/source/baltic_water_v30'/row['model']))
    files.extend([(name,B/'compile/source/baltic_water_v30'/name) for name in ('config.cpp','$PBOPREFIX$')])
    archive=B/'authored-water-sources.zip';assert not archive.exists(),'Do not overwrite a source snapshot'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,path in sorted(files):
            info=zipfile.ZipInfo('baltic_water_v30/'+name,date_time=(2026,10,9,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,path.read_bytes())
    with zipfile.ZipFile(archive) as z:
        assert len(z.namelist())==len(files)
        assert all(z.read('baltic_water_v30/'+name)==path.read_bytes() for name,path in files)
    report=dict(status='PRESERVED_VERIFIED_CHECKPOINT',files=records,generated_sources=dict(path=str(archive),sha256=sha(archive),members=len(files),bytes=archive.stat().st_size),
                field=dict(path=str(compressed_field),sha256=sha(compressed_field),original_npy_sha256=sha(field)),
                policy='Generated full sources remain outside OneDrive/Git; exact receipts and compact evidence are versioned.')
    put(E/'preservation.json',(json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps({k:v for k,v in report.items() if k!='files'},indent=2));print('evidence files',len(records))

if __name__=='__main__':main()
