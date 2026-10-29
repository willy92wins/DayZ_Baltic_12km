import sys,io,zipfile,json,hashlib
from pathlib import Path
import numpy as np
W=Path(sys.argv[1]);sys.path.insert(0,str(W))
from tools.quality import saved_scene_io_q03b as q
from tools.quality import saved_scene_binding_q03b as p
checks=[]
dt=np.dtype([('x','<i4')]);actual=q.descr_json(dt);checks.append({'id':'structured_dtype','expected':[['x','<i4']],'actual':actual,'defect_reproduced':actual!=[['x','<i4']]})
b=io.BytesIO();np.lib.format.write_array(b,np.array([1.0],dtype='<f8'),version=(2,0),allow_pickle=False);z=io.BytesIO()
with zipfile.ZipFile(z,'w') as f:f.writestr('v.npy',b.getvalue())
try:q.load_npz(z.getvalue(),['v'],{},'literal_npy_v2');outcome='ACCEPTED'
except Exception as e:outcome=type(e).__name__+':'+str(e)
checks.append({'id':'valid_npy_2_0','expected':'ACCEPTED','actual':outcome,'defect_reproduced':outcome!='ACCEPTED'})
md=np.dtype([(a,b)for a,b in p.META_DESCR]);m=np.zeros(1,dtype=md);m['model']=0;m['source_model']=2;m['proxy']=0;m['kind']=2
sections={0:{'proxies':[{'model':'test/unrelated.p3d','matrix':[1,0,0,0,1,0,0,0,1,0,0,0]}]},2:{'proxies':[]},3:{'proxies':[]}}
routes=[{'root_model':0,'source_model':2,'slots':[[0,0]]}]
try:p.check_proxy_routes(m,routes,sections,{'test/unrelated.p3d':3});outcome='ACCEPTED'
except Exception as e:outcome=type(e).__name__+':'+str(e)
checks.append({'id':'wrong_literal_proxy_child','expected':'REJECTED','actual':outcome,'defect_reproduced':outcome=='ACCEPTED'})
result={'scope':'synthetic readonly review; no real NPZ','checks':checks,'all_defects_reproduced':all(x['defect_reproduced'] for x in checks),'source_pins':{str(x.relative_to(W)):hashlib.sha256(x.read_bytes()).hexdigest() for x in [W/'tools/quality/saved_scene_io_q03b.py',W/'tools/quality/saved_scene_binding_q03b.py']}}
Path(sys.argv[2]).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result));sys.exit(0 if result['all_defects_reproduced'] else 1)
