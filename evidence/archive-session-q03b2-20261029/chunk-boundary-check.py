"""Additional one-pass validation of the new raw decoder's 64KiB boundaries.
Budget30s/256MiB, no author retry or code edits; failure rejects this unit.
Oracles are literal byte patterns, not results of the candidate transform.
"""
from pathlib import Path
import os,io,json,hashlib,struct,zipfile,importlib.util
module=Path(os.environ["Q03B2_MODULE"])
assert hashlib.sha256(module.read_bytes()).hexdigest()=="79ef0195ce28648a4c32a0c36cd82d381cc366e06277fac8e0468e7d42a2c369"
s=importlib.util.spec_from_file_location("q03b2",module);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
out=Path(os.environ["Q03B2_CHUNK_ROOT"]);out.mkdir(exist_ok=False)
rows=[]
for name,pattern,copies in [("zeros",b"\x00",262144),("mixed",bytes(range(256)),768)]:
    payload=pattern*copies
    text=("{'descr': '|u1', 'fortran_order': False, 'shape': ("+str(len(payload))+",), }").encode()
    h=text+b" "*((-(10+len(text)+1))%64)+b"\n"
    raw=b"\x93NUMPY\x01\x00"+struct.pack("<H",len(h))+h+payload
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,"w",compression=zipfile.ZIP_DEFLATED) as z:z.writestr("v.npy",raw)
    path=out/(name+".npz");path.write_bytes(buf.getvalue())
    with m.Session().open(path,{"v.npy":{"dtype":"|u1","shape":[len(payload)]}}) as result:
        actual=result["arrays"]["v.npy"]
        assert hashlib.sha256(memoryview(actual)).digest()==hashlib.sha256(payload).digest()
        rows.append({"id":name,"payload_bytes":len(payload),"payload_sha256":hashlib.sha256(payload).hexdigest(),"result":"EXACT"})
print(json.dumps({"status":"SYNTHETIC_CHUNK_BOUNDARIES_VERIFIED_ONLY","cases":rows,"historical_npz_opened":0}))
