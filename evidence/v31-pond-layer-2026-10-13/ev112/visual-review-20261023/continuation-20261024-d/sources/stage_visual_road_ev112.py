"""Apply the reviewed H height layer to Q source, reseating forest roots only.

Read back every record. Nonforest records and forest attributes except Y remain
byte exact. Existing water footprint and guards must remain exact before stage.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys
import numpy as np
from scipy.ndimage import binary_dilation

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent/'vegetation'),str(HERE.parent/'water')]
from prune_visual_forest_v31 import prefix,objects
from streambed_kit_v31 import tri_h
import despike_v31 as guard


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('build',type=Path);ap.add_argument('out',type=Path);a=ap.parse_args()
    B,S=a.build,a.out;assert not S.exists()
    Q=B/'stage-visual-forest-20261024-b';M=B/'road-merged-20261024-h';oldM=B/'visual-merged-20261024-b'
    src=Q/'root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
    assert sha(src)=='19e1a63711080d4214b1d8aef5de874d873fe00d128076e5f2092b65595375e9'
    H0=np.load(oldM/'terrain-buried.npz')['heights'];data=np.load(M/'terrain-buried.npz');H=data['heights']
    repair=json.loads((B/'road-repair-20261024-h/review.json').read_text())
    assert repair['status']=='OFFLINE_CANDIDATE_PASS' and repair['terrain_output_sha256']==sha(B/'road-repair-20261024-h/terrain.npz')
    assert np.array_equal(H,np.load(B/'road-repair-20261024-h/terrain.npz')['heights'])
    bury=json.loads((M/'bury-report.json').read_text());assert bury['changed_vs_input']==0 and not bury['final_new_exposed']
    oldfp=np.load(oldM/'bury-work/fp0/footprint.npz');fp=np.load(M/'bury-work/fp0/footprint.npz')
    assert oldfp.files==fp.files
    assert all(np.array_equal(oldfp[k],fp[k],equal_nan=True) for k in fp.files),'changed water footprint'
    changed=H!=H0
    assert int(changed.sum())==64
    fixed=data['narva']|guard.env_vertex_plane(fp['plane'])[0]|(H0<.9)
    fixed |= guard.shoreline_vertices(H0,oldM/'bury-work/fp0/footprint.npz',np.ones_like(fixed))
    fixed |= guard.records_mask([str(B/'records-nonforest.json')])[0]
    for k in ('v31_kit','v31_bridge_cut','v31_bridge_fill','v31_dam','v31_shore_ramp','v31_causeway','v31_continuous_pilot'):
        fixed |= binary_dilation(data[k],iterations=2)
    rr,cc=np.mgrid[:2048,:2048];fixed |= np.hypot(cc*6-10397.4,12282-rr*6-9421.9)<=60
    assert not (changed&fixed).any() and np.array_equal(H<.75,H0<.75)
    sr=json.loads((Q/'stage-report.json').read_text())
    ref=Path(sr['forest_reference']['path']);assert sha(ref)==sr['forest_reference']['sha256']
    models=json.loads(ref.read_text())['models']
    target=S/'root/dayz_baltic_12km_dev/tb/narva_trial';target.parent.mkdir(parents=True)
    shutil.copytree(src.parent,target,ignore=shutil.ignore_patterns('baltic_trial.wrp'))
    for name in ('baseline-config.bin','baseline-config.cpp','decode-config.log'):shutil.copy2(Q/name,S/name)
    coords=np.argwhere(changed);lo=[coords[:,1].min()*6-6,12282-coords[:,0].max()*6-6];hi=[coords[:,1].max()*6+6,12282-coords[:,0].min()*6+6]
    shifts={};count=0
    with src.open('rb') as f,(target/'baltic_trial.wrp').open('wb') as g:
        pre=prefix(f);assert np.array_equal(np.frombuffer(pre,dtype='<f4',offset=24,count=2048**2).reshape(2048,2048),H0[::-1])
        newpre=pre[:24]+np.ascontiguousarray(H[::-1],dtype='<f4').tobytes()+pre[24+2048**2*4:]
        g.write(newpre);it=objects(f)
        while True:
            try:ident,name,raw=next(it)
            except StopIteration as stop:terminal=stop.value;g.write(terminal);break
            if name in models:
                m=np.array(struct.unpack_from('<12f',raw));bc=np.array(models[name]['bc'])
                origin=m[9:]-m[:9].reshape(3,3).T@bc
                if lo[0]<=origin[0]<=hi[0] and lo[1]<=origin[2]<=hi[1]:
                    dy=float(tri_h(H,np.array([origin[0]]),np.array([origin[2]]))[0]-tri_h(H0,np.array([origin[0]]),np.array([origin[2]]))[0])
                    yy=np.float32(m[10]+dy)
                    if yy!=m[10]:
                        shifts[ident]=dict(before=float(m[10]),after=float(yy),root_xz=origin[[0,2]].tolist())
                        raw=raw[:40]+struct.pack('<f',yy)+raw[44:]
            g.write(raw);count+=1
    changed_ids=set()
    with src.open('rb') as f,(target/'baltic_trial.wrp').open('rb') as g:
        assert prefix(f)==pre and prefix(g)==newpre
        source_iter=objects(f);output_iter=objects(g);read_count=0
        while True:
            try:old=next(source_iter)
            except StopIteration as stop:
                assert stop.value==terminal
                try:next(output_iter);raise AssertionError('extra object')
                except StopIteration as stop2:assert stop2.value==terminal
                break
            new=next(output_iter);assert old[:2]==new[:2]
            if old[2]!=new[2]:
                assert old[1] in models and old[0] in shifts
                assert old[2][:40]==new[2][:40] and old[2][44:]==new[2][44:]
                assert struct.unpack_from('<f',new[2],40)[0]==shifts[old[0]]['after']
                changed_ids.add(old[0])
            read_count+=1
    assert count==read_count==2578822 and changed_ids==set(shifts)
    sr.update(wrp_sha256=sha(target/'baltic_trial.wrp'),source_wrp_sha256=sha(src),terrain_sha256=sha(M/'terrain-buried.npz'),
              merged=str(M),parent_visual_stage=str(Q),forest_height_adjustments=len(shifts),road_layer='H')
    (S/'stage-report.json').write_text(json.dumps(sr,indent=2))
    report=dict(status='SOURCE_DELTA_VERIFIED_PENDING_SUPPORT_BUILD_RUNTIME',terrain_vertices=64,forest_y_adjustments=len(shifts),
                object_count=count,water_footprint_all_arrays_exact=True,protected_vertices_exact=True,
                nonforest_all_bytes_exact=True,forest_except_y_exact=True,source_wrp_sha256=sha(src),wrp_sha256=sr['wrp_sha256'],
                terrain_sha256=sr['terrain_sha256'],shifts=shifts)
    (S/'road-stage-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='shifts'},indent=2))


if __name__=='__main__':main()
