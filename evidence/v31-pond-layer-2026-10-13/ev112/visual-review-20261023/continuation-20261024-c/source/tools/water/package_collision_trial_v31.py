"""Package exactly two corrected collision models over the verified runtime PBO.

Recompiling unchanged models can alter their binary bytes. Preserve the original
33 ODOLs and class config so the in-engine experiment isolates only two entries.
"""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'playtest'),'C:/temp/moto_lanes/review_g3/tools','C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/py3d']
from attach_navmesh import read_pbo
from odol_reader import ODOL
import py3d

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('build');a=ap.parse_args();B=Path(a.build);P=B/'visual-pilot-20261024-p';Q=B/'visual-pilot-collision-20261024-q';out=Q/'collision-package';assert not out.exists()
    base=B/'pilot-classes-20261024-a/Addons/baltic_stream_pilot.pbo';assert sha(base)=='4a194de23caa7629026dd6db93565ce37779f00b9488471bbe45a187b2b4c864'
    br=json.loads((Q/'binary-review.json').read_text());assert br['status']=='BINARY_PASS' and sha(Q/'packed/baltic_stream_pilot.pbo')==br['pbo_sha256']
    _,props,old=read_pbo(base);_,_,new=read_pbo(Q/'packed/baltic_stream_pilot.pbo');assert set(old)==set(new) and old['config.bin']==new['config.bin']
    assert json.loads((P/'records.json').read_text())==json.loads((Q/'records.json').read_text()),'compiled poses changed'
    changed=['cs_kit_118_0072.p3d','cs_kit_118_0288.p3d'];proof=[]
    for name in changed:
        od=ODOL.from_file(str(Q/'temp/baltic_stream_pilot'/name),strict=True);before=ODOL.from_file(str(P/'temp/baltic_stream_pilot'/name),strict=True)
        bc=od.model_info.bounding_center;bc=np.array([bc.x,bc.y,bc.z]);oldbc=before.model_info.bounding_center
        assert np.array_equal(bc,[oldbc.x,oldbc.y,oldbc.z])
        raw=py3d.P3D(open(Q/'source/baltic_stream_pilot'/name,'rb'));A=np.array([p.coords for p in raw.lods[1].points])
        g=min(od.lods,key=lambda l:abs(l.resolution-1e13));V=np.array([(p.x,p.y,p.z) for p in g.vertices])+bc
        error=max(float(cKDTree(A).query(V)[0].max()),float(cKDTree(V).query(A)[0].max()));assert error<1e-4
        proof.append(dict(model=name,geometry_vertex_hausdorff_m=error,bounding_center_exact=True))
    expected=dict(old)
    for name in changed:expected[name]=new[name]
    folder=out/'compiled/baltic_stream_pilot';folder.mkdir(parents=True);dest=out/'Addons';dest.mkdir()
    for name,data in expected.items():(folder/name).write_bytes(data)
    args=['C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe']
    for key,value in props.items():args+=['-property',key+'='+value]
    result=subprocess.run(args+['-dst',str(dest),str(folder)],capture_output=True);(out/'filebank.log').write_bytes(result.stdout+result.stderr);assert result.returncode==0
    packed,finalprops,final=read_pbo(dest/'baltic_stream_pilot.pbo');assert final==expected and all(finalprops.get(k)==v for k,v in props.items())
    report=dict(status='BINARY_COLLISION_DELTA_PASS',pbo_sha256=hashlib.sha256(packed).hexdigest(),baseline_sha256=sha(base),changed_entries=changed,
                other_entries_byte_exact=len(old)-2,config_byte_exact=True,all_35_poses_exact=True,geometry=proof,
                limits=['Isolated numerical collision experiment; full unchanged runtime gate required.','No visual acceptance or global rollout.'])
    (out/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':main()
