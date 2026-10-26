from pathlib import Path
import numpy as np,zipfile,json,hashlib
R=Path(__file__).parent;source=R/'river-kit7-midpoint-a-20261026/terrain.npz';saved=R/'river-kit7-merged-20261026/terrain-buried.npz'
sha=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
with zipfile.ZipFile(source) as a,zipfile.ZipFile(saved) as b:
 assert a.namelist()==b.namelist()
 entries=[dict(name=n,source_compression=a.getinfo(n).compress_type,saved_compression=b.getinfo(n).compress_type,npy_byte_exact=a.read(n)==b.read(n)) for n in a.namelist()]
with np.load(source) as a,np.load(saved) as b:
 arrays={k:dict(dtype_exact=a[k].dtype==b[k].dtype,shape_exact=a[k].shape==b[k].shape,values_exact=bool(np.array_equal(a[k],b[k],equal_nan=True)) if np.issubdtype(a[k].dtype,np.number) else bool(np.array_equal(a[k],b[k]))) for k in a.files}
result=dict(status='DIAGNOSTIC',source_sha256=sha(source),saved_sha256=sha(saved),source_bytes=source.stat().st_size,saved_bytes=saved.stat().st_size,zip_entries=entries,arrays=arrays,all_npy_byte_exact=all(x['npy_byte_exact'] for x in entries),all_arrays_exact=all(all(v.values()) for v in arrays.values()))
out=R/'river-kit7-merged-20261026/container-diagnostic.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['arrays','zip_entries']},indent=2));print('COMPRESSION',sorted({(e['source_compression'],e['saved_compression']) for e in entries}))
