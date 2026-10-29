from pathlib import Path
import importlib.util,hashlib,io,json,struct,zipfile,zlib,time
R=Path("E:/DayZ-Baltic-Build/shape-repair-20261025")
D=R/"q03b2-local-author-20261029"
O=R/"q03b2-decoded-extent-repro-20261029"
O.mkdir(exist_ok=False)
start=time.monotonic()
spec=importlib.util.spec_from_file_location("q03b2",D/"saved_scene_archive_q03b2.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
f=json.loads((R/"q03b1-reader-inputs-20261029/oracle.json").read_text())["fixtures"][0]
h=f["header_dictionary"].encode("ascii");h+=b" "*((-(10+len(h)+1))%64)+b"\n"
npy=b"\x93NUMPY\x01\x00"+struct.pack("<H",len(h))+h+bytes.fromhex(f["payload_hex"])
rows=[]
for method in [0,8]:
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,"w",compression=method) as z:z.writestr("v.npy",npy+b"HIDDEN")
    data=bytearray(stream.getvalue());c=data.index(b"PK\x01\x02")
    for pos in [22,c+24]:struct.pack_into("<I",data,pos,len(npy))
    for pos in [14,c+16]:struct.pack_into("<I",data,pos,zlib.crc32(npy))
    p=O/f"method{method}.npz";p.write_bytes(data)
    try:
        with m.Session().open(p,{"v.npy":f["schema"]}) as result:
            verdict=result["status"]
    except Exception as exc:verdict=getattr(exc,"code",type(exc).__name__)
    rows.append({"method":method,"literal_full_decoded_bytes":len(npy)+6,"declared_bytes":len(npy),"hidden_literal_hex":b"HIDDEN".hex(),"observed":verdict,"sha256":hashlib.sha256(data).hexdigest()})
out={"hypothesis":"ZipExtFile EOF is size-truncated, not full compressed stream EOF; identity claim has hole","source_anchor":"zipfile/__init__.py:1094-1097","budget_seconds":10,"seconds":time.monotonic()-start,"rows":rows,"historical_npz_opened":0}
(O/"report.json").write_text(json.dumps(out,indent=2),encoding="utf-8");print(json.dumps(out))
