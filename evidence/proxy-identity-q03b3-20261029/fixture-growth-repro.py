"""One new concern from integration: file prefix hash is not a complete fixture hash.
Read-only towards real evidence; one synthetic mutation, budget10s/256MiB.
"""
from pathlib import Path
import hashlib,json,importlib.util,time
from unittest.mock import patch
R=Path("E:/DayZ-Baltic-Build/shape-repair-20261025")
O=R/"q03b3-fixture-growth-repro-20261029";O.mkdir(exist_ok=False)
s=importlib.util.spec_from_file_location("kernel",R/"q03b3-local-author-20261029/saved_scene_proxy_identity_q03b3.py")
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
data=b'{"x":1}';p=O/"fixture.json";p.write_bytes(data);real=m.os.fstat
calls=0;t=time.monotonic()
def growing(fd):
    global calls
    st=real(fd);calls+=1
    if calls==1:
        with p.open("ab") as stream:stream.write(b'{"y":2}')
    return st
try:
    with patch.object(m.os,"fstat",side_effect=growing):
        result=m.load_fixture(p,hashlib.sha256(data).hexdigest())
    status="ACCEPTED_PREFIX"
except Exception as exc:status=getattr(exc,"code",type(exc).__name__);result=None
out={"status":status,"loaded":result,"original_bytes":7,"actual_bytes":p.stat().st_size,"seconds":time.monotonic()-t,"budget_seconds":10,"real_npz_opened":0}
(O/"report.json").write_text(json.dumps(out,indent=2),encoding="utf-8");print(json.dumps(out))
