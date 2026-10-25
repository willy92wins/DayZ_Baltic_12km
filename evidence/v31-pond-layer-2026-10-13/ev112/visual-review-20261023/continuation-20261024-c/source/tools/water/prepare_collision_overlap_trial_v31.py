"""Isolate two zero-width ray misses at shared collision vertices.

Only twelve internal prism components grow by 1% around their centroids. Their
top planes remain coplanar; all other LOD bytes, model bounds, poses and terrain
are preserved. This is an experiment until the unchanged runtime gate passes.
"""
import argparse,hashlib,io,json,shutil,struct,sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,Point
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import continuous_stream_pilot_v31 as author
py3d=author.py3d

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def split(raw):
    f=io.BytesIO(raw);assert struct.unpack('<4s2I',f.read(12))==(b'MLOD',257,4)
    result=[]
    for _ in range(4):
        start=f.tell();lod=py3d.LOD(f);result.append((lod,raw[start:f.tell()]))
    assert f.tell()==len(raw);return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('pilot');ap.add_argument('out');a=ap.parse_args();P=Path(a.pilot);out=Path(a.out);assert not out.exists()
    rep=json.loads((P/'author-report.json').read_text());src=out/'source/baltic_stream_pilot';src.mkdir(parents=True)
    target={'cs_kit_118_0072.p3d':(8273.058594,9003.779297),'cs_kit_118_0288.p3d':(8226.964844,9210.511719)};changes=[]
    for inst in rep['instances']:
        name=inst['model'].rsplit('\\',1)[-1];path=P/'source/baltic_stream_pilot'/name;assert sha(path)==inst['sha256'];raw=path.read_bytes()
        if name not in target:(src/name).write_bytes(raw);continue
        parts=split(raw);old=parts[1][0];v=np.array([p.coords for p in old.points]);assert len(v)%6==0
        prism=v.reshape(-1,6,3);p=Point(np.array(target[name])-np.array(inst['origin'])[[0,2]])
        chosen=[i for i,t in enumerate(prism) if Polygon(t[:3,[0,2]]).distance(p)<.005];assert len(chosen)==6
        geo=py3d.LOD();geo.resolution=old.resolution;geo.properties.update(old.properties);vol=[];max_delta=0.
        for i,t in enumerate(prism):
            top=t[:3].copy()
            assert np.allclose(t[3:],top-[0,180/512,0],atol=0,rtol=0)
            if i in chosen:
                centre=top.mean(0);top=centre+(top-centre)*1.01;max_delta=max(max_delta,float(np.linalg.norm(top-t[:3],axis=1).max()))
                old_n=np.cross(t[1]-t[0],t[2]-t[0]);assert np.max(np.abs((top-t[0])@old_n))<1e-10
                assert Polygon(top[:,[0,2]]).contains(p),'miss point must lie inside, not on the edge'
            vol.append(author.add_prism(geo,top,i+1))
        newv=np.array([p.coords for p in geo.points]);assert np.array_equal(newv.min(0),v.min(0)) and np.array_equal(newv.max(0),v.max(0)),'bounds changed'
        buffer=io.BytesIO();geo.write(buffer);result=raw[:12]+parts[0][1]+buffer.getvalue()+parts[2][1]+parts[3][1]
        (src/name).write_bytes(result);again=split(result)
        assert all(again[i][1]==parts[i][1] for i in (0,2,3))
        changes.append(dict(model=name,components=chosen,max_vertex_delta_m=max_delta,non_geometry_lods_byte_exact=True,geometry_bounds_exact=True,
                            before_sha256=inst['sha256'],after_sha256=sha(src/name)))
        inst['sha256']=sha(src/name);inst['signed_collision_volume']=float(sum(vol))
    assert len(changes)==2
    (src/'config.cpp').write_text(author.model_config(rep['instances']),encoding='ascii')
    rep['collision_trial']=dict(parent=str(P),purpose='Shared-vertex RV precision discriminator',changes=changes)
    (out/'author-report.json').write_text(json.dumps(rep,indent=2))
    for path in P.glob('*-surfaces.npz'):shutil.copy2(path,out/path.name)
    report=dict(status='AUTHORED_EXPERIMENT_NOT_ACCEPTED',changes=changes,unchanged_models=33,terrain_changed=False,
                gate='Unchanged V3 full probe, calibrated Bullet margin plus exact RV rays; no radius relaxation',
                limits=['Only the two observed shared-vertex cases; not a general collision policy or global rollout.','Binary parity and engine probe required.'])
    (out/'collision-trial.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':main()
