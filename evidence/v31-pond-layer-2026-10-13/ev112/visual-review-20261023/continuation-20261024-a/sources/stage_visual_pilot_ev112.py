"""Stage the EV112 visual probe, with exact old-kit removal and source parity.

Consumes a reviewed pilot's binary-derived poses and the final buried terrain.
Default is a non-forest technical probe. --forest keeps the AE vegetation and
adjusts its vertical origin by the measured native ground delta; this is only
reseating, not acceptance of roots, slopes or performance.
"""
import argparse,hashlib,json,re,shutil,struct,subprocess,sys
from collections import Counter
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent/'water'),str(HERE.parent/'playtest')]
from wrp0wzd import read,write,object_record
from attach_navmesh import read_pbo
from streambed_kit_v31 import tri_h


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def key(model,matrix):return model.replace('/','\\').lower().lstrip('\\'),struct.pack('<12f',*matrix)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('build');ap.add_argument('pilot');ap.add_argument('merged');ap.add_argument('out');ap.add_argument('--forest',action='store_true');a=ap.parse_args()
    B=Path(a.build);P=Path(a.pilot);M=Path(a.merged);out=Path(a.out);assert not out.exists()
    binary=json.loads((P/'binary-review.json').read_text());assert binary['status']=='BINARY_PASS'
    assert binary['pbo_sha256']==sha(P/'packed/baltic_stream_pilot.pbo')
    author=json.loads((P/'author-report.json').read_text());records=json.loads((P/'records.json').read_text())
    assert len(records)==len(author['instances'])>0
    bury=json.loads((M/'bury-report.json').read_text());assert not bury['final_new_exposed'] and bury['changed_vs_input']==0
    # Exact current water representation is a precondition for reusing its PBO.
    oldfp=np.load(B/'water-fix-b/bury-work/fp0/footprint.npz');dirs=sorted((M/'bury-work').glob('fp*'),key=lambda p:int(p.name[2:]));fp=np.load(dirs[-1]/'footprint.npz')
    for k in ('plane','field','visible'):
        assert np.array_equal(oldfp[k],fp[k],equal_nan=True), ('water footprint changed',k)
    source=B/('stage-forest-ae' if a.forest else 'stage-nonforest-c')/'root/dayz_baltic_12km_dev/tb/narva_trial'
    base=read(source/'baltic_trial.wrp');H=np.load(M/'terrain-buried.npz')['heights'];oldH=base['heights'][::-1].copy()
    oldrecords=json.loads((B/'water-fix-b/kit/kit-records.json').read_text());oldrecords=[r for r in oldrecords if r['site'] in author['removed_sites']]
    remove=Counter(key(r['model'],r['matrix']) for r in oldrecords);remaining=remove.copy();kept=[];removed=[];shifted=[]
    base_nonforest_ids=None
    if a.forest:
        nf=read(B/'stage-nonforest-c/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp');base_nonforest_ids={o['id']:o['bytes'] for o in nf['objects']}
    for obj in base['objects']:
        k=key(obj['name'],obj['matrix'])
        if remaining[k]>0:remaining[k]-=1;removed.append(obj['id']);continue
        raw=obj['bytes']
        if a.forest and obj['id'] in base_nonforest_ids:
            assert raw==base_nonforest_ids[obj['id']],('source nonforest drift',obj['id'])
        elif a.forest:
            model=obj['name'].lower().replace('/','\\');assert model.startswith(('dz\\plants\\','dz\\rocks\\')),model
            mat=obj['matrix'].copy();x,z=mat[9],mat[11]
            dy=float(tri_h(H,np.array([x]),np.array([z]))[0]-tri_h(oldH,np.array([x]),np.array([z]))[0])
            if dy:
                old_y=mat[10];mat[10]=float(np.float32(old_y+dy));raw=object_record(mat,obj['id'],obj['raw_name'])
                shifted.append((obj['id'],old_y,mat[10]))
        kept.append(raw)
    assert not sum(remaining.values()),('old kit not found',[(k[0],v) for k,v in remaining.items() if v][:5])
    assert len(removed)==len(oldrecords)>0
    nid=max(o['id'] for o in base['objects'])+1
    appended=[object_record(r['matrix'],nid+i,r['model'].encode('ascii')) for i,r in enumerate(records)]
    stage=out/'root/dayz_baltic_12km_dev/tb/narva_trial';stage.parent.mkdir(parents=True)
    shutil.copytree(source,stage,ignore=shutil.ignore_patterns('baltic_trial.wrp','config.cpp','config.bin'))
    write(stage/'baltic_trial.wrp',base['header'],H[::-1],base['materials'],kept+appended,base['terminator'])
    # Decode the DEPLOYED configuration; requiredAddons is the sole change.
    deployed=Path('P:/Mods/@DayZ_Baltic_EV112_RuntimeMarginsV2/Addons/narva_trial.pbo')
    assert sha(deployed)=='751823ac65cd56c9093de9705ee30b08a448a69606690c1363ecf944a15ac838'
    _,_,entries=read_pbo(deployed);(out/'baseline-config.bin').write_bytes(entries['config.bin'])
    converter=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/CfgConvert/CfgConvert.exe');assert converter.is_file()
    done=subprocess.run([str(converter),'-txt','-dst',str(out/'baseline-config.cpp'),str(out/'baseline-config.bin')],capture_output=True)
    (out/'decode-config.log').write_bytes(done.stdout+done.stderr);assert done.returncode==0
    text=(out/'baseline-config.cpp').read_text(encoding='utf-8-sig');assert text.count('"Baltic_Water_V30"')==1
    candidate=text.replace('"Baltic_Water_V30"','"Baltic_Water_V30", "Baltic_Stream_Pilot"');(stage/'config.cpp').write_text(candidate,encoding='utf-8')
    got=read(stage/'baltic_trial.wrp')
    checks=dict(heights=bool(np.array_equal(got['heights'],H[::-1])),objects=[o['bytes'] for o in got['objects']]==kept+appended,
                ids_unique=len({o['id'] for o in got['objects']})==len(got['objects']),materials=got['materials']==base['materials'],header=got['header']==base['header'])
    assert all(checks.values())
    if shifted:np.save(out/'forest-height-delta.npy',np.array(shifted,dtype=float))
    result=dict(status='STAGED',forest=a.forest,source_wrp_sha256=sha(source/'baltic_trial.wrp'),wrp_sha256=sha(stage/'baltic_trial.wrp'),
                pilot_pbo_sha256=binary['pbo_sha256'],terrain_sha256=sha(M/'terrain-buried.npz'),removed_old_kit_records=len(removed),
                added_models=len(appended),remaining_objects=len(kept),forest_height_adjustments=len(shifted),checks=checks,
                config_delta='requiredAddons += Baltic_Stream_Pilot',pilot=str(P),merged=str(M),
                limitations=['Source WRP parity only; binarized WRP readback and engine tests pending.','Navmesh unchanged; this is not AI navigation acceptance.','Vegetation reseating still requires forest consumer checks.'])
    (out/'stage-report.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
